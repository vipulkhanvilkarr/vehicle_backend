from celery import shared_task
from django.utils.timezone import now
from services.models import ServiceReminder
from celery_app.service_reminder import send_service_reminder
import logging

logger = logging.getLogger(__name__)

@shared_task
def trigger_due_service_reminders():
    """
    Runs once per day.
    Finds all PENDING reminders due today or earlier
    and triggers send_service_reminder for each.
    """
    today = now().date()
    logger.info("Scheduler triggered: today=%s", today)
    print(f"[Scheduler] trigger_due_service_reminders running for {today}")

    reminder_ids = list(
        ServiceReminder.objects
        .filter(
            status="PENDING",
            scheduled_for=today,
        )
        .values_list("id", flat=True)
    )

    if not reminder_ids:
        logger.info("No reminders due today")
        return

    for reminder_id in reminder_ids:
        logger.info("Triggering reminder %s", reminder_id)
        send_service_reminder.delay(reminder_id)
