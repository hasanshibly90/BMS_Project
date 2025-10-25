from django.contrib import admin
from .models import ParkingSpot, ParkingAssignment

@admin.register(ParkingSpot)
class ParkingSpotAdmin(admin.ModelAdmin):
    list_display = ("code", "flat", "location", "assigned_now")
    search_fields = ("code", "flat__unit", "flat__floor", "location")

    def assigned_now(self, obj):
        return bool(obj.active_assignment())
    assigned_now.boolean = True
    assigned_now.short_description = "Assigned"

@admin.register(ParkingAssignment)
class ParkingAssignmentAdmin(admin.ModelAdmin):
    list_display = ("spot", "start_date", "end_date", "vehicle_no", "note")
    list_filter = ("start_date", "end_date")
    search_fields = ("spot__code", "vehicle_no", "note")
