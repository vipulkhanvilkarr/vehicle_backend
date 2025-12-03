
import secrets
from django.utils import timezone
from django.db import models
from django.contrib.auth.models import AbstractUser

# Custom AuthToken model
class AuthToken(models.Model):
    key = models.CharField(max_length=64, unique=True, db_index=True)
    user = models.ForeignKey('User', related_name='auth_tokens', on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    @staticmethod
    def generate_key():
        return secrets.token_hex(32)

    @classmethod
    def create_token(cls, user):
        key = cls.generate_key()
        return cls.objects.create(user=user, key=key)

    def deactivate(self):
        self.is_active = False
        self.save()


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




# New VehicleType model
class VehicleType(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name

    @staticmethod
    def choices():
        return [
            "Two Wheeler",
            "Three Wheeler",
            "Four Wheeler",
        ]

    def save(self, *args, **kwargs):
        # Only allow saving if name is in choices
        if self.name not in self.choices():
            raise ValueError(f"VehicleType must be one of: {', '.join(self.choices())}")
        super().save(*args, **kwargs)


class Vehicle(models.Model):
    vehicle_number = models.CharField(max_length=50, unique=True)
    vehicle_type = models.ForeignKey(
    VehicleType,
    on_delete=models.PROTECT,
    related_name="vehicles",
    default=None,
    null=True,
    blank=True
)
    vehicle_model = models.CharField(max_length=100)
    vehicle_description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.vehicle_number} - {self.vehicle_model}"



