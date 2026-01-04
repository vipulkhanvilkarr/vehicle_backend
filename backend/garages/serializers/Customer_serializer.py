from rest_framework import serializers
from garages.models import Garage, Customer

class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ["id", "name", "mobile", "address"]
