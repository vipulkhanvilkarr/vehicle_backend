from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("vehicles.urls")),
    path("api/", include("garages.urls")),
    path("api/", include("services.urls")),
    path("api/auth/", include("accounts.urls")),
]