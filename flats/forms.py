from django import forms
from .models import Flat
from people.models import Ownership, Tenancy

class FlatForm(forms.ModelForm):
    class Meta:
        model = Flat
        fields = ['floor', 'unit', 'status_hint', 'remarks']

_date = forms.DateInput(attrs={"type": "date"})

class OwnershipForm(forms.ModelForm):
    class Meta:
        model = Ownership
        fields = ["owner", "start_date", "end_date"]
        widgets = {"start_date": _date, "end_date": _date}

class TenancyForm(forms.ModelForm):
    class Meta:
        model = Tenancy
        fields = ["lessee", "start_date", "end_date"]
        widgets = {"start_date": _date, "end_date": _date}
