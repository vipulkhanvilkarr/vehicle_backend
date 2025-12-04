import logging
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Vehicle, VehicleType
from .serializers import VehicleSerializer, VehicleTypeSerializer
from .permissions import RoleBasedCRUD, SuperAdminOnly

logger = logging.getLogger(__name__)

class VehicleTypeListView(generics.ListAPIView):
    queryset = VehicleType.objects.all()
    serializer_class = VehicleTypeSerializer
    permission_classes = [IsAuthenticated]

class VehicleCreateView(generics.CreateAPIView):
    queryset = Vehicle.objects.all()
    serializer_class = VehicleSerializer
    permission_classes = [IsAuthenticated, RoleBasedCRUD]

    def create(self, request, *args, **kwargs):
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            return Response({"message": "Vehicle created successfully", "data": serializer.data},
                            status=status.HTTP_201_CREATED)
        except Exception as exc:
            logger.exception("Failed to create vehicle: %s", exc)
            return Response({"error": "Failed to create vehicle", "details": str(exc)},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class VehicleListView(generics.ListAPIView):
    queryset = Vehicle.objects.all().order_by("-id")
    serializer_class = VehicleSerializer
    permission_classes = [IsAuthenticated, RoleBasedCRUD]

    def list(self, request, *args, **kwargs):
        try:
            return super().list(request, *args, **kwargs)
        except Exception as exc:
            logger.exception("Failed to fetch vehicles: %s", exc)
            return Response({"error": "Failed to fetch vehicles", "details": str(exc)},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class VehicleDetailView(generics.RetrieveAPIView):
    queryset = Vehicle.objects.all()
    serializer_class = VehicleSerializer
    permission_classes = [IsAuthenticated, RoleBasedCRUD]

    def retrieve(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            data = self.get_serializer(instance).data
            vehicle_type = None
            if getattr(instance, "vehicle_type", None):
                vehicle_type = instance.vehicle_type
            else:
                vt_id = getattr(instance, "vehicle_type_id", None)
                if vt_id:
                    vehicle_type = VehicleType.objects.filter(id=vt_id).first()
            if vehicle_type:
                data["vehicle_type"] = VehicleTypeSerializer(vehicle_type).data
            return Response(data, status=status.HTTP_200_OK)
        except Exception as exc:
            logger.exception("Failed to fetch vehicle: %s", exc)
            return Response({"error": "Failed to fetch vehicle", "details": str(exc)},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class VehicleUpdateView(generics.UpdateAPIView):
    queryset = Vehicle.objects.all()
    serializer_class = VehicleSerializer
    permission_classes = [IsAuthenticated, RoleBasedCRUD]

    def update(self, request, *args, **kwargs):
        try:
            partial = kwargs.pop("partial", False)
            instance = self.get_object()
            serializer = self.get_serializer(instance, data=request.data, partial=partial)
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)
            return Response({"message": "Vehicle updated successfully", "data": serializer.data},
                            status=status.HTTP_200_OK)
        except Exception as exc:
            logger.exception("Failed to update vehicle: %s", exc)
            return Response({"error": "Failed to update vehicle", "details": str(exc)},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class VehicleDeleteView(generics.DestroyAPIView):
    queryset = Vehicle.objects.all()
    serializer_class = VehicleSerializer
    permission_classes = [IsAuthenticated, SuperAdminOnly]

    def destroy(self, request, *args, **kwargs):
        try:
            self.check_permissions(request)
            response = super().destroy(request, *args, **kwargs)
            if response.status_code == status.HTTP_204_NO_CONTENT:
                return Response({"message": "Vehicle deleted successfully"}, status=status.HTTP_200_OK)
            return response
        except Exception as exc:
            logger.exception("Failed to delete vehicle: %s", exc)
            return Response({"error": "Failed to delete vehicle", "details": str(exc)},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)
