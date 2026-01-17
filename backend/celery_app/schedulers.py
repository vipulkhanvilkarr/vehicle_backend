from datetime import timedelta
from celery import shared_task
from django.utils.timezone import now
from services.models import ServiceReminder, ServiceRecord
from .service_reminder import send_service_reminder

def create_upcoming_reminders():
    """
    Scans all ServiceRecords and creates ServiceReminder entries 
    for 7 days, 3 days, and 1 day before the next_service_date.
    """
    today = now().date()
    print(f"--- [Generator] Scanning for services requiring reminders on {today} ---")

    # Define the target days intervals (7, 3, 1)
    # If service is due on Jan 20:
    # - On Jan 13 (7 days before), we create a reminder
    # - On Jan 17 (3 days before), we create a reminder
    # - On Jan 19 (1 day before), we create a reminder
    
    intervals = [7, 3, 1]

    for days_before in intervals:
        target_service_date = today + timedelta(days=days_before)
        
        # Find records due on this specific future date
        records_due = ServiceRecord.objects.filter(
            next_service_date=target_service_date,
            status="PENDING" # Only active service records
        )
        
        for record in records_due:
            # Check if we already created a reminder for this specific day/record to avoid duplicates
            exists = ServiceReminder.objects.filter(
                service_record=record,
                reminder_type=f"{days_before}_DAYS",
                scheduled_for=today
            ).exists()
            
            if not exists:
                ServiceReminder.objects.create(
                    service_record=record,
                    customer=record.customer,
                    vehicle=record.vehicle,
                    reminder_type=f"{days_before}_DAYS",
                    reminder_day=days_before,
                    scheduled_for=today,
                    channel="WHATSAPP", # Default to WhatsApp, or logic to choose
                    status="PENDING"
                )
                print(f"--- [Generator] Created {days_before}-day reminder for Service ID {record.id} ---")

@shared_task
def schedule_due_service_reminders():
    """
    1. Generate new reminders for upcoming services.
    2. Send all PENDING reminders scheduled for TODAY.
    """
    # Step 1: Create the data
    create_upcoming_reminders()

    # Step 2: Send the messages
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
