from django.core.management.base import BaseCommand
from celery_app.schedulers import trigger_due_service_reminders


class Command(BaseCommand):
    help = "Run the service reminders scheduler once (for testing)."

    def handle(self, *args, **options):
        self.stdout.write("[Management] Running trigger_due_service_reminders()...")
        try:
            # Call the scheduler function synchronously so you can test without celery-beat
            trigger_due_service_reminders()
            self.stdout.write(self.style.SUCCESS("Scheduler executed successfully."))
        except Exception as exc:
            self.stderr.write(self.style.ERROR(f"Scheduler execution failed: {exc}"))
            raise
