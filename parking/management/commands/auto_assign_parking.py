from django.core.management.base import BaseCommand
from django.db import transaction
from flats.models import Flat
from parking.models import ParkingSpot, ParkingAssignment

class Command(BaseCommand):
    help = (
        "Auto-assign each ParkingSpot to the flat's current occupant "
        "(Lessee if rented, else Owner). Ends active assignment on the occupant's start date."
    )

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, **opts):
        dry = opts.get("dry_run", False)
        changed = 0
        total = 0

        @transaction.atomic
        def run():
            nonlocal changed, total
            for f in Flat.objects.all().order_by("floor", "unit"):
                total += 1
                start = None
                if f.status_hint == f.RENTED and f.active_tenancy():
                    start = f.active_tenancy().start_date
                elif f.status_hint == f.OWNER_OCCUPIED and f.active_ownership():
                    start = f.active_ownership().start_date
                if not start:
                    continue
                spot, _ = ParkingSpot.objects.get_or_create(flat=f)
                cur = spot.active_assignment()
                if cur and cur.end_date is None and cur.start_date != start:
                    cur.end_date = start
                    if not dry:
                        cur.save(update_fields=["end_date"])
                    changed += 1
                if not spot.active_assignment():
                    if not dry:
                        ParkingAssignment.objects.create(
                            spot=spot, start_date=start, vehicle_no="", note="Auto-assign"
                        )
                    changed += 1
            if dry:
                raise transaction.TransactionManagementError("dry run")

        try:
            run()
        except transaction.TransactionManagementError:
            pass

        self.stdout.write(self.style.SUCCESS(f"Processed: {total} spots, changes: {changed}, dry_run={dry}"))
