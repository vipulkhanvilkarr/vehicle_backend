import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("backend")
app.config_from_object("django.conf:settings", namespace="CELERY")

# Discover tasks in files named 'tasks.py' or 'service_reminder.py'
# Discover tasks in files named 'tasks.py', 'service_reminder.py', or 'schedulers.py'
app.autodiscover_tasks(related_name="tasks")
app.autodiscover_tasks(related_name="service_reminder")
app.autodiscover_tasks(related_name="schedulers")

# Configure service reminder schedule via environment variables (use .env or docker-compose)
SERVICE_REMINDER_HOUR = int(os.getenv("SERVICE_REMINDER_HOUR", 12))
SERVICE_REMINDER_MINUTE = int(os.getenv("SERVICE_REMINDER_MINUTE", 30))
# Allow overriding Celery timezone (e.g. "Asia/Kolkata") - defaults to UTC
CELERY_TZ = os.getenv("CELERY_TIMEZONE", "UTC")

# Apply timezone - disable UTC to make crontab use the configured timezone
app.conf.timezone = CELERY_TZ
app.conf.enable_utc = False

# Print schedule info at startup for debugging
print(f"[Celery Config] Timezone: {CELERY_TZ}")
print(f"[Celery Config] Scheduler will run at {SERVICE_REMINDER_HOUR}:{SERVICE_REMINDER_MINUTE:02d} ({CELERY_TZ})")

# Define Periodic Tasks (Celery Beat)
app.conf.beat_schedule = {
    "send-service-reminders-daily": {
        "task": "celery_app.schedulers.trigger_due_service_reminders",
        "schedule": crontab(hour=SERVICE_REMINDER_HOUR, minute=SERVICE_REMINDER_MINUTE),
    },
}

# Expose common aliases so imports like `from config.celery_app import celery_app` work
celery_app = app
celery = app
