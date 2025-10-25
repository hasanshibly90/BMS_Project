import re
from django.views.generic import TemplateView, FormView, View
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.contrib import messages
from django.utils import timezone
from django.db import transaction
from django.db.models import Count, Q

from flats.models import Flat
from people.models import Owner, Ownership, Lessee, Tenancy
from .forms import BulkOwnersForm

# Optional: if Parking app is installed, Overview can show parking + vehicle info.
try:
    from parking.models import ParkingSpot
except Exception:
    ParkingSpot = None


# ───────────────────────── Dashboard ─────────────────────────
class DashboardView(TemplateView):
    template_name = "core/dashboard.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        all_flats = Flat.objects.all()
        ctx["flat_count"] = all_flats.count()

        counts = dict(
            all_flats.values_list("status_hint")
            .annotate(c=Count("id"))
            .values_list("status_hint", "c")
        )
        ctx["cnt_owner"]  = counts.get("owner", 0)
        ctx["cnt_rented"] = counts.get("rented", 0)
        ctx["cnt_vacant"] = counts.get("vacant", 0)

        # Occupancy grid (floors 14..1, units A..H)
        units = list("ABCDEFGH")
        levels = []
        status_by = {(f.floor, f.unit): f.status_hint for f in all_flats}
        for floor in range(14, 0, -1):
            row = []
            for u in units:
                status = status_by.get((floor, u), "vacant")
                row.append({"unit": u, "floor": floor, "status": status})
            levels.append({"floor": floor, "cells": row})
        ctx["levels"] = levels

        return ctx


# ───────────────────────── Bulk owners paste tool ─────────────────────────
class BulkOwnersView(FormView):
    """
    Paste rows like:
        Flat no, Owner, Cell
        A-01, Md. Rahim, 01711123456
        E-10, Ashikur Rahman, 01711...
    Preview via form.dry_run; can optionally vacate flats not listed.
    """
    template_name = "core/bulk_owners.html"
    form_class = BulkOwnersForm
    success_url = reverse_lazy("bulk_owners")

    @staticmethod
    def _clean_flat_code(s: str):
        if not s:
            return None
        s = str(s).strip().upper().replace(" ", "")
        m = re.match(r"^([A-H])[-_]?0?(\d{1,2})$", s)
        if not m:
            return None
        unit, fl = m.group(1), int(m.group(2))
        if 1 <= fl <= 14:
            return unit, fl
        return None

    @staticmethod
    def _norm_phone(s: str) -> str:
        return re.sub(r"[^0-9]", "", str(s or ""))

    def form_valid(self, form):
        raw = form.cleaned_data["data"] or ""
        lines = [ln for ln in raw.splitlines() if ln.strip()]

        # remove header if present
        if lines and ("flat" in lines[0].lower() and "owner" in lines[0].lower()):
            lines = lines[1:]

        # parse rows (comma or tab)
        rows = []
        for ln in lines:
            parts = [p.strip() for p in re.split(r"[,\t]", ln) if p.strip()]
            if len(parts) < 2:
                continue
            flat_no, name = parts[0], parts[1]
            phone = parts[2] if len(parts) > 2 else ""
            rows.append((flat_no, name, phone))

        start_date = form.cleaned_data.get("start_date") or timezone.localdate()
        vacate_missing = bool(form.cleaned_data.get("vacate_missing"))
        dry_run = bool(form.cleaned_data.get("dry_run"))

        # map all flats
        flats = {(f.unit.upper(), int(f.floor)): f for f in Flat.objects.all()}
        touched = set()

        counters = dict(
            owners_created=0, owners_updated=0,
            owns_created=0, owns_ended=0,
            status_changed=0, skipped=0
        )
        would = counters.copy()

        def tally(dst, **kw):
            for k, v in kw.items():
                if v:
                    dst[k] += 1

        @transaction.atomic
        def _apply():
            nonlocal counters, would
            for flat_no, owner_name, phone in rows:
                parsed = self._clean_flat_code(flat_no)
                if not parsed or not owner_name:
                    tally(would if dry_run else counters, skipped=True)
                    continue

                unit, fl = parsed
                touched.add((unit, fl))
                flat = flats.get((unit, fl))
                if not flat:
                    tally(would if dry_run else counters, skipped=True)
                    continue

                phone_norm = self._norm_phone(phone)

                # upsert owner
                owner = None
                qs = Owner.objects.filter(name__iexact=owner_name)
                if phone_norm:
                    owner = qs.filter(phone__icontains=phone_norm).first()
                if not owner:
                    owner = qs.first()

                if not owner:
                    if dry_run:
                        tally(would, owners_created=True)
                    else:
                        owner = Owner.objects.create(name=owner_name, phone=phone_norm)
                        tally(counters, owners_created=True)
                else:
                    if phone_norm and owner.phone != phone_norm:
                        if dry_run:
                            tally(would, owners_updated=True)
                        else:
                            owner.phone = phone_norm
                            owner.save(update_fields=["phone"])
                            tally(counters, owners_updated=True)

                # end existing active ownership if owner differs
                current = Ownership.objects.filter(flat=flat, end_date__isnull=True).order_by("-start_date").first()

                if current and current.owner_id != owner.id:
                    if dry_run:
                        tally(would, owns_ended=True)
                        current = None
                    else:
                        current.end_date = start_date
                        current.save(update_fields=["end_date"])
                        tally(counters, owns_ended=True)
                        current = None

                if current is None:
                    if dry_run:
                        tally(would, owns_created=True)
                    else:
                        Ownership.objects.create(flat=flat, owner=owner, start_date=start_date)
                        tally(counters, owns_created=True)

                # set status to Owner-occupied
                if flat.status_hint != Flat.OWNER_OCCUPIED:
                    if dry_run:
                        tally(would, status_changed=True)
                    else:
                        flat.status_hint = Flat.OWNER_OCCUPIED
                        flat.save(update_fields=["status_hint"])
                        tally(counters, status_changed=True)

            # optionally vacate non-touched
            if vacate_missing:
                for (u, f), flat in flats.items():
                    if (u, f) in touched:
                        continue
                    curr = Ownership.objects.filter(flat=flat, end_date__isnull=True).order_by("-start_date").first()
                    if dry_run:
                        if curr:
                            tally(would, owns_ended=True)
                        if flat.status_hint != Flat.VACANT:
                            tally(would, status_changed=True)
                    else:
                        if curr:
                            curr.end_date = start_date
                            curr.save(update_fields=["end_date"])
                            tally(counters, owns_ended=True)
                        if flat.status_hint != Flat.VACANT:
                            flat.status_hint = Flat.VACANT
                            flat.save(update_fields=["status_hint"])
                            tally(counters, status_changed=True)

            if dry_run:
                # rollback silently
                raise transaction.TransactionManagementError("dry-run-rollback")

        try:
            _apply()
        except transaction.TransactionManagementError:
            pass

        msg = (
            f"Preview — would create owners: {would['owners_created']}, update owners: {would['owners_updated']}, "
            f"create ownerships: {would['owns_created']}, end ownerships: {would['owns_ended']}, "
            f"status changes: {would['status_changed']}, skipped: {would['skipped']}."
            if dry_run else
            f"Applied — owners created: {counters['owners_created']}, owners updated: {counters['owners_updated']}, "
            f"ownerships created: {counters['owns_created']}, ownerships ended: {counters['owns_ended']}, "
            f"status changes: {counters['status_changed']}, skipped: {counters['skipped']}."
        )
        (messages.info if dry_run else messages.success)(self.request, msg)
        return super().form_valid(form)


# ───────────────────────── Sync flat statuses ─────────────────────────
class SyncStatusView(View):
    template_name = "core/sync_status.html"

    def get(self, request):
        ctx = {
            "flat_count": Flat.objects.count(),
            "active_owners": Ownership.objects.filter(end_date__isnull=True).count(),
            "active_tenants": Tenancy.objects.filter(end_date__isnull=True).count(),
        }
        return render(request, self.template_name, ctx)

    def post(self, request):
        changed = 0
        for fl in Flat.objects.all():
            has_owner = Ownership.objects.filter(flat=fl, end_date__isnull=True).exists()
            has_tenant = Tenancy.objects.filter(flat=fl, end_date__isnull=True).exists()
            target = Flat.VACANT
            if has_tenant:
                target = Flat.RENTED
            elif has_owner:
                target = Flat.OWNER_OCCUPIED
            if fl.status_hint != target:
                fl.status_hint = target
                fl.save(update_fields=["status_hint"])
                changed += 1
        messages.success(request, f"Sync complete. Status updated on {changed} flats.")
        return redirect(reverse_lazy("sync_status"))


# ───────────────────────── At-a-glance board ─────────────────────────
class OverviewBoardView(TemplateView):
    template_name = "core/overview.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        rows = []
        for f in Flat.objects.all().order_by("floor", "unit"):
            occ_label, occ_name = "—", "—"
            if f.status_hint == f.RENTED and f.active_tenancy():
                occ_label, occ_name = "Lessee", f.active_tenancy().lessee.name
            elif f.status_hint == f.OWNER_OCCUPIED and f.active_ownership():
                occ_label, occ_name = "Owner", f.active_ownership().owner.name

            parking_code = "—"
            vehicle = "—"
            spot_id = None
            if ParkingSpot:
                try:
                    spot = f.parking_spot
                    parking_code = spot.code
                    spot_id = spot.pk
                    pa = spot.active_assignment()
                    if pa:
                        vehicle = pa.vehicle_no or "—"
                except ParkingSpot.DoesNotExist:
                    pass

            rows.append({
                "flat": f"{f.unit}-{f.floor:02d}",
                "status": f.get_status_hint_display(),
                "occ_label": occ_label,
                "occ_name": occ_name,
                "parking_code": parking_code,
                "vehicle": vehicle,
                "flat_id": f.pk,
                "spot_id": spot_id,
            })
        ctx["rows"] = rows
        return ctx
