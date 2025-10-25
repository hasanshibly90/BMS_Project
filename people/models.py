from django.db import models
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
    def __str__(self): return self.name

class Lessee(models.Model):
    name = models.CharField(max_length=120)
    phone = models.CharField(max_length=40, blank=True)
    email = models.EmailField(blank=True)
    photo = models.ImageField(upload_to=upload_to, blank=True, null=True)
    nid_image = models.ImageField(upload_to=upload_to, blank=True, null=True)
    address = models.CharField(max_length=255, blank=True)
    def __str__(self): return self.name

class Ownership(models.Model):
    flat = models.ForeignKey(Flat, on_delete=models.CASCADE)
    owner = models.ForeignKey(Owner, on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField(blank=True, null=True)
    class Meta: ordering = ['-start_date']

class Tenancy(models.Model):
    flat = models.ForeignKey(Flat, on_delete=models.CASCADE)
    lessee = models.ForeignKey(Lessee, on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField(blank=True, null=True)
    agreement_file = models.FileField(upload_to=upload_to, blank=True, null=True)
    class Meta: ordering = ['-start_date']
