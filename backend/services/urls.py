from django.urls import path # pyright: ignore[reportMissingModuleSource]

from .views.services_views import ServiceCreateView, ServiceListView, SchedulerTriggerView  # noqa: F401
from .views.reminders import RemindersSummaryView, UpcomingRemindersView

urlpatterns = [
    # Add your service endpoints here
    path("services/create/", ServiceCreateView.as_view(), name="create-service"),
    path("services/list", ServiceListView.as_view(), name="list-services"),
    # Admin/test endpoint to enqueue the reminder scheduler
    path("services/trigger-reminders/", SchedulerTriggerView.as_view(), name="trigger-reminders"),

    # Dashboard endpoints (garage-scoped, read-only)
    path("reminders/summary/", RemindersSummaryView.as_view(), name="reminders-summary"),
    path("reminders/upcoming/", UpcomingRemindersView.as_view(), name="reminders-upcoming"),
]