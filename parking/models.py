from django.db import models
from django.db.models import Q
from flats.models import Flat

class ParkingSpot(models.Model):
    flat = models.OneToOneField(Flat, on_delete=models.CASCADE, related_name="parking_spot")
    code = models.CharField(max_length=8, unique=True, editable=False)
    location = models.CharField(max_length=120, blank=True)

    class Meta:
        ordering = ["flat__floor", "flat__unit"]

    def save(self, *args, **kwargs):
        self.code = f"{self.flat.unit}-{self.flat.floor:02d}"
        super().save(*args, **kwargs)

    def __str__(self):
        return self.code

    def active_assignment(self):
        return self.assignments.filter(end_date__isnull=True).order_by("-start_date").first()

    @property
    def is_assigned(self) -> bool:
        return self.active_assignment() is not None

class ParkingAssignment(models.Model):
    spot = models.ForeignKey(ParkingSpot, on_delete=models.CASCADE, related_name="assignments")
    start_date = models.DateField()
    end_date = models.DateField(blank=True, null=True)
    vehicle_no = models.CharField(max_length=40, blank=True)
    note = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["-start_date", "-id"]
        constraints = [
            models.UniqueConstraint(
                fields=["spot"],
                condition=Q(end_date__isnull=True),
                name="one_active_parking_per_spot",
            )
        ]

    def __str__(self):
        to = self.end_date or "present"
        return f"{self.spot.code} | {self.start_date} → {to}"
