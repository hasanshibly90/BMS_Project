import re
from django.views.generic import TemplateView, FormView
from django.views import View
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.db import transaction
from django.contrib import messages
from django.db.models import Count

from .forms import BulkOwnersForm
from flats.models import Flat
from people.models import Owner, Ownership, Tenancy


# ──────────────────────────────────────────────────────────────────────────────
# Dashboard
# ──────────────────────────────────────────────────────────────────────────────
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
        ctx["cnt_owner"] = counts.get("owner", 0)
        ctx["cnt_rented"] = counts.get("rented", 0)
        ctx["cnt_vacant"] = counts.get("vacant", 0)

        # Occupancy grid (floors 14..1, units A..H)
        units = list("ABCDEFGH")
        levels = []
        by_key = {(f.floor, f.unit): f.status_hint for f in all_flats}
        for floor in range(14, 0, -1):
            row = []
            for u in units:
                status = by_key.get((floor, u), "vacant")
                row.append({"unit": u, "floor": floor, "status": status})
            levels.append({"floor": floor, "cells": row})
        ctx["levels"] = levels

        return ctx


# ──────────────────────────────────────────────────────────────────────────────
# One-time Manual Bulk Owners Paste Tool (Preview + Apply)
# ──────────────────────────────────────────────────────────────────────────────
class BulkOwnersView(FormView):
    template_name = "core/bulk_owners.html"
    form_class = BulkOwnersForm
    success_url = reverse_lazy("bulk_owners")

    # helpers
    @staticmethod
    def _clean_flat_no(s: str):
        if not s:
            return None
        s = str(s).strip().upper().replace(" ", "")
        if "-" not in s:
            return None
        unit, fl = s.split("-", 1)
        fl = re.sub(r"[^0-9]", "", fl or "")
        if not unit or not fl:
            return None
        try:
            return unit, int(fl)
        except ValueError:
            return None

    @staticmethod
    def _norm_phone(s: str) -> str:
        if not s:
            return ""
        return re.sub(r"[^0-9]", "", str(s).strip())

    def form_valid(self, form):
        raw = form.cleaned_data["data"] or ""
        lines = [ln for ln in raw.splitlines() if ln.strip()]
        # skip header if it looks like one
        if lines and ("flat" in lines[0].lower() and "owner" in lines[0].lower()):
            lines = lines[1:]

        # Parse rows: split by comma or tab
        rows = []
        for ln in lines:
            parts = [p.strip() for p in re.split(r"[,\t]", ln)]
            parts = [p for p in parts if p != ""]
            if len(parts) < 2:
                continue
            flat_no, phone = parts[0], parts[-1]
            name = ", ".join(parts[1:-1]) if len(parts) > 2 else ""
            rows.append((flat_no, name, phone))

        start_date = form.cleaned_data["start_date"] or timezone.localdate()
        vacate_missing = bool(form.cleaned_data["vacate_missing"])
        dry_run = bool(form.cleaned_data["dry_run"])

        # Prefetch flats
        flats = {(f.unit.upper(), int(f.floor)): f for f in Flat.objects.all()}
        touched = set()

        # Counters
        c = dict(
            owners_created=0,
            owners_updated=0,
            ownerships_created=0,
            ownerships_ended=0,
            status_changed=0,
            skipped=0,
        )
        would = c.copy()

        def tally(dst, *, create_owner=False, update_owner=False,
                  create_ownership=False, end_ownership=False,
                  change_status=False, skipped=False):
            if create_owner: dst["owners_created"] += 1
            if update_owner: dst["owners_updated"] += 1
            if create_ownership: dst["ownerships_created"] += 1
            if end_ownership: dst["ownerships_ended"] += 1
            if change_status: dst["status_changed"] += 1
            if skipped: dst["skipped"] += 1

        @transaction.atomic
        def _apply():
            nonlocal c, would

            for flat_no, owner_name, phone in rows:
                parsed = self._clean_flat_no(flat_no)
                if not parsed or not owner_name:
                    (tally(would, skipped=True) if dry_run else tally(c, skipped=True))
                    continue

                unit, floor = parsed
                touched.add((unit, floor))
                flat = flats.get((unit, floor))
                if not flat:
                    (tally(would, skipped=True) if dry_run else tally(c, skipped=True))
                    continue

                phone_norm = self._norm_phone(phone)

                # Upsert Owner by (name + optional phone)
                qs = Owner.objects.filter(name__iexact=owner_name)
                owner = qs.filter(phone__icontains=phone_norm).first() if phone_norm else None
                if not owner:
                    owner = qs.first()

                created_owner = updated_owner = False
                if not owner:
                    if dry_run:
                        tally(would, create_owner=True)
                    else:
                        owner = Owner.objects.create(name=owner_name, phone=phone_norm)
                        created_owner = True
                elif phone_norm and owner.phone != phone_norm:
                    if dry_run:
                        tally(would, update_owner=True)
                    else:
                        owner.phone = phone_norm
                        owner.save(update_fields=["phone"])
                        updated_owner = True

                # Active ownership
                current = (
                    Ownership.objects.filter(flat=flat, end_date__isnull=True)
                    .order_by("-start_date")
                    .first()
                )

                ended = created = False
                if current and (not dry_run) and current.owner_id != owner.id:
                    current.end_date = start_date
                    current.save(update_fields=["end_date"])
                    ended = True
                    current = None
                elif current and dry_run and current.owner_id != (owner.id if owner else -1):
                    tally(would, end_ownership=True)
                    current = None

                if current is None:
                    if dry_run:
                        tally(would, create_ownership=True)
                    else:
                        Ownership.objects.create(flat=flat, owner=owner, start_date=start_date)
                        created = True

                # Sync status → owner
                status_change = False
                if flat.status_hint != Flat.OWNER_OCCUPIED:
                    if dry_run:
                        tally(would, change_status=True)
                    else:
                        flat.status_hint = Flat.OWNER_OCCUPIED
                        flat.save(update_fields=["status_hint"])
                        status_change = True

                if not dry_run:
                    tally(
                        c,
                        create_owner=created_owner,
                        update_owner=updated_owner,
                        create_ownership=created,
                        end_ownership=ended,
                        change_status=status_change,
                    )

            # Optionally vacate non-touched flats
            if vacate_missing:
                for (u, f), flat in flats.items():
                    if (u, f) in touched:
                        continue
                    current = (
                        Ownership.objects.filter(flat=flat, end_date__isnull=True)
                        .order_by("-start_date")
                        .first()
                    )
                    if dry_run:
                        if current:
                            tally(would, end_ownership=True)
                        if flat.status_hint != Flat.VACANT:
                            tally(would, change_status=True)
                    else:
                        if current:
                            current.end_date = start_date
                            current.save(update_fields=["end_date"])
                            tally(c, end_ownership=True)
                        if flat.status_hint != Flat.VACANT:
                            flat.status_hint = Flat.VACANT
                            flat.save(update_fields=["status_hint"])
                            tally(c, change_status=True)

            if dry_run:
                transaction.set_rollback(True)

        _apply()

        msg = (
            f"Preview — would create owners: {would['owners_created']}, update owners: {would['owners_updated']}, "
            f"create ownerships: {would['ownerships_created']}, end ownerships: {would['ownerships_ended']}, "
            f"status changes: {would['status_changed']}, skipped: {would['skipped']}."
            if dry_run else
            f"Applied — owners created: {c['owners_created']}, owners updated: {c['owners_updated']}, "
            f"ownerships created: {c['ownerships_created']}, end ownerships: {c['ownerships_ended']}, "
            f"status changes: {c['status_changed']}, skipped: {c['skipped']}."
        )
        (messages.info if dry_run else messages.success)(self.request, msg)
        return super().form_valid(form)


# ──────────────────────────────────────────────────────────────────────────────
# One-click Sync: align Flat.status_hint with active Ownership/Tenancy
# ──────────────────────────────────────────────────────────────────────────────
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
        return redirect(reverse("sync_status"))
