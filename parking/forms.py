from django import forms
from django.utils import timezone

from people.models import Owner, Lessee
from .models import Vehicle, ExternalOwner, ParkingSpot, ParkingAssignment

_date = forms.DateInput(attrs={"type": "date"})

class VehicleForm(forms.ModelForm):
    owner_type = forms.ChoiceField(choices=Vehicle.OWNER_TYPES, label="Vehicle belongs to")
    owner = forms.ModelChoiceField(queryset=Owner.objects.all().order_by("name"), required=False)
    lessee = forms.ModelChoiceField(queryset=Lessee.objects.all().order_by("name"), required=False)
    external_owner = forms.ModelChoiceField(queryset=ExternalOwner.objects.all().order_by("name"), required=False, label="External (Uber/Rental)")

    assign_parking = forms.BooleanField(required=False, initial=False, label="Assign parking now?")
    spot = forms.ModelChoiceField(queryset=ParkingSpot.objects.all().order_by("code"), required=False)
    start_date = forms.DateField(required=False, widget=_date, initial=timezone.localdate())

    class Meta:
        model = Vehicle
        fields = ["plate_no","vehicle_type","make","model","color","tag_no","owner_type","owner","lessee","external_owner","flat","is_active","notes"]

    def clean(self):
        cleaned = super().clean()
        ot = cleaned.get("owner_type")
        if ot == Vehicle.OWNER and not cleaned.get("owner"):
            self.add_error("owner", "Select an Owner.")
        if ot == Vehicle.LESSEE and not cleaned.get("lessee"):
            self.add_error("lessee", "Select a Lessee.")
        if ot in (Vehicle.UBER_DRIVER, Vehicle.RENTAL_COMPANY) and not cleaned.get("external_owner"):
            self.add_error("external_owner", "Select or create an External owner.")
        if cleaned.get("assign_parking"):
            if not cleaned.get("spot"): self.add_error("spot", "Choose a parking spot.")
            if not cleaned.get("start_date"): self.add_error("start_date", "Provide a start date.")
        return cleaned
