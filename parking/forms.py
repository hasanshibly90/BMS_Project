from django import forms
from .models import ParkingAssignment

_date = forms.DateInput(attrs={"type": "date"})

class ParkingAssignmentForm(forms.ModelForm):
    class Meta:
        model = ParkingAssignment
        fields = ["spot", "start_date", "end_date", "vehicle_no", "note"]
        widgets = {"start_date": _date, "end_date": _date}

class ParkingAssignmentQuickForm(forms.ModelForm):
    class Meta:
        model = ParkingAssignment
        fields = ["start_date", "end_date", "vehicle_no", "note"]
        widgets = {"start_date": _date, "end_date": _date}
