from rest_framework import serializers
from garages.models import Garage

class GarageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Garage
        fields = ["id", "name", "mobile", "address"]
