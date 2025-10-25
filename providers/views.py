from django.views.generic import CreateView, ListView, TemplateView
from django.urls import reverse_lazy
from .models import ServiceProvider
from .forms import ServiceProviderForm

class ServiceProviderRegisterView(CreateView):
    model = ServiceProvider
    form_class = ServiceProviderForm
    template_name = "providers/register.html"
    success_url = reverse_lazy("providers:thank_you")

class ServiceProviderThankYouView(TemplateView):
    template_name = "providers/thank_you.html"

# Optional simple list page to review entries (can be staff-only if needed)
class ServiceProviderListView(ListView):
    model = ServiceProvider
    template_name = "providers/provider_list.html"
    paginate_by = 50

    def get_queryset(self):
        qs = ServiceProvider.objects.select_related("category").all().order_by("category__name", "full_name")
        q = (self.request.GET.get("q") or "").strip()
        if q:
            qs = qs.filter(full_name__icontains=q)
        cat = (self.request.GET.get("category") or "").strip()
        if cat:
            qs = qs.filter(category__name__iexact=cat)
        return qs
