from celery import Celery
from celery.schedules import crontab
from django.conf import settings
import os

# Ensure Django settings module is set
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("backend")
# Load config from Django settings (namespace CELERY_*)
app.config_from_object("django.conf:settings", namespace="CELERY")
# Autodiscover tasks in common module names
app.autodiscover_tasks(related_name="tasks")
app.autodiscover_tasks(related_name="service_reminder")
app.autodiscover_tasks(related_name="schedulers")

# Schedule configuration driven by environment variables
SERVICE_REMINDER_HOUR = int(os.getenv("SERVICE_REMINDER_HOUR", 12))
SERVICE_REMINDER_MINUTE = int(os.getenv("SERVICE_REMINDER_MINUTE", 49))
CELERY_TZ = os.getenv("CELERY_TIMEZONE", "UTC")
app.conf.timezone = CELERY_TZ

app.conf.beat_schedule = {
    "send-service-reminders-daily": {
        # correct task path to the scheduler function
        "task": "celery_app.schedulers.trigger_due_service_reminders",
        "schedule": crontab(hour=SERVICE_REMINDER_HOUR, minute=SERVICE_REMINDER_MINUTE),
    },
}
