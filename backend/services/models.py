from datetime import timedelta, timezone
from django.db import models # type: ignore
from garages.models import Garage, Customer
from vehicles.models import Vehicle

class ServiceRecord(models.Model):

    SERVICE_TYPE_CHOICES = (
        ("PERIODIC", "Periodic Service"),
        ("REPAIR", "Repair"),
    )

    REMINDER_STATUS_CHOICES = (
        ("PENDING", "Pending"),
        ("SENT", "Sent"),
    )

    garage = models.ForeignKey(Garage, on_delete=models.CASCADE, related_name="services")
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name="services")
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="services")

    service_type = models.CharField(
        max_length=20,
        choices=SERVICE_TYPE_CHOICES,
        default="PERIODIC",
    )

    service_date = models.DateField()

    # 🔹 OPTION 1: Interval-based
    service_interval_months = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="3, 6, 12 months",
    )

    # 🔹 OPTION 2: Manual date
    next_service_date = models.DateField(
        null=True,
        blank=True,
    )

    notes = models.TextField(blank=True)

    reminder_status = models.CharField(
        max_length=10,
        choices=REMINDER_STATUS_CHOICES,
        default="PENDING",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        """
        Priority:
        1. If next_service_date is provided → use it
        2. Else if interval is provided → calculate
        """
        if not self.next_service_date and self.service_interval_months:
            self.next_service_date = (
                self.service_date + timedelta(days=30 * self.service_interval_months)
            )
        super().save(*args, **kwargs)



class ServiceReminder(models.Model):

    REMINDER_DAY_CHOICES = (
        (7, "7 Days Before"),
        (3, "3 Days Before"),
        (1, "1 Day Before"),
    )

    CHANNEL_CHOICES = (
        ("WHATSAPP", "WhatsApp"),
        ("EMAIL", "Email"),
        ("BOTH", "WhatsApp + Email"),
    )

    STATUS_CHOICES = (
        ("PENDING", "Pending"),
        ("PROCESSING", "Processing"),
        ("SENT", "Sent"),
        ("FAILED", "Failed"),
    )

    service_record = models.ForeignKey(
        "ServiceRecord",
        on_delete=models.CASCADE,
        related_name="reminders",
    )

    vehicle = models.ForeignKey(
        Vehicle,
        on_delete=models.CASCADE,
        related_name="service_reminders",
    )

    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name="service_reminders",
    )

    reminder_day = models.PositiveSmallIntegerField(
        choices=REMINDER_DAY_CHOICES,
        help_text="How many days before next service date",
    )

    scheduled_for = models.DateField(
        help_text="Date on which reminder should be sent (checked at 9 AM)",
    )

    channel = models.CharField(
        max_length=20,
        choices=CHANNEL_CHOICES,
        default="BOTH",
    )

    status = models.CharField(
        max_length=15,
        choices=STATUS_CHOICES,
        default="PENDING",
    )

    sent_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    failure_reason = models.TextField(
        null=True,
        blank=True,
    )

    provider_message_id = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="WhatsApp / Email provider reference ID",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        db_table = "service_reminders"
        unique_together = ("service_record", "reminder_day")
        indexes = [
            models.Index(fields=["scheduled_for", "status"]),
        ]

    def mark_sent(self, provider_message_id=None):
        self.status = "SENT"
        self.sent_at = timezone.now()
        self.provider_message_id = provider_message_id
        self.save(update_fields=["status", "sent_at", "provider_message_id"])

    def mark_failed(self, reason: str):
        self.status = "FAILED"
        self.failure_reason = reason
        self.save(update_fields=["status", "failure_reason"])

    def __str__(self):
        return f"ServiceReminder(service={self.service_record_id}, day={self.reminder_day})"
