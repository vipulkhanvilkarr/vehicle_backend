import secrets
from datetime import timedelta

from django.db import models
from django.utils import timezone
from django.conf import settings


 
# Vehicle Type model
 
class VehicleType(models.Model):
    name = models.CharField(max_length=50, unique=True)

    VEHICLE_CHOICES = [
        "Two Wheeler",
        "Three Wheeler",
        "Four Wheeler",
    ]

    def __str__(self):
        return self.name

    @staticmethod
    def choices():
        return VehicleType.VEHICLE_CHOICES

    def save(self, *args, **kwargs):
        # Only allow saving if name is in allowed choices
        if self.name not in self.choices():
            raise ValueError(
                f"VehicleType must be one of: {', '.join(self.choices())}"
            )
        super().save(*args, **kwargs)


 
# Vehicle model
 
from garages.models import Customer, Garage

class Vehicle(models.Model):
    vehicle_number = models.CharField(max_length=50, unique=True)

    vehicle_type = models.ForeignKey(
        VehicleType,
        on_delete=models.PROTECT,
        related_name="vehicles",
        null=True,
        blank=True,
    )

    vehicle_model = models.CharField(max_length=100)
    vehicle_description = models.TextField(blank=True)

    # NEW FIELDS (IMPORTANT)
    customer = models.ForeignKey(
        Customer,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="vehicles",
    )

    garage = models.ForeignKey(
        Garage,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="vehicles",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.vehicle_number} - {self.vehicle_model}"

