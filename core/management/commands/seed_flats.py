from django.core.management.base import BaseCommand
from flats.models import Flat

class Command(BaseCommand):
    help = "Create 14 floors × 8 units (A–H) if none exist."

    def handle(self, *args, **kwargs):
        if Flat.objects.exists():
            self.stdout.write(self.style.WARNING("Flats already exist. Skipping."))
            return
        units = list("ABCDEFGH")
        created = 0
        for floor in range(1, 15):
            for u in units:
                Flat.objects.create(floor=floor, unit=u)
                created += 1
        self.stdout.write(self.style.SUCCESS(f"Created {created} flats."))
