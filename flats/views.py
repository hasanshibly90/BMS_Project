from django.urls import reverse_lazy, reverse
from django.views.generic import ListView, CreateView, UpdateView, TemplateView, View
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Count, Q
from django.utils import timezone

from .models import Flat
from .forms import FlatForm, OwnershipForm, TenancyForm
from people.models import Ownership, Tenancy

class FlatListView(ListView):
    model = Flat
    template_name = 'flats/flat_list.html'
    paginate_by = 40

    def get_queryset(self):
        qs = Flat.objects.all().order_by('floor', 'unit')
        q = (self.request.GET.get('q') or '').strip()
        status = (self.request.GET.get('status') or '').strip()
        floor = (self.request.GET.get('floor') or '').strip()
        if q:
            if q.isdigit(): qs = qs.filter(floor=int(q))
            else: qs = qs.filter(Q(unit__iexact=q) | Q(remarks__icontains=q))
        if status in dict(Flat.STATUS_CHOICES): qs = qs.filter(status_hint=status)
        if floor.isdigit(): qs = qs.filter(floor=int(floor))
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['q'] = (self.request.GET.get('q') or '').strip()
        ctx['status'] = (self.request.GET.get('status') or '').strip()
        ctx['floor'] = (self.request.GET.get('floor') or '').strip()
        counts = dict(Flat.objects.values_list('status_hint').annotate(c=Count('id')).values_list('status_hint', 'c'))
        ctx['cnt_owner'] = counts.get('owner', 0)
        ctx['cnt_rented'] = counts.get('rented', 0)
        ctx['cnt_vacant'] = counts.get('vacant', 0)
        ctx['floors'] = list(range(1, 15))
        ctx['status_choices'] = Flat.STATUS_CHOICES
        return ctx

class FlatCreateView(CreateView):
    model = Flat
    form_class = FlatForm
    template_name = 'form.html'
    success_url = reverse_lazy('flats:list')

class FlatUpdateView(UpdateView):
    model = Flat
    form_class = FlatForm
    template_name = 'form.html'
    success_url = reverse_lazy('flats:list')

class FlatStatusUpdateView(View):
    def post(self, request, pk):
        obj = get_object_or_404(Flat, pk=pk)
        new_status = (request.POST.get('status_hint') or '').strip()
        valid = dict(Flat.STATUS_CHOICES).keys()
        if new_status in valid:
            obj.status_hint = new_status
            obj.save(update_fields=['status_hint'])
            messages.success(request, f'Status updated for {obj}.')
        else:
            messages.error(request, 'Invalid status.')
        return redirect(request.META.get('HTTP_REFERER') or reverse_lazy('flats:list'))

class FlatOccupancyView(TemplateView):
    template_name = "flats/occupancy.html"
    def get_context_data(self, pk, **kwargs):
        ctx = super().get_context_data(**kwargs)
        flat = get_object_or_404(Flat, pk=pk)
        ctx["flat"] = flat
        ctx["active_owner"] = flat.active_ownership()
        ctx["active_lessee"] = flat.active_tenancy()
        ctx["ownership_form"] = OwnershipForm()
        ctx["tenancy_form"] = TenancyForm()
        return ctx

class AssignOwnerView(View):
    def post(self, request, pk):
        flat = get_object_or_404(Flat, pk=pk)
        form = OwnershipForm(request.POST)
        if form.is_valid():
            start = form.cleaned_data["start_date"]; owner = form.cleaned_data["owner"]
            current = flat.active_ownership()
            if current and current.start_date <= start and current.end_date is None:
                current.end_date = start; current.save(update_fields=["end_date"])
            Ownership.objects.create(flat=flat, owner=owner, start_date=start, end_date=form.cleaned_data.get("end_date"))
            flat.status_hint = Flat.OWNER_OCCUPIED; flat.save(update_fields=["status_hint"])
            messages.success(request, f"Owner assigned to {flat}.")
        else:
            messages.error(request, "Invalid owner assignment.")
        return redirect(reverse("flats:occupancy", args=[flat.pk]))

class EndOwnerView(View):
    def post(self, request, pk):
        flat = get_object_or_404(Flat, pk=pk)
        current = flat.active_ownership()
        if current:
            current.end_date = timezone.now().date(); current.save(update_fields=["end_date"])
            if flat.active_tenancy() is None:
                flat.status_hint = Flat.VACANT; flat.save(update_fields=["status_hint"])
            messages.success(request, f"Ended owner for {flat}.")
        else:
            messages.info(request, "No active owner to end.")
        return redirect(reverse("flats:occupancy", args=[flat.pk]))

class AssignLesseeView(View):
    def post(self, request, pk):
        flat = get_object_or_404(Flat, pk=pk)
        form = TenancyForm(request.POST)
        if form.is_valid():
            start = form.cleaned_data["start_date"]; lessee = form.cleaned_data["lessee"]
            current = flat.active_tenancy()
            if current and current.start_date <= start and current.end_date is None:
                current.end_date = start; current.save(update_fields=["end_date"])
            Tenancy.objects.create(flat=flat, lessee=lessee, start_date=start, end_date=form.cleaned_data.get("end_date"))
            flat.status_hint = Flat.RENTED; flat.save(update_fields=["status_hint"])
            messages.success(request, f"Lessee assigned to {flat}.")
        else:
            messages.error(request, "Invalid lessee assignment.")
        return redirect(reverse("flats:occupancy", args=[flat.pk]))

class EndLesseeView(View):
    def post(self, request, pk):
        flat = get_object_or_404(Flat, pk=pk)
        current = flat.active_tenancy()
        if current:
            current.end_date = timezone.now().date(); current.save(update_fields=["end_date"])
            if flat.active_ownership() is None:
                flat.status_hint = Flat.VACANT; flat.save(update_fields=["status_hint"])
            messages.success(request, f"Ended lessee for {flat}.")
        else:
            messages.info(request, "No active lessee to end.")
        return redirect(reverse("flats:occupancy", args=[flat.pk]))
