from django.urls import path
from .views import VehicleListView, VehicleCreateView, VehicleUpdateView, SpotListView

app_name = "parking"
urlpatterns = [
    path("vehicles/", VehicleListView.as_view(), name="vehicle_list"),
    path("vehicles/create/", VehicleCreateView.as_view(), name="vehicle_create"),
    path("vehicles/<int:pk>/edit/", VehicleUpdateView.as_view(), name="vehicle_edit"),
    path("spots/", SpotListView.as_view(), name="spot_list"),
]
