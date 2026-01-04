from rest_framework import serializers # type: ignore
from datetime import date

from services.models import ServiceRecord
from garages.models import Customer
from vehicles.models import Vehicle


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
    )

    class Meta:
        model = ServiceRecord
        fields = [
            "id",
            "vehicle_id",
            "customer_id",
            "service_type",
            "service_date",
            "service_interval_months",
            "next_service_date",
            "notes",
            "reminder_status",
            "created_at",
        ]
        read_only_fields = ["reminder_status", "created_at"]

    def validate(self, attrs):
        request = self.context.get("request")
        user = request.user if request else None

        vehicle = attrs.get("vehicle")
        customer = attrs.get("customer")

        interval = attrs.get("service_interval_months")
        next_date = attrs.get("next_service_date")

        #  Garage isolation check
        if user and hasattr(user, "garage"):
            if vehicle.garage != user.garage:
                raise serializers.ValidationError(
                    "Vehicle does not belong to your garage."
                )
            if customer.garage != user.garage:
                raise serializers.ValidationError(
                    "Customer does not belong to your garage."
                )

        #  Vehicle–Customer consistency
        if vehicle.customer and vehicle.customer != customer:
            raise serializers.ValidationError(
                "Vehicle does not belong to this customer."
            )

        # Interval vs manual date rule
        if not interval and not next_date:
            raise serializers.ValidationError(
                "Provide either service interval or next service date."
            )

        if interval and next_date:
            raise serializers.ValidationError(
                "Provide either interval OR next service date, not both."
            )

        #  Date sanity
        if next_date and next_date <= attrs.get("service_date"):
            raise serializers.ValidationError(
                "Next service date must be after service date."
            )

        return attrs
