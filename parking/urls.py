from django.urls import path
from .views import (
    VehicleListView, VehicleCreateView, VehicleUpdateView,
    SpotListView, SpotCreateView, SpotUpdateView, SpotDetailView, SpotSeedAllView,
)

app_name = "parking"

urlpatterns = [
    # Vehicles
    path("vehicles/", VehicleListView.as_view(), name="vehicle_list"),
    path("vehicles/create/", VehicleCreateView.as_view(), name="vehicle_create"),
    path("vehicles/<int:pk>/edit/", VehicleUpdateView.as_view(), name="vehicle_edit"),

    # Spots
    path("spots/", SpotListView.as_view(), name="spot_list"),
    path("spots/create/", SpotCreateView.as_view(), name="spot_create"),
    path("spots/<int:pk>/", SpotDetailView.as_view(), name="spot_detail"),
    path("spots/<int:pk>/edit/", SpotUpdateView.as_view(), name="spot_edit"),

    # Bulk create/sync: Flat → ParkingSpot
    path("spots/seed/", SpotSeedAllView.as_view(), name="spot_seed_all"),
]
