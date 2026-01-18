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

        serializer.is_valid(raise_exception=True)

        # Assign garage
        if user.is_super_admin():
            garage_id = request.data.get("garage_id")
            if not garage_id:
                return Response(
                    {"success": False, "error": "Garage is required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            garage = Garage.objects.get(pk=garage_id)

        service = serializer.save(garage=garage)

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


class ServiceListView(generics.ListAPIView):
    """List all service records for the user's garage (or all for super admin)."""
    serializer_class = ServiceRecordSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        base_qs = ServiceRecord.objects.select_related(
            "vehicle", "customer", "garage"
        ).prefetch_related("reminders").order_by("-service_date")
        
        if user.is_super_admin():
            return base_qs
        garage = get_user_garage(user)
        if garage:
            return base_qs.filter(garage=garage)
        return ServiceRecord.objects.none()

    def list(self, request, *args, **kwargs):
        try:
            user = request.user

            # Check access for non-super-admin users
            if not user.is_super_admin():
                garage = get_user_garage(user)
                if not garage:
                    return Response(
                        {"success": False, "error": "Access denied. You are not associated with any garage."},
                        status=status.HTTP_403_FORBIDDEN,
                    )

            queryset = self.get_queryset()
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


from rest_framework.views import APIView


class SchedulerTriggerView(APIView):
    """Small admin-only endpoint to enqueue the daily reminder scheduler for testing."""
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        user = request.user
        # allow super admin or staff users only
        if not ((hasattr(user, "is_super_admin") and user.is_super_admin()) or user.is_staff):
            return Response({"success": False, "error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)

        try:
            from celery_app.schedulers import trigger_due_service_reminders
            # Enqueue the scheduler as a Celery task
            trigger_due_service_reminders.delay()
            return Response({"success": True, "message": "Scheduler enqueued"}, status=status.HTTP_200_OK)
        except Exception as exc:
            return Response({"success": False, "error": "Failed to enqueue scheduler", "details": str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
