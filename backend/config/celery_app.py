import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("backend")
app.config_from_object("django.conf:settings", namespace="CELERY")

# Discover tasks in files named 'tasks.py' or 'service_reminder.py'
# Discover tasks in files named 'tasks.py', 'service_reminder.py', or 'schedulers.py'
app.autodiscover_tasks(related_name="tasks")
app.autodiscover_tasks(related_name="service_reminder")
app.autodiscover_tasks(related_name="schedulers")

# Define Periodic Tasks (Celery Beat)
from celery.schedules import crontab

app.conf.beat_schedule = {
    "send-reminders-every-morning": {
        "task": "celery_app.schedulers.schedule_due_service_reminders",
        "schedule": crontab(hour=9, minute=0),  # Runs daily at 9:00 AM UTC (or configured TZ)
    },
}

# Expose common aliases so imports like `from config.celery_app import celery_app` work
celery_app = app
celery = app
