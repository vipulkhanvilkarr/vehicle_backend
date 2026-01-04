import logging
from accounts.permissions import AdminAccess, SuperAdminOnly
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Vehicle, VehicleType
from .serializers import VehicleSerializer, VehicleTypeSerializer
from garages.models import GarageUser


def get_user_garage(user):
    """Helper to get user's active garage from GarageUser"""
    membership = GarageUser.objects.filter(user=user, is_active=True).first()
    return membership.garage if membership else None


class VehicleTypeListView(generics.ListAPIView):
    queryset = VehicleType.objects.all()
    serializer_class = VehicleTypeSerializer
    permission_classes = [AdminAccess]


class VehicleCreateView(generics.CreateAPIView):
    queryset = Vehicle.objects.all()
    serializer_class = VehicleSerializer
    permission_classes = [AdminAccess]

    def create(self, request, *args, **kwargs):
        try:
            user = request.user
            garage = get_user_garage(user)

            # Non-super admin must have a garage
            if not user.is_super_admin() and not garage:
                return Response(
                    {"success": False, "error": "Only garage members can create vehicles"},
                    status=status.HTTP_403_FORBIDDEN,
                )

            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            # Auto-assign garage for non-super admin
            if garage:
                vehicle = serializer.save(garage=garage)
            else:
                # Super admin - use provided garage or customer's garage
                vehicle = serializer.save()
                if vehicle.customer and not vehicle.garage:
                    vehicle.garage = vehicle.customer.garage
                    vehicle.save()

            return Response(
                {
                    "success": True,
                    "message": "Vehicle created successfully",
                    "data": VehicleSerializer(vehicle).data
                },
                status=status.HTTP_201_CREATED,
            )

        except Exception as exc:
            return Response(
                {"success": False, "error": "Failed to create vehicle", "details": str(exc)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class VehicleListView(generics.ListAPIView):
    serializer_class = VehicleSerializer
    permission_classes = [AdminAccess]

    def get_queryset(self):
        user = self.request.user

        if user.is_super_admin():
            return Vehicle.objects.all().order_by("-id")

        garage = get_user_garage(user)
        if garage:
            return Vehicle.objects.filter(garage=garage).order_by("-id")

        return Vehicle.objects.none()


class VehicleDetailView(generics.RetrieveAPIView):
    serializer_class = VehicleSerializer
    permission_classes = [AdminAccess]

    def get_queryset(self):
        user = self.request.user
        if user.is_super_admin():
            return Vehicle.objects.all()
        garage = get_user_garage(user)
        if garage:
            return Vehicle.objects.filter(garage=garage)
        return Vehicle.objects.none()

    def retrieve(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            data = self.get_serializer(instance).data
            if instance.vehicle_type:
                data["vehicle_type"] = VehicleTypeSerializer(instance.vehicle_type).data
            return Response({"success": True, "data": data}, status=status.HTTP_200_OK)
        except Exception as exc:
            return Response(
                {"success": False, "error": "Failed to fetch vehicle", "details": str(exc)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class VehicleUpdateView(generics.UpdateAPIView):
    serializer_class = VehicleSerializer
    permission_classes = [AdminAccess]

    def get_queryset(self):
        user = self.request.user
        if user.is_super_admin():
            return Vehicle.objects.all()
        garage = get_user_garage(user)
        if garage:
            return Vehicle.objects.filter(garage=garage)
        return Vehicle.objects.none()

    def update(self, request, *args, **kwargs):
        try:
            partial = kwargs.pop("partial", False)
            instance = self.get_object()
            serializer = self.get_serializer(instance, data=request.data, partial=partial)
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)
            updated_fields = list(request.data.keys())
            if updated_fields:
                field_list = ', '.join(updated_fields)
                message = f"Vehicle field(s) {field_list} updated successfully"
            else:
                message = "Vehicle updated successfully"
            return Response({"success": True, "message": message}, status=status.HTTP_200_OK)
        except Exception as exc:
            return Response(
                {"success": False, "error": "Failed to update vehicle", "details": str(exc)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class VehicleDeleteView(generics.DestroyAPIView):
    queryset = Vehicle.objects.all()
    serializer_class = VehicleSerializer
    permission_classes = [IsAuthenticated, SuperAdminOnly]

    def destroy(self, request, *args, **kwargs):
        try:
            response = super().destroy(request, *args, **kwargs)
            if response.status_code == status.HTTP_204_NO_CONTENT:
                return Response({"success": True, "message": "Vehicle deleted successfully"}, status=status.HTTP_200_OK)
            return response
        except Exception as exc:
            return Response(
                {"success": False, "error": "Failed to delete vehicle", "details": str(exc)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
