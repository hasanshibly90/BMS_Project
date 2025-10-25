from django.core.management.base import BaseCommand
from flats.models import Flat
from parking.models import ParkingSpot

class Command(BaseCommand):
    help = "Create a ParkingSpot for every Flat (code = flat code). Skips existing."

    def handle(self, *args, **kwargs):
        created = 0
        for flat in Flat.objects.all():
            _, made = ParkingSpot.objects.get_or_create(flat=flat)
            if made:
                created += 1
        self.stdout.write(self.style.SUCCESS(
            f"Parking spots ready. Created: {created}, total: {ParkingSpot.objects.count()}"
        ))
