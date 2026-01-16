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

    with transaction.atomic():
        reminder = (
            ServiceReminder.objects
            .select_for_update()
            .get(id=reminder_id)
        )

        # Prevent duplicate sending
        if reminder.status in ["SENT", "PROCESSING"]:
            return

        reminder.status = "PROCESSING"
        reminder.save(update_fields=["status"])

    try:
        service = reminder.service_record
        customer = reminder.customer
        vehicle = reminder.vehicle

        # WhatsApp
        if reminder.channel in ["WHATSAPP", "BOTH"]:
            whatsapp_resp = send_whatsapp_reminder(
                phone_number=customer.phone_number,
                template_name=settings.WHATOMATE_TEMPLATE_NAME,
                variables={
                    "name": customer.name,
                    "vehicle_no": vehicle.registration_number,
                    "service_date": service.next_service_date.strftime("%d %b %Y"),
                },
            )
            reminder.provider_message_id = whatsapp_resp.get("message_id")

        # Email
        if reminder.channel in ["EMAIL", "BOTH"]:
            send_email_reminder(
                to_email=customer.email,
                subject="Vehicle Service Reminder",
                message=(
                    f"Hi {customer.name},\n\n"
                    f"Your vehicle {vehicle.registration_number} "
                    f"is due for service on {service.next_service_date}.\n\n"
                    f"Please contact the garage to book your slot."
                ),
            )

        reminder.status = "SENT"
        reminder.sent_at = now()
        reminder.save()

    except Exception as exc:
        reminder.status = "FAILED"
        reminder.failure_reason = str(exc)
        reminder.save(update_fields=["status", "failure_reason"])
        raise
