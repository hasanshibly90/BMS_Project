from django.db.models import Q
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView

from .models import ServiceProvider, ServiceCategory
from .forms import ServiceProviderForm


class ProviderListView(ListView):
    """
    List providers with filters:
      - q: name/phone/email/address/notes search
      - category: category id (from admin)
      - active: 'yes'/'no' or empty for any
    Provides 'categories' to the template for the dropdown.
    """
    model = ServiceProvider
    template_name = "providers/provider_list.html"
    paginate_by = 30

    def get_queryset(self):
        qs = (
            ServiceProvider.objects
            .select_related("category")
            .all()
            .order_by("category__name", "full_name")
        )

        q = (self.request.GET.get("q") or "").strip()
        cat = (self.request.GET.get("category") or "").strip()
        active = (self.request.GET.get("active") or "").strip()

        if q:
            qs = qs.filter(
                Q(full_name__icontains=q) |
                Q(phone__icontains=q) |
                Q(email__icontains=q) |
                Q(address__icontains=q) |
                Q(notes__icontains=q)
            )

        if cat.isdigit():
            qs = qs.filter(category_id=int(cat))

        if active == "yes":
            qs = qs.filter(is_active=True)
        elif active == "no":
            qs = qs.filter(is_active=False)

        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["q"] = (self.request.GET.get("q") or "").strip()
        ctx["category"] = (self.request.GET.get("category") or "").strip()
        ctx["active"] = (self.request.GET.get("active") or "").strip()
        ctx["categories"] = ServiceCategory.objects.filter(is_active=True).order_by("name")
        return ctx


class ProviderCreateView(CreateView):
    """
    Register/Add a new Service Provider.
    """
    model = ServiceProvider
    form_class = ServiceProviderForm
    template_name = "providers/provider_form.html"
    success_url = reverse_lazy("providers:list")


class ProviderUpdateView(UpdateView):
    """
    Edit an existing Service Provider.
    """
    model = ServiceProvider
    form_class = ServiceProviderForm
    template_name = "providers/provider_form.html"
    success_url = reverse_lazy("providers:list")


class ProviderDeleteView(DeleteView):
    """
    Confirm + delete a Service Provider.
    """
    model = ServiceProvider
    template_name = "providers/provider_confirm_delete.html"
    success_url = reverse_lazy("providers:list")
