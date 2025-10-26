from django.contrib import admin
from .models import Vehicle, ExternalOwner, ParkingSpot, ParkingAssignment


@admin.register(ParkingSpot)
class ParkingSpotAdmin(admin.ModelAdmin):
    list_display = ("code", "level", "is_reserved")
    search_fields = ("code",)
    list_filter = ("is_reserved", "level")


@admin.register(ExternalOwner)
class ExternalOwnerAdmin(admin.ModelAdmin):
    list_display = ("name", "kind", "phone", "company")
    list_filter = ("kind",)
    search_fields = ("name", "phone", "company")


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ("plate_no", "vehicle_type", "owner_type", "owner", "lessee", "external_owner", "flat", "is_active")
    list_filter = ("vehicle_type", "owner_type", "is_active")
    search_fields = ("plate_no", "make", "model", "tag_no", "owner__name", "lessee__name", "external_owner__name")


@admin.register(ParkingAssignment)
class ParkingAssignmentAdmin(admin.ModelAdmin):
    list_display = ("vehicle", "spot", "start_date", "end_date")
    list_filter = ("spot", "start_date", "end_date")
    search_fields = ("vehicle__plate_no", "spot__code")
