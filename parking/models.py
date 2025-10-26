from django.db import models
from django.core.exceptions import ValidationError

from flats.models import Flat
from people.models import Owner, Lessee


class ExternalOwner(models.Model):
    UBER_DRIVER = "UBER_DRIVER"
    RENTAL_COMPANY = "RENTAL_COMPANY"
    KIND_CHOICES = [
        (UBER_DRIVER, "Uber driver"),
        (RENTAL_COMPANY, "Rental company"),
    ]

    kind = models.CharField(max_length=20, choices=KIND_CHOICES)
    name = models.CharField(max_length=120)
    phone = models.CharField(max_length=40, blank=True)
    company = models.CharField(max_length=120, blank=True)

    def __str__(self):
        label = dict(self.KIND_CHOICES).get(self.kind, self.kind.title())
        return f"{self.name} ({label}{', ' + self.company if self.company else ''})"


class ParkingSpot(models.Model):
    code = models.CharField(max_length=10, unique=True, help_text="e.g., E-10")
    level = models.PositiveSmallIntegerField(default=1)
    is_reserved = models.BooleanField(default=False)
    notes = models.CharField(max_length=255, blank=True, default="")

    # Dedicated spot for a flat (so Flat gets f.parking_spot)
    flat = models.OneToOneField(
        Flat, null=True, blank=True, on_delete=models.SET_NULL, related_name="parking_spot"
    )

    class Meta:
        ordering = ["code"]

    def __str__(self):
        return self.code

    def _flat_code(self):
        if self.flat_id and self.flat:
            return f"{self.flat.unit}-{self.flat.floor:02d}"
        return None

    def save(self, *args, **kwargs):
        # Default: if code is blank and a flat is chosen, use flat code (E-10 etc.)
        if (not self.code or not self.code.strip()) and self.flat_id:
            fc = self._flat_code()
            if fc:
                self.code = fc
        super().save(*args, **kwargs)


class Vehicle(models.Model):
    CAR = "CAR"; BIKE = "BIKE"; MICROBUS = "MICROBUS"; TRUCK = "TRUCK"; OTHER = "OTHER"
    V_TYPES = [(CAR, "Car"), (BIKE, "Bike"), (MICROBUS, "Microbus"), (TRUCK, "Truck"), (OTHER, "Other")]

    OWNER = "OWNER"; LESSEE = "LESSEE"
    UBER_DRIVER = ExternalOwner.UBER_DRIVER; RENTAL_COMPANY = ExternalOwner.RENTAL_COMPANY
    OWNER_TYPES = [
        (OWNER, "Owner"),
        (LESSEE, "Lessee"),
        (UBER_DRIVER, "Uber driver"),
        (RENTAL_COMPANY, "Rental company"),
    ]

    plate_no = models.CharField(max_length=20, unique=True)
    vehicle_type = models.CharField(max_length=20, choices=V_TYPES, default=CAR)
    make = models.CharField(max_length=50, blank=True)
    model = models.CharField(max_length=50, blank=True)
    color = models.CharField(max_length=30, blank=True)
    tag_no = models.CharField(max_length=50, blank=True, help_text="RFID / Sticker no (optional)")

    owner_type = models.CharField(max_length=20, choices=OWNER_TYPES)
    owner = models.ForeignKey(Owner, null=True, blank=True, on_delete=models.SET_NULL, related_name="vehicles")
    lessee = models.ForeignKey(Lessee, null=True, blank=True, on_delete=models.SET_NULL, related_name="vehicles")
    external_owner = models.ForeignKey(
        ExternalOwner, null=True, blank=True, on_delete=models.SET_NULL, related_name="vehicles"
    )

    # Optional manual link to a flat (useful for externals or edge cases)
    flat = models.ForeignKey(Flat, null=True, blank=True, on_delete=models.SET_NULL, related_name="vehicles")

    is_active = models.BooleanField(default=True)
    notes = models.CharField(max_length=255, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["plate_no"]

    def __str__(self):
        return self.plate_no

    def save(self, *args, **kwargs):
        if self.plate_no:
            self.plate_no = self.plate_no.upper().replace(" ", "")
        super().save(*args, **kwargs)

    def clean(self):
        picks = [self.owner_id, self.lessee_id, self.external_owner_id]
        if sum(1 for x in picks if x) != 1:
            raise ValidationError("Select exactly one: Owner or Lessee or External owner.")
        if self.owner_type == self.OWNER and not self.owner_id:
            raise ValidationError("owner_type=Owner requires selecting an Owner.")
        if self.owner_type == self.LESSEE and not self.lessee_id:
            raise ValidationError("owner_type=Lessee requires selecting a Lessee.")
        if self.owner_type in (self.UBER_DRIVER, self.RENTAL_COMPANY) and not self.external_owner_id:
            raise ValidationError("External owner details required for Uber driver / Rental company.")

    @property
    def owner_label(self):
        if self.owner_id:
            return f"Owner — {self.owner.name}"
        if self.lessee_id:
            return f"Lessee — {self.lessee.name}"
        if self.external_owner_id:
            return str(self.external_owner)
        return "—"

    @property
    def flat_code(self):
        try:
            if self.owner_id:
                from people.models import Ownership
                o = Ownership.objects.filter(owner_id=self.owner_id, end_date__isnull=True).select_related("flat").first()
                if o: return f"{o.flat.unit}-{o.flat.floor:02d}"
            if self.lessee_id:
                from people.models import Tenancy
                t = Tenancy.objects.filter(lessee_id=self.lessee_id, end_date__isnull=True).select_related("flat").first()
                if t: return f"{t.flat.unit}-{t.flat.floor:02d}"
        except Exception:
            pass
        if self.flat_id and self.flat: return f"{self.flat.unit}-{self.flat.floor:02d}"
        return None

    @property
    def current_parking(self):
        rel = getattr(self, "assignments", None)
        return rel.filter(end_date__isnull=True).select_related("spot").first() if rel is not None else None


class ParkingAssignment(models.Model):
    vehicle = models.ForeignKey(
        Vehicle, on_delete=models.CASCADE, related_name="assignments",
        null=True, blank=True  # keep nullable to avoid legacy prompts
    )
    spot = models.ForeignKey(ParkingSpot, on_delete=models.CASCADE, related_name="assignments")
    start_date = models.DateField()
    end_date = models.DateField(blank=True, null=True)
    driver_name = models.CharField(max_length=120, blank=True, default="")  # NEW
    remarks = models.CharField(max_length=255, blank=True, default="")

    class Meta:
        ordering = ["-start_date"]
        constraints = [
            models.UniqueConstraint(
                fields=["vehicle"],
                condition=models.Q(end_date__isnull=True, vehicle__isnull=False),
                name="one_active_assignment_per_vehicle",
            ),
            models.UniqueConstraint(
                fields=["spot"],
                condition=models.Q(end_date__isnull=True),
                name="one_active_assignment_per_spot",
            ),
        ]

    def __str__(self):
        span = f"{self.start_date} → {self.end_date or 'present'}"
        v = self.vehicle.plate_no if self.vehicle_id else "—"
        return f"{v} → {self.spot} ({span})"

    @property
    def is_active(self):
        return self.end_date is None

    def clean(self):
        if self.end_date and self.end_date < self.start_date:
            raise ValidationError("End date cannot be before start date.")
