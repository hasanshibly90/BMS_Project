from django.urls import path
from .views import SpotListView, SpotDetailView, AssignParkingView, EndParkingView

app_name = "parking"

urlpatterns = [
    path("spots/",                SpotListView.as_view(),    name="spots"),
    path("spots/<int:pk>/",       SpotDetailView.as_view(),  name="spot_detail"),
    path("spots/<int:pk>/assign/",AssignParkingView.as_view(), name="spot_assign"),
    path("spots/<int:pk>/end/",   EndParkingView.as_view(),  name="spot_end"),
]
