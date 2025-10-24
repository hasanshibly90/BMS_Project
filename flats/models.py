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
