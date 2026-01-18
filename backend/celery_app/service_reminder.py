from datetime import timedelta
from celery import shared_task
from django.db import transaction
from django.utils.timezone import now
from requests import HTTPError, RequestException

from services.models import ServiceReminder

REMINDER_DAYS = [7, 3, 1]

@shared_task(
    bind=True,
    autoretry_for=(ConnectionError, TimeoutError,),
    retry_backoff=60,
    retry_kwargs={"max_retries": 3},
)
def send_service_reminder(self, reminder_id):
    """
    Send WhatsApp + Email reminder for a ServiceReminder
    """

    # Lazy imports (correct)
    from services.whatsapp_service import send_whatsapp_reminder
    from services.email_service import send_email_reminder

    print(f"[Celery] Starting reminder task: {reminder_id}")

    reminder = None

    # 🔒 Lock row to prevent duplicate sending
    with transaction.atomic():
        reminder = (
            ServiceReminder.objects
            .select_for_update()
            .get(id=reminder_id)
        )

        if reminder.status in ["SENT", "PROCESSING"]:
            print(f"[Celery] Skipped reminder {reminder_id} (status={reminder.status})")
            return

        reminder.status = "PROCESSING"
        reminder.save(update_fields=["status"])

    try:
        service = reminder.service_record
        customer = reminder.customer
        vehicle = reminder.vehicle

        garage = service.garage
        garage_phone = garage.mobile or ""
        garage_whatsapp = garage.whatsapp_number or garage_phone
        garage_address = garage.address or ""

        days_left = reminder.reminder_day
        urgency_text = (
            f"Only {days_left} days left! Your service is due on "
            f"{service.next_service_date.strftime('%d %b %Y')}."
            if days_left <= 3
            else f"Service due on {service.next_service_date.strftime('%d %b %Y')}."
        )

        # Track which channels succeeded
        sent_channels = []

        # WhatsApp
        if reminder.channel in ["WHATSAPP", "BOTH"]:
            # render a WhatsApp text template per reminder day (1,3,7)
            from django.template.loader import render_to_string
            template_name = f"reminders/whatsapp_{days_left}.txt"
            context = {
                "garage": garage,
                "customer": customer,
                "vehicle": vehicle,
                "service": service,
                "days_left": days_left,
                "urgency_text": urgency_text,
                "garage_phone": garage_phone,
                "garage_whatsapp": garage_whatsapp,
                "garage_address": garage_address,
            }
            try:
                message = render_to_string(template_name, context).strip()
            except Exception:
                # fallback to inline text if template missing or errors
                message = (
                    f"🚗 *Service Reminder - {garage.garage_name}*\n\n"
                    f"Hello {customer.name},\n"
                    f"Your *{vehicle.vehicle_model}* ({vehicle.vehicle_number}) "
                    f"is due for service.\n\n"
                    f"📅 {urgency_text}\n\n"
                    f"📍 Address: {garage_address or 'Contact us for location'}\n"
                    f"📞 Call: {garage_phone}\n"
                    f"💬 WhatsApp: {garage_whatsapp}\n"
                )

            try:
                resp = send_whatsapp_reminder(
                    phone_number=customer.mobile,
                    message=message,
                )
                reminder.provider_message_id = resp.get("message", {}).get("id")
                sent_channels.append("WHATSAPP")
            except HTTPError as he:
                status_code = getattr(he.response, "status_code", None)
                reminder.failure_reason = f"WhatsApp HTTP {status_code}: {he}"
                reminder.save(update_fields=["failure_reason"])
                # 402: payment/trial limit -> mark FAILED and do NOT retry
                if status_code == 402:
                    reminder.status = "FAILED"
                    reminder.save(update_fields=["status", "failure_reason"])
                    print(f"[Celery] WhatsApp 402 for reminder {reminder_id}; marked FAILED")
                    return
                # 5xx: server error -> treat as transient and raise ConnectionError to trigger retry
                if status_code and 500 <= status_code < 600:
                    print(f"[Celery] WhatsApp server error {status_code} for reminder {reminder_id}; will retry")
                    raise ConnectionError(str(he))
                # other 4xx: treat as permanent failure
                reminder.status = "FAILED"
                reminder.save(update_fields=["status", "failure_reason"])
                return
            except RequestException as rexc:
                # If this is a transient network error, re-raise to allow retry
                if isinstance(rexc, (ConnectionError, TimeoutError)):
                    print(f"[Celery] Network error for reminder {reminder_id}: {rexc}; will retry")
                    raise
                # Otherwise mark FAILED
                reminder.failure_reason = str(rexc)
                reminder.status = "FAILED"
                reminder.save(update_fields=["status", "failure_reason"])
                return

        # Email
        if reminder.channel in ["EMAIL", "BOTH"]:
            email = getattr(customer, "email", None)
            if email:
                from django.template.loader import render_to_string
                template_name = f"reminders/email_{days_left}.html"
                try:
                    html_message = render_to_string(template_name, context)
                except Exception:
                    html_message = (
                        f"Dear {customer.name},\n\n"
                        f"Your vehicle {vehicle.vehicle_model} ({vehicle.vehicle_number}) is due for service on "
                        f"{service.next_service_date.strftime('%d %b %Y')}.\n\n"
                        f"{urgency_text}\n\n"
                        f"Regards,\n{garage.garage_name}"
                    )
                try:
                    send_email_reminder(
                        to_email=customer.email,
                        subject=f"Service Reminder - {garage.garage_name}",
                        message=html_message,
                    )
                    sent_channels.append("EMAIL")
                except Exception as exc:
                    reminder.failure_reason = f"Email send failed: {exc}"
                    reminder.status = "FAILED"
                    reminder.save(update_fields=["status", "failure_reason"])
                    print(f"[Celery] Email send failed for reminder {reminder_id}: {exc}")
                    return
            else:
                print(f"[Celery] No email for customer {customer.id}; skipping email for reminder {reminder_id}")

        reminder.status = "SENT"
        reminder.sent_at = now()
        reminder.sent_via = ",".join(sent_channels) if sent_channels else None
        reminder.save()

        print(f"[Celery] Reminder {reminder_id} SENT via {reminder.sent_via}")

    except Exception as exc:
        # Transient network errors should be retried by Celery
        if isinstance(exc, (ConnectionError, TimeoutError)):
            print(f"[Celery] Transient error for reminder {reminder_id}: {exc}; will retry")
            raise
        reminder.status = "FAILED"
        reminder.failure_reason = str(exc)
        reminder.save(update_fields=["status", "failure_reason"])
        print(f"[Celery] Reminder {reminder_id} FAILED: {exc}")
        return

def create_service_reminders(service_record, channel="BOTH"):
    if not service_record.next_service_date:
        return

    today = now().date()
    for day in REMINDER_DAYS:
        scheduled_for = service_record.next_service_date - timedelta(days=day)
        # clamp past dates to today if you want overdue reminders to be handled now
        if scheduled_for < today:
            scheduled_for = today

        reminder, created = ServiceReminder.objects.get_or_create(
            service_record=service_record,
            reminder_day=day,
            defaults={
                "vehicle_id": service_record.vehicle_id,
                "customer_id": service_record.customer_id,
                "scheduled_for": scheduled_for,
                "channel": channel,
                "status": "PENDING",
            },
        )

        # Optional: if created and scheduled_for == today, enqueue immediately
        # from celery_app.service_reminder import send_service_reminder
        # if created and scheduled_for == today:
        #     send_service_reminder.delay(reminder.id)
