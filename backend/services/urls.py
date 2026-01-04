from django.urls import path # pyright: ignore[reportMissingModuleSource]

from .views.services_views import ServiceCreateView, ServiceListView  # noqa: F401

urlpatterns = [
    # Add your service endpoints here
     path("services/create/", ServiceCreateView.as_view(), name="create-service"),
    path("services/list", ServiceListView.as_view(), name="list-services"),
]