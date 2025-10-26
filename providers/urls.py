from django.urls import path
from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.http import require_http_methods
from django.http import Http404

# Robustly import your existing list/create/update views
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

# Robustly resolve the model class (Provider or ServiceProvider)
ProviderModel = None
try:
    from .models import Provider as ProviderModel
except Exception:
    try:
        from .models import ServiceProvider as ProviderModel
    except Exception:
        ProviderModel = None


@require_http_methods(["GET", "POST"])
def provider_delete(request, pk: int):
    """
    GET: show confirm page
    POST: delete and redirect back to the list
    """
    if ProviderModel is None:
        raise Http404("Provider model not found in providers.models")

    obj = get_object_or_404(ProviderModel, pk=pk)
    if request.method == "POST":
        obj.delete()
        return redirect("providers:list")
    return render(request, "providers/provider_confirm_delete.html", {"object": obj})


app_name = "providers"

urlpatterns = [
    path("", ListViewClass.as_view(), name="list"),               # /providers/
    path("list/", ListViewClass.as_view(), name="list_alias"),    # /providers/list/ (alias)
    path("register/", CreateViewClass.as_view(), name="register"),
    path("<int:pk>/edit/", UpdateViewClass.as_view(), name="edit"),
    path("<int:pk>/delete/", provider_delete, name="delete"),     # ← added to fix NoReverseMatch
]
