from rest_framework import serializers
from .models import Vehicle, User, VehicleType


# vehicle serializer
class VehicleTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = VehicleType
        fields = ["id", "name"]


class VehicleSerializer(serializers.ModelSerializer):

    vehicle_type = serializers.PrimaryKeyRelatedField(queryset=VehicleType.objects.all(), required=True)
    vehicle_number = serializers.CharField(required=True)
    vehicle_model = serializers.CharField(required=True)
    vehicle_type_name = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Vehicle
        fields = [
            "id",
            "vehicle_number",
            "vehicle_type",
            "vehicle_type_name",
            "vehicle_model",
            "vehicle_description",
        ]

    def get_vehicle_type_name(self, obj):
        return obj.vehicle_type.name if obj.vehicle_type else None

    def validate_vehicle_number(self, value):
        # Always convert to uppercase
        value = value.upper()
        import re
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
#user serializer
class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = User
        fields = ["id", "username", "password", "role"]

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user

    def update(self, instance, validated_data):
        # handle password if provided
        password = validated_data.pop("password", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if password:
            instance.set_password(password)

        instance.save()
        return instance


