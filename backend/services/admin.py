from django.contrib import admin

from .models import ServiceReminder


@admin.register(ServiceReminder)
class ServiceReminderAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "service_record",
        "vehicle",
        "customer",
        "reminder_day",
        "scheduled_for",
        "channel",
        "status",
        "sent_at",
        "created_at",
    )
    list_filter = ("channel", "status", "reminder_day")
    search_fields = ("provider_message_id", "failure_reason")

