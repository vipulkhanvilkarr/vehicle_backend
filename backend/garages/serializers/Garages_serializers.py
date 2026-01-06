from rest_framework import serializers
from garages.models import Garage

class GarageSerializer(serializers.ModelSerializer):
    whatsapp_number = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    class Meta:
        model = Garage
        fields = ["id", "garage_name", "mobile", "address", "whatsapp_number", "email"]
