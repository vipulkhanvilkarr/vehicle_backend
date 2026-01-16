import logging
from rest_framework import generics, status # type: ignore
from rest_framework.permissions import IsAuthenticated # type: ignore
from rest_framework.response import Response # type: ignore
from ..serializer import ServiceRecordSerializer
from services.models import ServiceRecord
from garages.models import GarageUser, Garage, Garage

logger = logging.getLogger(__name__)



def get_user_garage(user):
    """Helper to get user's active garage from GarageUser"""
    membership = GarageUser.objects.filter(user=user, is_active=True).first()
    return membership.garage if membership else None


class ServiceCreateView(generics.CreateAPIView):
    serializer_class = ServiceRecordSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        try:
            user = request.user
            garage = get_user_garage(user)

            if not user.is_super_admin() and not garage:
                return Response(
                    {"success": False, "error": "Only garage members can create service records"},
                    status=status.HTTP_403_FORBIDDEN,
                )

            serializer = self.get_serializer(
                data=request.data,
                context={"request": request},
            )
            
            if not serializer.is_valid():
                return Response({
                    "success": False,
                    "error": "Validation failed",
                    "details": serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)

            # Auto-assign garage for non-super admin
            if garage:
                service = serializer.save(garage=garage)
            else:
                # Super-admins may create records for any garage by passing `garage_id` or `garage` in payload
                if user.is_super_admin():
                    garage_id = request.data.get("garage_id") or request.data.get("garage")
                    if not garage_id:
                        return Response(
                            {"success": False, "error": "Garage is required when creating service records as super admin"},
                            status=status.HTTP_400_BAD_REQUEST,
                        )
                    try:
                        garage_obj = Garage.objects.get(pk=garage_id)
                    except Garage.DoesNotExist:
                        return Response(
                            {"success": False, "error": "Garage not found"},
                            status=status.HTTP_400_BAD_REQUEST,
                        )
                    service = serializer.save(garage=garage_obj)
                else:
                    return Response(
                        {"success": False, "error": "Only garage members can create service records"},
                        status=status.HTTP_403_FORBIDDEN,
                    )

            return Response(
                {
                    "success": True,
                    "message": "Service record created successfully",
                    "data": {
                        "service_id": service.id,
                        "next_service_date": service.next_service_date,
                    }
                },
                status=status.HTTP_201_CREATED,
            )

        except Exception as exc:
            logger.exception("Service creation failed")
            return Response(
                {"success": False, "error": "Failed to create service record", "details": str(exc)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ServiceListView(generics.ListAPIView):
    serializer_class = ServiceRecordSerializer
    permission_classes = [IsAuthenticated]

    def list(self, request, *args, **kwargs):
        try:
            user = request.user

            if user.is_super_admin():
                queryset = ServiceRecord.objects.all().order_by("-service_date")
            else:
                garage = get_user_garage(user)
                if not garage:
                    return Response(
                        {"success": False, "error": "Access denied"},
                        status=status.HTTP_403_FORBIDDEN,
                    )
                queryset = ServiceRecord.objects.filter(garage=garage).order_by("-service_date")

            serializer = self.get_serializer(queryset, many=True)
            return Response({
                "success": True,
                "count": queryset.count(),
                "data": serializer.data
            }, status=status.HTTP_200_OK)

        except Exception as exc:
            logger.exception("Service list fetch failed")
            return Response(
                {"success": False, "error": "Failed to fetch service records", "details": str(exc)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
