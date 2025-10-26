from django.urls import path

# Robust imports: prefer Provider*; fall back to ServiceProvider* if needed
try:
    from .views import ProviderListView as ListViewClass
except Exception:
    from .views import ServiceProviderListView as ListViewClass

try:
    from .views import ProviderCreateView as CreateViewClass
except Exception:
    from .views import ServiceProviderCreateView as CreateViewClass

try:
    from .views import ProviderUpdateView as UpdateViewClass
except Exception:
    from .views import ServiceProviderUpdateView as UpdateViewClass

app_name = "providers"

urlpatterns = [
    path("", ListViewClass.as_view(), name="list"),
    path("register/", CreateViewClass.as_view(), name="register"),
    path("<int:pk>/edit/", UpdateViewClass.as_view(), name="edit"),
]
