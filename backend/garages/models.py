from django.db import models
from django.conf import settings


class Garage(models.Model):
    """
    Represents a physical garage/workshop.
    user field stores the primary owner, GarageUser manages all memberships.
    """

    name = models.CharField(max_length=150)
    mobile = models.CharField(max_length=15)
    address = models.TextField(blank=True)
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="owned_garages",
        null=True,
        blank=True,
        help_text="Primary owner of this garage",
    )
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.mobile})"

    def get_owner(self):
        """Get the owner of this garage"""
        return self.user


class GarageUser(models.Model):
    """
    Junction table for User-Garage relationship.
    Tracks which users have access to which garages.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="garage_memberships",
    )
    garage = models.ForeignKey(
        Garage,
        on_delete=models.CASCADE,
        related_name="members",
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'garage')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.garage.name}"


class Customer(models.Model):
    """
    Represents a customer who brings vehicles to a garage.
    Identified primarily by mobile number (India-specific).
    """

    garage = models.ForeignKey(
        Garage,
        on_delete=models.CASCADE,
        related_name="customers",
    )

    name = models.CharField(max_length=100)
    mobile = models.CharField(max_length=15)
    address = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("garage", "mobile")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} - {self.mobile}"
