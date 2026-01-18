from celery import shared_task
from django.utils.timezone import now
from services.models import ServiceReminder
from .service_reminder import send_service_reminder

@shared_task
def schedule_due_service_reminders():
    """
    Checks the database for all ServiceReminders due TODAY (and still PENDING).
    Triggers 'send_service_reminder' specifically for each one.
    """
    today = now().date()
    print(f"--- [Scheduler] Checking for reminders due on {today} ---")
    
    # Filter for PENDING reminders scheduled for today
    reminders = ServiceReminder.objects.filter(
        status="PENDING", 
        scheduled_for=today
    )
    
    count = reminders.count()
    print(f"--- [Scheduler] Found {count} reminders due today ---")

    for r in reminders:
        print(f"--- [Scheduler] Triggering task for ID {r.id} ---")
        send_service_reminder.delay(r.id)
