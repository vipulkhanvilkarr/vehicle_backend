import logging
from datetime import date, timedelta

from django.db.models import Count, Q
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from services.serializer import UpcomingReminderSerializer
from services.models import ServiceReminder
from garages.models import GarageUser
from services.permissions import IsGarageMember

logger = logging.getLogger(__name__)


def get_user_garage(user):
    membership = GarageUser.objects.filter(user=user, is_active=True).first()
    return membership.garage if membership else None


class RemindersSummaryView(APIView):
    permission_classes = [IsAuthenticated, IsGarageMember]

    def get(self, request, *args, **kwargs):
        user = request.user
        garage = get_user_garage(user)
        if not garage:
            return Response({"success": False, "error": "Access denied. You are not associated with any garage."}, status=status.HTTP_403_FORBIDDEN)

        # Optional date filters
        start_date = request.query_params.get("start_date")
        end_date = request.query_params.get("end_date")

        qs = ServiceReminder.objects.filter(service_record__garage=garage)
        if start_date:
            qs = qs.filter(scheduled_for__gte=start_date)
        if end_date:
            qs = qs.filter(scheduled_for__lte=end_date)

        totals = qs.aggregate(
            total=Count("id"),
            pending=Count("id", filter=Q(status="PENDING")),
            processing=Count("id", filter=Q(status="PROCESSING")),
            sent=Count("id", filter=Q(status="SENT")),
            failed=Count("id", filter=Q(status="FAILED")),
        )

        by_channel = qs.values("channel").annotate(count=Count("id"))
        by_day = qs.values("reminder_day").annotate(count=Count("id"))

        return Response({
            "success": True,
            "totals": totals,
            "by_channel": list(by_channel),
            "by_reminder_day": list(by_day),
        })


class UpcomingRemindersView(generics.ListAPIView):
    permission_classes = [IsAuthenticated, IsGarageMember]
    serializer_class = UpcomingReminderSerializer

    def get_queryset(self):
        user = self.request.user
        garage = get_user_garage(user)
        if not garage:
            return ServiceReminder.objects.none()

        days = int(self.request.query_params.get("days", 7))
        today = date.today()
        end_date = today + timedelta(days=days)

        qs = ServiceReminder.objects.select_related(
            "service_record", "vehicle", "customer"
        ).filter(
            service_record__garage=garage,
            scheduled_for__gte=today,
            scheduled_for__lte=end_date,
        ).order_by("scheduled_for")

        return qs