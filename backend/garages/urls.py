from django.urls import path
from garages.views.create_garage_views import CreateGarageView
from garages.views.create_customer_views import CustomerCreateView, CustomerListView, CustomerDropdownView

urlpatterns = [
    path("garages/create/", CreateGarageView.as_view(), name="create-garage"),
    path("garages/customers/create/", CustomerCreateView.as_view(), name="create-customer"),
    path("garages/customers", CustomerListView.as_view(), name="list-customers"),
]
