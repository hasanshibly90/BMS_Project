# providers/urls.py
from django.urls import path
from .views import (
    ProviderListView,
    ProviderCreateView,
    ProviderUpdateView,
    ProviderDeleteView,
)

app_name = "providers"

urlpatterns = [
    # List + Register
    path("list/",     ProviderListView.as_view(),    name="list"),
    path("register/", ProviderCreateView.as_view(),  name="register"),

    # Edit + Delete (names used by your template)
    path("<int:pk>/edit/",   ProviderUpdateView.as_view(), name="edit"),
    path("<int:pk>/delete/", ProviderDeleteView.as_view(), name="delete"),
]
