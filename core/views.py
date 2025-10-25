from django.views.generic import TemplateView
from flats.models import Flat
from parking.models import ParkingSpot

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
            try:
                spot = f.parking_spot
                parking_code = spot.code
                pa = spot.active_assignment()
                if pa:
                    vehicle = pa.vehicle_no or "—"
                spot_id = spot.pk
            except ParkingSpot.DoesNotExist:
                spot_id = None

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
