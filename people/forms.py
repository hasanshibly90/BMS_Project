from django import forms
from .models import Owner, Lessee, Ownership, Tenancy

class OwnerForm(forms.ModelForm):
    class Meta:
        model = Owner
        fields = ["name", "phone", "email", "photo", "nid_image", "address"]

class LesseeForm(forms.ModelForm):
    class Meta:
        model = Lessee
        fields = ["name", "phone", "email", "photo", "nid_image", "address"]

_date = forms.DateInput(attrs={"type": "date"})

class OwnershipForm(forms.ModelForm):
    # Extra fields to also assign parking in the same submit
    assign_parking = forms.BooleanField(required=False, label="Also assign parking")
    vehicle_no = forms.CharField(required=False, label="Vehicle no")
    parking_note = forms.CharField(required=False, label="Parking note")

    class Meta:
        model = Ownership
        fields = ["owner", "start_date", "end_date"]
        widgets = {"start_date": _date, "end_date": _date}

class TenancyForm(forms.ModelForm):
    assign_parking = forms.BooleanField(required=False, label="Also assign parking")
    vehicle_no = forms.CharField(required=False, label="Vehicle no")
    parking_note = forms.CharField(required=False, label="Parking note")

    class Meta:
        model = Tenancy
        fields = ["lessee", "start_date", "end_date"]
        widgets = {"start_date": _date, "end_date": _date}
