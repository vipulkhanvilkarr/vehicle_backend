# vehicles/admin.py

from django.contrib import admin
from .models import Vehicle


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ("vehicle_number", "vehicle_type_id", "vehicle_model", "created_at")
    search_fields = ("vehicle_number", "vehicle_model")
    list_filter = ("vehicle_type_id", "created_at")
