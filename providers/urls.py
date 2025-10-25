from django.urls import path
from .views import ServiceProviderRegisterView, ServiceProviderThankYouView, ServiceProviderListView

app_name = "providers"

urlpatterns = [
    path("register/", ServiceProviderRegisterView.as_view(), name="register"),
    path("thank-you/", ServiceProviderThankYouView.as_view(), name="thank_you"),
    path("list/", ServiceProviderListView.as_view(), name="list"),  # optional
]
