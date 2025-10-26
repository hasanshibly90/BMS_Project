from django.urls import path
from .views import (
    VehicleListView, VehicleCreateView, VehicleUpdateView,
    SpotListView, SpotCreateView,
)

app_name = "parking"

urlpatterns = [
    # Vehicles
    path("vehicles/", VehicleListView.as_view(), name="vehicle_list"),
    path("vehicles/create/", VehicleCreateView.as_view(), name="vehicle_create"),
    path("vehicles/<int:pk>/edit/", VehicleUpdateView.as_view(), name="vehicle_edit"),

    # Spots (keeps your Parking nav useful)
    path("spots/", SpotListView.as_view(), name="spot_list"),
    path("spots/create/", SpotCreateView.as_view(), name="spot_create"),
]
