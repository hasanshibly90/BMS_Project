from django.urls import path
from .views import (
    ServiceProviderListView,
    ServiceProviderCreateView,
    ServiceProviderUpdateView,
)

app_name = "providers"

urlpatterns = [
    path("", ServiceProviderListView.as_view(), name="list"),
    path("register/", ServiceProviderCreateView.as_view(), name="register"),
    path("<int:pk>/edit/", ServiceProviderUpdateView.as_view(), name="edit"),
]
