from rest_framework import serializers
from datetime import date
from dateutil.relativedelta import relativedelta

from services.models import ServiceRecord, ServiceReminder
from garages.models import Customer
from vehicles.models import Vehicle
from services.service_reminder import create_service_reminders


class ServiceReminderSerializer(serializers.ModelSerializer):
    """Serializer for reminder details (read-only)."""
    reminder_day_display = serializers.CharField(source="get_reminder_day_display", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    channel_display = serializers.CharField(source="get_channel_display", read_only=True)

    class Meta:
        model = ServiceReminder
        fields = [
            "id",
            "reminder_day",
            "reminder_day_display",
            "scheduled_for",
            "channel",
            "channel_display",
            "status",
            "status_display",
            "sent_at",
            "sent_via",
        ]


class UpcomingReminderSerializer(serializers.ModelSerializer):
    """Lightweight serializer for dashboard lists."""
    reminder_day_display = serializers.CharField(source="get_reminder_day_display", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    channel_display = serializers.CharField(source="get_channel_display", read_only=True)
    customer_name = serializers.CharField(source="customer.name", read_only=True)
    vehicle_number = serializers.CharField(source="vehicle.registration_number", read_only=True)
    service_id = serializers.IntegerField(source="service_record.id", read_only=True)

    class Meta:
        model = ServiceReminder
        fields = [
            "id",
            "service_id",
            "scheduled_for",
            "reminder_day",
            "reminder_day_display",
            "channel",
            "channel_display",
            "status",
            "status_display",
            "sent_at",
            "sent_via",
            "customer_name",
            "vehicle_number",
        ]


class ServiceRecordSerializer(serializers.ModelSerializer):
    vehicle_id = serializers.PrimaryKeyRelatedField(
        queryset=Vehicle.objects.all(),
        source="vehicle",
        write_only=True,
    )

    customer_id = serializers.PrimaryKeyRelatedField(
        queryset=Customer.objects.all(),
        source="customer",
        write_only=True,
        required=True,  # <-- enforce mandatory
    )
    customer_name = serializers.CharField(
        source="customer.name",
        read_only=True
    )

    # Vehicle details for display
    vehicle_number = serializers.CharField(source="vehicle.registration_number", read_only=True)
    vehicle_model = serializers.CharField(source="vehicle.model", read_only=True)

    # Nested reminders for detailed view
    reminders = ServiceReminderSerializer(many=True, read_only=True)

    # Summary fields for quick status check
    reminder_summary = serializers.SerializerMethodField()

    service_date = serializers.DateField(required=True)

    class Meta:
        model = ServiceRecord
        fields = [
            "id",
            "vehicle_id",
            "vehicle_number",
            "vehicle_model",
            "customer_id",
            "customer_name",
            "service_type",
            "service_date",
            "service_interval_months",
            "next_service_date",
            "notes",
            "reminder_status",
            "reminders",
            "reminder_summary",
            "created_at",
        ]
        read_only_fields = ["reminder_status", "created_at", "customer_name", "vehicle_number", "vehicle_model"]

    def get_reminder_summary(self, obj):
        """
        Returns a summary of reminder statuses for quick frontend display.
        Example: {"total": 3, "sent": 1, "pending": 2, "failed": 0}
        """
        reminders = obj.reminders.all()
        return {
            "total": reminders.count(),
            "pending": reminders.filter(status="PENDING").count(),
            "processing": reminders.filter(status="PROCESSING").count(),
            "sent": reminders.filter(status="SENT").count(),
            "failed": reminders.filter(status="FAILED").count(),
            "next_scheduled": self._get_next_scheduled(reminders),
        }

    def _get_next_scheduled(self, reminders):
        """Get the next pending reminder date."""
        next_reminder = reminders.filter(status="PENDING").order_by("scheduled_for").first()
        if next_reminder:
            return {
                "date": next_reminder.scheduled_for,
                "days_before": next_reminder.reminder_day,
            }
        return None

    def validate(self, attrs):
        request = self.context.get("request")
        user = request.user if request else None

        vehicle = attrs.get("vehicle")
        customer = attrs.get("customer")

        service_date = attrs.get("service_date")
        interval = attrs.get("service_interval_months")
        next_date = attrs.get("next_service_date")

        # --- Mandatory ---
        if not service_date:
            raise serializers.ValidationError("Service date is required.")

        # --- Interval vs manual next date ---
        if not interval and not next_date:
            raise serializers.ValidationError(
                "Provide either service interval OR next service date."
            )

        if interval and next_date:
            raise serializers.ValidationError(
                "Provide either service interval OR next service date, not both."
            )

        # --- Interval validation ---
        if interval and interval not in (3, 6, 12):
            raise serializers.ValidationError(
                "Service interval must be 3, 6, or 12 months."
            )

        # --- Date sanity ---
        if next_date and next_date <= service_date:
            raise serializers.ValidationError(
                "Next service date must be after service date."
            )

        # --- Garage isolation ---
        if user and hasattr(user, "garage"):
            if vehicle.garage != user.garage:
                raise serializers.ValidationError("Vehicle does not belong to your garage.")
            if customer.garage != user.garage:
                raise serializers.ValidationError("Customer does not belong to your garage.")

        # --- Vehicle–Customer consistency ---
        if vehicle.customer and vehicle.customer != customer:
            raise serializers.ValidationError(
                "Vehicle does not belong to this customer."
            )

        # If customer was not explicitly provided, try to infer from vehicle
        if not customer and vehicle and getattr(vehicle, "customer", None):
            attrs["customer"] = vehicle.customer
            customer = vehicle.customer

        # Enforce customer is mandatory
        if not customer:
            raise serializers.ValidationError("Customer ID is required to create a service record.")

        return attrs

    def create(self, validated_data):
        interval = validated_data.get("service_interval_months")
        service_date = validated_data.get("service_date")

        # Auto-calculate next_service_date from interval
        if interval:
            validated_data["next_service_date"] = (
                service_date + relativedelta(months=interval)
            )

        service = super().create(validated_data)

        # Create reminders (non-blocking)
        try:
            create_service_reminders(service)
        except Exception:
            pass

        return service

    def update(self, instance, validated_data):
        interval = validated_data.get("service_interval_months")
        service_date = validated_data.get("service_date", instance.service_date)

        if interval:
            validated_data["next_service_date"] = (
                service_date + relativedelta(months=interval)
            )

        service = super().update(instance, validated_data)

        try:
            create_service_reminders(service)
        except Exception:
            pass

        return service
