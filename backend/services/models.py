from datetime import timedelta
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
