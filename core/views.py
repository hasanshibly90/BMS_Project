from django.views.generic import TemplateView
from django.db.models import Count
from importlib import import_module

class DashboardView(TemplateView):
    template_name = "core/dashboard.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        # Flats (required)
        Flat = import_module("flats.models").Flat
        all_flats = Flat.objects.all()
        ctx["flat_count"] = all_flats.count()

        # Status counts (safe defaults)
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
        # Preload into dict for O(1) lookup
        by_key = { (f.floor, f.unit): f.status_hint for f in all_flats }
        for floor in range(14, 1-1, -1):
            row = []
            for u in units:
                status = by_key.get((floor, u), "vacant")
                row.append({"unit": u, "floor": floor, "status": status})
            levels.append({"floor": floor, "cells": row})
        ctx["levels"] = levels

        return ctx
