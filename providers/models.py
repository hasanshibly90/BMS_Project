from django.db import models

class ServiceCategory(models.Model):
    name = models.CharField(max_length=80, unique=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Service Category"
        verbose_name_plural = "Service Categories"

    def __str__(self):
        return self.name


class ServiceProvider(models.Model):
    category = models.ForeignKey(ServiceCategory, on_delete=models.PROTECT, related_name="providers")
    full_name = models.CharField(max_length=120)
    phone = models.CharField(max_length=40, blank=True)
    email = models.EmailField(blank=True)
    address = models.CharField(max_length=255, blank=True)

    nid_number = models.CharField("NID / ID Number", max_length=50, blank=True)
    experience_years = models.PositiveIntegerField(blank=True, null=True)
    notes = models.TextField(blank=True)

    photo = models.ImageField(upload_to="docs/service_provider/", blank=True, null=True)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["full_name"]

    def __str__(self):
        return f"{self.full_name} ({self.category.name})"
