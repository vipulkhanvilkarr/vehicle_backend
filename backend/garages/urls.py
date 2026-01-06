from django.urls import path
from accounts.views import UserListView
from garages.views.create_garage_views import CreateGarageView
from garages.views.create_customer_views import CustomerCreateView, CustomerListView

urlpatterns = [
    path("garages/create/", CreateGarageView.as_view(), name="create-garage"),
    path("garages/customers/create/", CustomerCreateView.as_view(), name="create-customer"),
    path("garages/customers", CustomerListView.as_view(), name="list-customers"),
    path("users/", UserListView.as_view(), name="user_list"),    
    ]
