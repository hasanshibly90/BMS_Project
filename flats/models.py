from django.db import models

class Flat(models.Model):
    VACANT = 'vacant'
    OWNER_OCCUPIED = 'owner'
    RENTED = 'rented'
    STATUS_CHOICES = [
        (VACANT, 'Vacant'),
        (OWNER_OCCUPIED, 'Owner-occupied'),
        (RENTED, 'Rented'),
    ]

    floor = models.PositiveSmallIntegerField()
    unit = models.CharField(max_length=1)  # A–H
    remarks = models.CharField(max_length=255, blank=True)
    status_hint = models.CharField(max_length=10, choices=STATUS_CHOICES, default=VACANT)

    class Meta:
        unique_together = ('floor', 'unit')
        ordering = ['floor', 'unit']

    def __str__(self):
        return f"{self.unit}-{self.floor:02d}"

    # --- Occupancy helpers (import lazily to avoid circular import) ---
    def active_ownership(self):
        from people.models import Ownership
        return (
            Ownership.objects
            .filter(flat=self, end_date__isnull=True)
            .order_by('-start_date')
            .first()
        )

    def active_tenancy(self):
        from people.models import Tenancy
        return (
            Tenancy.objects
            .filter(flat=self, end_date__isnull=True)
            .order_by('-start_date')
            .first()
        )

    @property
    def current_owner(self):
        o = self.active_ownership()
        return o.owner if o else None

    @property
    def current_lessee(self):
        t = self.active_tenancy()
        return t.lessee if t else None

    @property
    def occupant_label(self):
        if self.status_hint == self.OWNER_OCCUPIED and self.current_owner:
            return f"Owner: {self.current_owner.name}"
        if self.status_hint == self.RENTED and self.current_lessee:
            return f"Lessee: {self.current_lessee.name}"
        return "—"
