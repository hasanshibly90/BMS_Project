from django.db import models
from django.db.models import Q
from flats.models import Flat


def upload_to(instance, filename):
    kind = instance.__class__.__name__.lower()
    return f"docs/{kind}/{filename}"


class Owner(models.Model):
    name = models.CharField(max_length=120)
    phone = models.CharField(max_length=40, blank=True)
    email = models.EmailField(blank=True)
    photo = models.ImageField(upload_to=upload_to, blank=True, null=True)
    nid_image = models.ImageField(upload_to=upload_to, blank=True, null=True)
    address = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return self.name


class Lessee(models.Model):
    name = models.CharField(max_length=120)
    phone = models.CharField(max_length=40, blank=True)
    email = models.EmailField(blank=True)
    photo = models.ImageField(upload_to=upload_to, blank=True, null=True)
    nid_image = models.ImageField(upload_to=upload_to, blank=True, null=True)
    address = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return self.name


class Ownership(models.Model):
    flat = models.ForeignKey(Flat, on_delete=models.CASCADE, related_name="ownerships")
    owner = models.ForeignKey(Owner, on_delete=models.CASCADE, related_name="ownerships")
    start_date = models.DateField()
    end_date = models.DateField(blank=True, null=True)

    class Meta:
        ordering = ['-start_date']
        constraints = [
            # Only one active (end_date IS NULL) ownership per flat
            models.UniqueConstraint(
                fields=['flat'],
                condition=Q(end_date__isnull=True),
                name='one_active_ownership_per_flat',
            ),
        ]
        indexes = [
            models.Index(fields=['flat', 'end_date'], name='own_flat_end_idx'),
            models.Index(fields=['flat', 'start_date'], name='own_flat_start_idx'),
        ]

    def __str__(self):
        to = self.end_date or "present"
        return f"{self.flat} → {self.owner} ({self.start_date} to {to})"

    @property
    def is_active(self) -> bool:
        return self.end_date is None


class Tenancy(models.Model):
    flat = models.ForeignKey(Flat, on_delete=models.CASCADE, related_name="tenancies")
    lessee = models.ForeignKey(Lessee, on_delete=models.CASCADE, related_name="tenancies")
    start_date = models.DateField()
    end_date = models.DateField(blank=True, null=True)
    agreement_file = models.FileField(upload_to=upload_to, blank=True, null=True)

    class Meta:
        ordering = ['-start_date']
        constraints = [
            # Only one active (end_date IS NULL) tenancy per flat
            models.UniqueConstraint(
                fields=['flat'],
                condition=Q(end_date__isnull=True),
                name='one_active_tenancy_per_flat',
            ),
        ]
        indexes = [
            models.Index(fields=['flat', 'end_date'], name='ten_flat_end_idx'),
            models.Index(fields=['flat', 'start_date'], name='ten_flat_start_idx'),
        ]

    def __str__(self):
        to = self.end_date or "present"
        return f"{self.flat} → {self.lessee} ({self.start_date} to {to})"

    @property
    def is_active(self) -> bool:
        return self.end_date is None
