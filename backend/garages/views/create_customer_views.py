import logging
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from django.contrib.auth import get_user_model

from garages.models import Garage, Customer, GarageUser
from garages.serializers.Garages_serializers import GarageSerializer
from garages.serializers.Customer_serializer import CustomerSerializer
from accounts.permissions import SuperAdminOnly

logger = logging.getLogger(__name__)
User = get_user_model()


def get_user_garage(user):
    """Helper to get user's active garage from GarageUser"""
    membership = GarageUser.objects.filter(user=user, is_active=True).first()
    return membership.garage if membership else None


class CustomerCreateView(generics.CreateAPIView):
    serializer_class = CustomerSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        try:
            user = request.user
            garage = get_user_garage(user)

            if not garage:
                return Response(
                    {"success": False, "error": "Only garage members can create customers"},
                    status=status.HTTP_403_FORBIDDEN,
                )

            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            customer = serializer.save(garage=garage)

            return Response(
                {
                    "success": True,
                    "message": "Customer created successfully",
                    "data": serializer.data
                },
                status=status.HTTP_201_CREATED,
            )

        except Exception as exc:
            logger.exception("Customer creation failed")
            return Response(
                {"success": False, "error": "Failed to create customer", "details": str(exc)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class CustomerListView(generics.ListAPIView):
    serializer_class = CustomerSerializer
    permission_classes = [IsAuthenticated]

    def list(self, request, *args, **kwargs):
        try:
            user = request.user

            # Super admin can see all customers
            if user.is_super_admin():
                queryset = Customer.objects.all().order_by("-id")
            else:
                garage = get_user_garage(user)
                if not garage:
                    return Response(
                        {"success": False, "error": "Only garage members can view customers"},
                        status=status.HTTP_403_FORBIDDEN,
                    )
                queryset = Customer.objects.filter(garage=garage).order_by("-id")

            serializer = self.get_serializer(queryset, many=True)

            return Response({
                "success": True,
                "count": queryset.count(),
                "data": serializer.data
            }, status=status.HTTP_200_OK)

        except Exception as exc:
            logger.exception("Customer list fetch failed")
            return Response(
                {"success": False, "error": "Failed to fetch customers", "details": str(exc)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class CustomerDropdownView(generics.ListAPIView):
    """Lightweight endpoint for customer dropdowns - returns only id and name"""
    permission_classes = [IsAuthenticated]

    def list(self, request, *args, **kwargs):
        try:
            user = request.user

            if user.is_super_admin():
                queryset = Customer.objects.all().order_by("name")
            else:
                garage = get_user_garage(user)
                if not garage:
                    return Response(
                        {"success": False, "error": "Only garage members can view customers"},
                        status=status.HTTP_403_FORBIDDEN,
                    )
                queryset = Customer.objects.filter(garage=garage).order_by("name")

            # Return only id and name for dropdown efficiency
            data = list(queryset.values("id", "name"))

            return Response({
                "success": True,
                "count": len(data),
                "data": data
            }, status=status.HTTP_200_OK)

        except Exception as exc:
            logger.exception("Customer dropdown fetch failed")
            return Response(
                {"success": False, "error": "Failed to fetch customers", "details": str(exc)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
