from django.contrib import admin
from .models import Garage, Customer, GarageUser


@admin.register(Garage)
class GarageAdmin(admin.ModelAdmin):
    list_display = ("garage_name", "mobile", "user", "created_at", "whatsapp_number")
    search_fields = ("garage_name", "mobile")
    list_filter = ("user",)
    


@admin.register(GarageUser)
class GarageUserAdmin(admin.ModelAdmin):
    list_display = ("user", "garage", "is_active", "created_at")
    search_fields = ("user__username", "garage__name")
    list_filter = ("is_active", "garage")


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ("name", "mobile", "garage", "created_at")
    search_fields = ("name", "mobile")
    list_filter = ("garage",)
