import secrets
from datetime import timedelta

from django.db import models
from django.utils import timezone
from django.contrib.auth.models import AbstractUser
from django.conf import settings


# Custom User model

class User(AbstractUser):
    class Role(models.TextChoices):

        SUPER_ADMIN = "SUPER_ADMIN", "Super Admin"
        ADMIN = "ADMIN", "Admin"
        USER = "USER", "User"

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.USER,
    )

    def is_super_admin(self):
        return self.role == self.Role.SUPER_ADMIN

    def is_admin(self):
        return self.role == self.Role.ADMIN

    def is_user(self):
        return self.role == self.Role.USER

    def has_role(self, *roles: str) -> bool:
        """
        Convenience method:
        user.has_role(User.Role.ADMIN, User.Role.SUPER_ADMIN)
        """
        return self.role in roles

    def __str__(self):
        return self.username



# Auth Token model

class AuthToken(models.Model):
    key = models.CharField(max_length=128, unique=True, db_index=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='auth_tokens',
        on_delete=models.CASCADE,
    )
    created = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def is_expired(self):
        # Token valid for 3 days
        return timezone.now() > self.created + timedelta(days=3)

    @staticmethod
    def generate_key():
        return secrets.token_hex(64)

    @classmethod
    def create_token(cls, user):
        key = cls.generate_key()
        return cls.objects.create(user=user, key=key)

    def deactivate(self):
        self.is_active = False
        self.save()

    def __str__(self):
        return f"Token for {self.user} ({'active' if self.is_active else 'inactive'})"


 
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
 
class Vehicle(models.Model):
    vehicle_number = models.CharField(max_length=50, unique=True)
    vehicle_type = models.ForeignKey(
        VehicleType,
        on_delete=models.PROTECT,
        related_name="vehicles",
        null=True,
        blank=True,
        default=None,
    )
    vehicle_model = models.CharField(max_length=100)
    vehicle_description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.vehicle_number} - {self.vehicle_model}"
