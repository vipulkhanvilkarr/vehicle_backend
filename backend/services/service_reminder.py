from datetime import timedelta
from django.utils.timezone import now
from services.models import ServiceReminder

REMINDER_DAYS = [7, 3, 1]


def create_service_reminders(service_record, channel="BOTH"):
    """
    Create 7, 3, 1 day reminders for a service record.
    Past reminders are allowed (scheduler will catch up).
    """
    if not service_record.next_service_date:
        return

    for day in REMINDER_DAYS:
        scheduled_for = service_record.next_service_date - timedelta(days=day)

        ServiceReminder.objects.get_or_create(
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
