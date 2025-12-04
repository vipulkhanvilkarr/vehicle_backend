from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework.authtoken.views import obtain_auth_token  
from .user_views import DeleteUserView, UpdateUserView, UserCreateView, CurrentUserView, LoginView, LogoutView, UserListView
from .vehicle_views import VehicleCreateView, VehicleDeleteView, VehicleListView, VehicleUpdateView, VehicleTypeListView, VehicleDetailView

router = DefaultRouter()

urlpatterns = [

    path("auth/login/", LoginView.as_view(), name="api_login"),
    path("auth/logout/", LogoutView.as_view(), name="api_logout"),

    # API for Super Admin to create users and view current user details
    path("current-user-details/", CurrentUserView.as_view(), name="current_user"),
    path("users/", UserListView.as_view(), name="user_list"),
    path("users/create/", UserCreateView.as_view(), name="user_create"),
    path("users/update/<int:pk>", UpdateUserView.as_view(), name="user_update"),
    path("users/delete/<int:pk>", DeleteUserView.as_view(), name="user_delete"),

    # API for vehicle routes
    path("vehicles/", VehicleListView.as_view(), name="vehicle_list"),                
    path("vehicles/create/", VehicleCreateView.as_view(), name="vehicle_create"),     
    path("vehicles/<int:pk>/", VehicleDetailView.as_view(), name="vehicle_detail"),
    path("vehicles/<int:pk>/update/", VehicleUpdateView.as_view(), name="vehicle_update"), 
    path("vehicles/<int:pk>/delete/", VehicleDeleteView.as_view(), name="vehicle_delete"),
    path("vehicle-types/", VehicleTypeListView.as_view(), name="vehicle_type_list"),


    path("", include(router.urls)),
]
