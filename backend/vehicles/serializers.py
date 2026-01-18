from rest_framework import serializers
from .models import Vehicle, VehicleType
from garages.models import Customer
from django.utils.html import strip_tags
from django.contrib.auth import get_user_model
import re

User = get_user_model()


# vehicle serializer
class VehicleTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = VehicleType
        fields = ["id", "name"]



class VehicleSerializer(serializers.ModelSerializer):
    # Accept customer_id as input and also return it in serialized output
    customer_id = serializers.PrimaryKeyRelatedField(
        queryset=Customer.objects.all(),
        source="customer",
        required=True,
    )
    customer_name = serializers.CharField(source="customer.name", read_only=True)
    vehicle_type_name = serializers.CharField(source="vehicle_type.name", read_only=True)

    class Meta:
        model = Vehicle
        fields = [
            "id",
            "vehicle_number",
            "vehicle_type",
            "vehicle_type_name",
            "vehicle_model",
            "vehicle_description",
            "customer_id",
            "customer_name",
        ]

    def validate(self, attrs):
        customer = attrs.get("customer")
        request = self.context.get("request")

        if customer and request and hasattr(request.user, "garage"):
            if customer.garage != request.user.garage:
                raise serializers.ValidationError(
                    "Customer does not belong to your garage."
                )

        return attrs

    def validate_vehicle_number(self, value):
        # Always convert to uppercase
        value = value.upper()
        # Must be alphanumeric and contain a digit group (1-4 digits) anywhere
        if not re.match(r'^[A-Z0-9]+$', value):
            raise serializers.ValidationError(
                "Vehicle number must be uppercase alphanumeric (A-Z, 0-9) only."
            )
        digit_groups = re.findall(r'\d+', value)
        if not digit_groups or not any(1 <= len(d) <= 4 for d in digit_groups):
            raise serializers.ValidationError(
                "Vehicle number must contain at least one group of 1 to 4 digits (e.g., MH05DU6253, MH5DU6, etc.)."
            )
        if self.instance is None and Vehicle.objects.filter(vehicle_number=value).exists():
            raise serializers.ValidationError("Vehicle number must be unique.")
        if self.instance is not None and Vehicle.objects.filter(vehicle_number=value).exclude(pk=self.instance.pk).exists():
            raise serializers.ValidationError("Vehicle number must be unique.")
        return value

    def to_internal_value(self, data):
        # Ensure vehicle_number is always uppercase before validation
        if 'vehicle_number' in data and isinstance(data['vehicle_number'], str):
            data['vehicle_number'] = data['vehicle_number'].upper()
        return super().to_internal_value(data)

    def create(self, validated_data):
        validated_data['vehicle_model'] = strip_tags(validated_data.get('vehicle_model', ''))
        validated_data['vehicle_description'] = strip_tags(validated_data.get('vehicle_description', ''))
        return super().create(validated_data)

    def update(self, instance, validated_data):
        if 'vehicle_model' in validated_data:
            validated_data['vehicle_model'] = strip_tags(validated_data['vehicle_model'])
        if 'vehicle_description' in validated_data:
            validated_data['vehicle_description'] = strip_tags(validated_data['vehicle_description'])
        return super().update(instance, validated_data)
#user serializer
class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = User
        fields = ["id", "username", "password", "role"]

    def create(self, validated_data):
        validated_data['username'] = strip_tags(validated_data.get('username', ''))
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user

    def update(self, instance, validated_data):
        # handle password if provided
        password = validated_data.pop("password", None)
        if 'username' in validated_data:
            validated_data['username'] = strip_tags(validated_data['username'])
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance


