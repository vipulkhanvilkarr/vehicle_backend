from django.contrib.auth import get_user_model
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated


User = get_user_model()

class UserNameByIdView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, user_id):
        try:
            user = User.objects.get(id=user_id)
            return Response({
                "success": True,
                "user_id": user.id,
                "username": user.username
            }, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({
                "success": False,
                "error": "User not found"
            }, status=status.HTTP_404_NOT_FOUND)
import logging
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from django.contrib.auth import get_user_model
from django.db import transaction

from garages.models import Garage, GarageUser
from garages.serializers.Garages_serializers import GarageSerializer
from garages.serializers.Customer_serializer import CustomerSerializer
from accounts.permissions import SuperAdminOnly

logger = logging.getLogger(__name__)
User = get_user_model()


class CreateGarageView(APIView):
    permission_classes = [IsAuthenticated, SuperAdminOnly]

    def post(self, request):
        try:
            serializer = GarageSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            user_id = request.data.get("user_id")
            if not user_id:
                return Response(
                    {"success": False, "error": "user_id is required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            try:
                owner = User.objects.get(id=user_id, role=User.Role.ADMIN)
            except User.DoesNotExist:
                return Response(
                    {"success": False, "error": "Invalid user_id or user is not ADMIN"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Check if this admin already owns a garage
            if GarageUser.objects.filter(user=owner, is_active=True).exists():
                return Response(
                    {"success": False, "error": "This admin already owns a garage"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Create garage and GarageUser in a transaction
            with transaction.atomic():
                garage = serializer.save(user=owner)
                GarageUser.objects.create(
                    user=owner,
                    garage=garage,
                    is_active=True,
                )

            return Response(
                {
                    "success": True,
                    "message": "Garage created successfully",
                    "data": {
                        "garage_id": garage.id,
                        "garage_name": garage.garage_name,
                        "mobile": garage.mobile,
                        "address": garage.address,
                        "whatsapp_number": garage.whatsapp_number,
                        "email": garage.email,
                        "user_id": owner.id,
                        "username": owner.username,
                    }
                },
                status=status.HTTP_201_CREATED,
            )

        except Exception as exc:
            logger.exception("Garage creation failed")
            return Response(
                {"success": False, "error": "Failed to create garage", "details": str(exc)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
