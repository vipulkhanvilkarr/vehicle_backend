from rest_framework import serializers
from django.utils.html import strip_tags
from .models import User


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ["id", "username", "password", "role"]

    def create(self, validated_data):
        username = strip_tags(validated_data["username"])
        password = validated_data.pop("password")

        user = User(
            username=username,
            role=validated_data.get("role", User.Role.USER),
        )
        user.set_password(password)
        user.save()
        return user
