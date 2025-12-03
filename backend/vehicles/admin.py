# vehicles/admin.py

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from .models import User, Vehicle


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    # show in list page
    list_display = ("username", "email", "role", "is_active", "is_staff", "is_superuser")
    list_filter = ("role", "is_staff", "is_superuser", "is_active")
    search_fields = ("username", "email")
    ordering = ("username",)

    # add 'role' into the user detail page (edit form)
    fieldsets = DjangoUserAdmin.fieldsets + (
        ("Role & Access", {"fields": ("role",)}),
    )

    # add 'role' field in the "add user" form
    add_fieldsets = DjangoUserAdmin.add_fieldsets + (
        ("Role & Access", {"fields": ("role",)}),
    )


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ("vehicle_number", "vehicle_type_id", "vehicle_model", "created_at")
    search_fields = ("vehicle_number", "vehicle_model")
    list_filter = ("vehicle_type_id", "created_at")
