from urllib.parse import urlencode

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
    paginate_by = 30  # default, user can override with ?per_page=...

    def get_paginate_by(self, queryset):
        per = (self.request.GET.get("per_page") or "").strip().lower()
        if per == "all":
            return None
        try:
            n = int(per)
            return max(1, min(n, 1000))
        except Exception:
            return self.paginate_by

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
        # keep query params except page/per_page for links
        params = self.request.GET.copy()
        params.pop("page", None); params.pop("per_page", None)
        base_qs = urlencode(params, doseq=True)
        ctx["base_qs"] = ("&" + base_qs) if base_qs else ""
        ctx["per_page"] = (self.request.GET.get("per_page") or str(self.paginate_by)).lower()
        ctx["per_page_options"] = ["25", "50", "100", "200", "all"]
        ctx["q"] = (self.request.GET.get("q") or "").strip()
        ctx["owner_type"] = (self.request.GET.get("owner_type") or "").strip()
        ctx["owner_types"] = Vehicle.OWNER_TYPES
        return ctx


# ───────── Spots ─────────
class SpotListView(ListView):
    model = ParkingSpot
    template_name = "parking/spot_list.html"
    paginate_by = None  # DEFAULT: show ALL (you can choose a page size via ?per_page=...)

    def get_paginate_by(self, queryset):
        per = (self.request.GET.get("per_page") or "").strip().lower()
        if per in ("", "all"):
            return None  # show all
        try:
            n = int(per)
            return max(1, min(n, 1000))
        except Exception:
            return None

    def get_queryset(self):
        # annotate occupied
        active_qs = ParkingAssignment.objects.filter(spot=OuterRef("pk"), end_date__isnull=True)
        qs = ParkingSpot.objects.select_related("flat").annotate(occupied=Exists(active_qs)).order_by("code")

        unit = (self.request.GET.get("unit") or "").strip().upper()
        floor = (self.request.GET.get("floor") or "").strip()
        reserved = (self.request.GET.get("reserved") or "").strip().lower()
        occupied = (self.request.GET.get("occupied") or "").strip().lower()

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
        # base_qs for page/per_page links
        params = self.request.GET.copy()
        params.pop("page", None); params.pop("per_page", None)
        base_qs = urlencode(params, doseq=True)
        ctx["base_qs"] = ("&" + base_qs) if base_qs else ""
        # per-page options (include total flats/“All (104)”)
        total_flats = Flat.objects.count()
        ctx["total_flats"] = total_flats
        ctx["per_page"] = (self.request.GET.get("per_page") or "all").lower()
        # Offer exact 104 (or whatever total_flats is), plus common sizes
        opts = ["25", "50", "100"]
        if str(total_flats) not in opts:
            opts.append(str(total_flats))
        opts.append("all")
        ctx["per_page_options"] = opts
        # current filter selections
        ctx["unit"] = (self.request.GET.get("unit") or "").strip().upper()
        ctx["floor"] = (self.request.GET.get("floor") or "").strip()
        ctx["reserved"] = (self.request.GET.get("reserved") or "").strip().lower()
        ctx["occupied"] = (self.request.GET.get("occupied") or "").strip().lower()
        ctx["units"] = list("ABCDEFGH")
        ctx["floors"] = list(range(1, 15))
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
    def post(self, request):
        created = 0
        updated = 0
        for flat in Flat.objects.all().order_by("floor", "unit"):
            code = f"{flat.unit}-{flat.floor:02d}"
            spot = getattr(flat, "parking_spot", None)
            if spot:
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
            ParkingSpot.objects.create(code=code_to_use, level=1, is_reserved=True, flat=flat)
            created += 1
        messages.success(request, f"Parking spots synced from flats. Created {created}, updated {updated}.")
        return redirect("parking:spot_list")
