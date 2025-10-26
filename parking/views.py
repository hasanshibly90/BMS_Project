from django.contrib import messages
from django.db import transaction
from django.db.models import Q
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import ListView, CreateView, UpdateView, DetailView

from .models import Vehicle, ParkingSpot, ParkingAssignment
from .forms import VehicleForm, ParkingSpotForm


# ───────── Vehicles ─────────
class VehicleListView(ListView):
    model = Vehicle
    template_name = "parking/vehicle_list.html"
    paginate_by = 30

    def get_queryset(self):
        qs = Vehicle.objects.select_related("owner", "lessee", "external_owner").order_by("plate_no")
        q = (self.request.GET.get("q") or "").strip()
        kind = (self.request.GET.get("owner_type") or "").strip()
        if q:
            qs = qs.filter(
                Q(plate_no__icontains=q) |
                Q(owner__name__icontains=q) |
                Q(lessee__name__icontains=q) |
                Q(external_owner__name__icontains=q)
            )
        if kind and kind in dict(Vehicle.OWNER_TYPES):
            qs = qs.filter(owner_type=kind)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["q"] = (self.request.GET.get("q") or "").strip()
        ctx["owner_type"] = (self.request.GET.get("owner_type") or "").strip()
        ctx["owner_types"] = Vehicle.OWNER_TYPES
        return ctx


class VehicleCreateView(CreateView):
    model = Vehicle
    form_class = VehicleForm
    template_name = "parking/vehicle_form.html"
    success_url = reverse_lazy("parking:vehicle_list")

    @transaction.atomic
    def form_valid(self, form):
        resp = super().form_valid(form)
        v: Vehicle = self.object
        if form.cleaned_data.get("assign_parking") and form.cleaned_data.get("spot"):
            prev = ParkingAssignment.objects.filter(vehicle=v, end_date__isnull=True).first()
            if prev:
                prev.end_date = form.cleaned_data.get("start_date") or timezone.localdate()
                prev.save(update_fields=["end_date"])
            ParkingAssignment.objects.create(
                vehicle=v,
                spot=form.cleaned_data["spot"],
                start_date=form.cleaned_data.get("start_date") or timezone.localdate(),
            )
            messages.success(self.request, "Vehicle saved and parking assigned.")
        else:
            messages.success(self.request, "Vehicle saved.")
        return resp


class VehicleUpdateView(UpdateView):
    model = Vehicle
    form_class = VehicleForm
    template_name = "parking/vehicle_form.html"
    success_url = reverse_lazy("parking:vehicle_list")

    @transaction.atomic
    def form_valid(self, form):
        resp = super().form_valid(form)
        v: Vehicle = self.object
        if form.cleaned_data.get("assign_parking") and form.cleaned_data.get("spot"):
            prev = ParkingAssignment.objects.filter(vehicle=v, end_date__isnull=True).first()
            if prev:
                prev.end_date = form.cleaned_data.get("start_date") or timezone.localdate()
                prev.save(update_fields=["end_date"])
            ParkingAssignment.objects.create(
                vehicle=v,
                spot=form.cleaned_data["spot"],
                start_date=form.cleaned_data.get("start_date") or timezone.localdate(),
            )
            messages.success(self.request, "Vehicle updated and parking assigned.")
        else:
            messages.success(self.request, "Vehicle updated.")
        return resp


# ───────── Spots ─────────
class SpotListView(ListView):
    model = ParkingSpot
    template_name = "parking/spot_list.html"
    paginate_by = 50
    ordering = ["code"]


class SpotCreateView(CreateView):
    model = ParkingSpot
    form_class = ParkingSpotForm
    template_name = "parking/spot_form.html"
    success_url = reverse_lazy("parking:spot_list")

    @transaction.atomic
    def form_valid(self, form):
        resp = super().form_valid(form)
        s: ParkingSpot = self.object
        if form.cleaned_data.get("assign_now") and form.cleaned_data.get("vehicle"):
            prev = ParkingAssignment.objects.filter(spot=s, end_date__isnull=True).first()
            if prev:
                prev.end_date = form.cleaned_data.get("start_date") or timezone.localdate()
                prev.save(update_fields=["end_date"])
            ParkingAssignment.objects.create(
                vehicle=form.cleaned_data["vehicle"],
                spot=s,
                start_date=form.cleaned_data.get("start_date") or timezone.localdate(),
                driver_name=form.cleaned_data.get("driver_name") or "",
            )
            messages.success(self.request, "Spot created and assigned.")
        else:
            messages.success(self.request, "Spot created.")
        return resp


class SpotUpdateView(UpdateView):
    model = ParkingSpot
    form_class = ParkingSpotForm
    template_name = "parking/spot_form.html"
    success_url = reverse_lazy("parking:spot_list")

    @transaction.atomic
    def form_valid(self, form):
        resp = super().form_valid(form)
        s: ParkingSpot = self.object
        if form.cleaned_data.get("assign_now") and form.cleaned_data.get("vehicle"):
            prev = ParkingAssignment.objects.filter(spot=s, end_date__isnull=True).first()
            if prev:
                prev.end_date = form.cleaned_data.get("start_date") or timezone.localdate()
                prev.save(update_fields=["end_date"])
            ParkingAssignment.objects.create(
                vehicle=form.cleaned_data["vehicle"],
                spot=s,
                start_date=form.cleaned_data.get("start_date") or timezone.localdate(),
                driver_name=form.cleaned_data.get("driver_name") or "",
            )
            messages.success(self.request, "Spot updated and assigned.")
        else:
            messages.success(self.request, "Spot updated.")
        return resp


class SpotDetailView(DetailView):
    model = ParkingSpot
    template_name = "parking/spot_detail.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        spot: ParkingSpot = self.object
        pa = spot.active_assignment()
        ctx["active_assignment"] = pa
        return ctx
