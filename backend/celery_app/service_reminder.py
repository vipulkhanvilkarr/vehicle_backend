from celery import shared_task
from django.db import transaction
from django.utils.timezone import now
from django.conf import settings
    # Local imports to avoid importing Django models at module import time (apps may not be loaded yet)
from services.models import ServiceReminder
from services.whatsapp_service import send_whatsapp_reminder
from services.email_service import send_email_reminder
# Delay importing models and helper services until the task runs to avoid AppRegistryNotReady


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=60,
    retry_kwargs={"max_retries": 3},
)
def send_service_reminder(self, reminder_id):
    """
    Send WhatsApp + Email reminder for a ServiceReminder
    """

    # Local imports to avoid importing Django models at module import time (apps may not be loaded yet)
    from services.models import ServiceReminder
    from services.whatsapp_service import send_whatsapp_reminder
    from services.email_service import send_email_reminder

    print(f"--- [Celery] Starting Task for Reminder ID: {reminder_id} ---")
    reminder = None
    with transaction.atomic():
        reminder = (
            ServiceReminder.objects
            .select_for_update()
            .get(id=reminder_id)
        )

        # Prevent duplicate sending
        if reminder.status in ["SENT", "PROCESSING"]:
            print(f"--- [Celery] Skipping ID {reminder_id}: Status is {reminder.status} ---")
            return

        reminder.status = "PROCESSING"
        reminder.save(update_fields=["status"])
        print(f"--- [Celery] ID {reminder_id} marked as PROCESSING ---")

    try:
        service = reminder.service_record
        customer = reminder.customer
        vehicle = reminder.vehicle

        # Get garage contact info (default to empty string if missing)
        garage_phone = service.garage.mobile if service.garage.mobile else ""
        garage_whatsapp = service.garage.whatsapp_number if service.garage.whatsapp_number else garage_phone
        
        # Determine urgency based on reminder_day
        days_left = reminder.reminder_day
        if days_left <= 3:
            urgency_text = f"Only {days_left} days left! Your service is due on {service.next_service_date.strftime('%d %b %Y')}."
        else:
            urgency_text = f"Book your slot soon. Due date: {service.next_service_date.strftime('%d %b %Y')}."

        # WhatsApp
        if reminder.channel in ["WHATSAPP", "BOTH"]:
            print(f"--- [Celery] Sending WhatsApp to Customer: {customer.name} ({customer.mobile}) ---")
            
            # Industry Standard Professional Message
            message = (
                f"🚗 *Service Reminder - {service.garage.garage_name}*\n\n"
                f"Hello {customer.name},\n"
                f"This is a gentle reminder that your *{vehicle.vehicle_model}* ({vehicle.vehicle_number}) is due for service on *{service.next_service_date.strftime('%d %b %Y')}*.\n\n"
                f"📅 *{urgency_text}*\n\n"
                f"To ensure smooth performance and longevity of your vehicle, we recommend booking your service in advance.\n\n"
                f"📞 *Call us:* {garage_phone}\n"
                f"💬 *WhatsApp:* {garage_whatsapp}\n\n"
                f"📍 {service.garage.address if service.garage.address else ''}\n"
                f"We look forward to serving you!\n"
            )

            whatsapp_resp = send_whatsapp_reminder(
                phone_number=customer.mobile,
                message=message,
            )

            reminder.provider_message_id = whatsapp_resp.get("message", {}).get("id")
            print(f"--- [Celery] WhatsApp Sent Successfully. Provider ID: {reminder.provider_message_id} ---")

        # Email
        if reminder.channel in ["EMAIL", "BOTH"] and hasattr(customer, "email") and customer.email:
            print(f"--- [Celery] Sending Email to: {customer.email} ---")
            send_email_reminder(
                to_email=customer.email,
                subject=f"Service Due for {vehicle.vehicle_model} - {service.garage.garage_name}",
                message=(
                    f"Dear {customer.name},\n\n"
                    f"We hope you are having a great day.\n\n"
                    f"This is a reminder from {service.garage.garage_name} that your vehicle is due for service.\n\n"
                    f"Vehicle Details:\n"
                    f"----------------\n"
                    f"Model: {vehicle.vehicle_model}\n"
                    f"Number: {vehicle.vehicle_number}\n"
                    f"Due Date: {service.next_service_date.strftime('%d %b %Y')}\n"
                    f"Urgency: {urgency_text}\n\n"
                    f"Regular maintenance helps keep your vehicle running smoothly and avoids costly repairs.\n\n"
                    f"Contact us to book an appointment:\n"
                    f"Phone: {garage_phone}\n"
                    f"Address: {service.garage.address if service.garage.address else 'N/A'}\n\n"
                    f"Best Regards,\n"
                    f"{service.garage.garage_name}"
                ),
            )
            print(f"--- [Celery] Email Sent Successfully ---")

        reminder.status = "SENT"
        reminder.sent_at = now()
        reminder.save()
        print(f"--- [Celery] ID {reminder_id} marked as SENT ---")

    except Exception as exc:
        print(f"--- [Celery] Error Processing ID {reminder_id}: {str(exc)} ---")
        # Only update the reminder if it was successfully fetched above
        if reminder is not None:
            reminder.status = "FAILED"
            reminder.failure_reason = str(exc)
            reminder.save(update_fields=["status", "failure_reason"])
            print(f"--- [Celery] ID {reminder_id} marked as FAILED ---")
        raise
