from django.contrib import messages
from django.db import transaction
from django.db.models import Q, Exists, OuterRef
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import ListView, CreateView, UpdateView, DetailView

from flats.models import Flat
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

    def get_queryset(self):
        # Base queryset with a fast "occupied" annotation (active assignment exists)
        active_qs = ParkingAssignment.objects.filter(
            spot=OuterRef("pk"), end_date__isnull=True
        )
        qs = (
            ParkingSpot.objects.select_related("flat")
            .annotate(occupied=Exists(active_qs))
            .order_by("code")
        )

        # Filters
        unit = (self.request.GET.get("unit") or "").strip().upper()
        floor = (self.request.GET.get("floor") or "").strip()
        reserved = (self.request.GET.get("reserved") or "").strip().lower()  # yes/no/blank
        occupied = (self.request.GET.get("occupied") or "").strip().lower()  # yes/no/blank

        if unit:
            qs = qs.filter(flat__unit=unit)
        if floor.isdigit():
            qs = qs.filter(flat__floor=int(floor))

        if reserved == "yes":
            qs = qs.filter(is_reserved=True)
        elif reserved == "no":
            qs = qs.filter(is_reserved=False)

        if occupied == "yes":
            qs = qs.filter(occupied=True)
        elif occupied == "no":
            qs = qs.filter(occupied=False)

        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        # Current selections
        ctx["unit"] = (self.request.GET.get("unit") or "").strip().upper()
        ctx["floor"] = (self.request.GET.get("floor") or "").strip()
        ctx["reserved"] = (self.request.GET.get("reserved") or "").strip().lower()
        ctx["occupied"] = (self.request.GET.get("occupied") or "").strip().lower()
        # Choices
        ctx["units"] = list("ABCDEFGH")  # A–H
        ctx["floors"] = list(range(1, 15))  # 1..14
        return ctx


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


class SpotSeedAllView(View):
    """
    Create/align one ParkingSpot per Flat:
      - code = "<UNIT>-<FLOOR two-digits>"
      - link spot.flat = Flat (OneToOne)
      - default level=1, is_reserved=True for dedicated spots
    """
    def post(self, request):
        created = 0
        updated = 0
        for flat in Flat.objects.all().order_by("floor", "unit"):
            code = f"{flat.unit}-{flat.floor:02d}"
            spot = getattr(flat, "parking_spot", None)
            if spot:
                # Sync code if unique and different
                if spot.code != code and not ParkingSpot.objects.filter(code=code).exclude(pk=spot.pk).exists():
                    spot.code = code
                    spot.save(update_fields=["code"])
                updated += 1
                continue

            code_to_use = code
            if ParkingSpot.objects.filter(code=code_to_use).exists():
                n = 2
                while ParkingSpot.objects.filter(code=f"{code}-{n}").exists():
                    n += 1
                code_to_use = f"{code}-{n}"

            ParkingSpot.objects.create(
                code=code_to_use,
                level=1,
                is_reserved=True,
                flat=flat,
            )
            created += 1

        messages.success(request, f"Parking spots synced from flats. Created {created}, updated {updated}.")
        return redirect("parking:spot_list")
