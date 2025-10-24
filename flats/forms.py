from django import forms
from .models import Flat

class FlatForm(forms.ModelForm):
    class Meta:
        model = Flat
        fields = ['floor', 'unit', 'status_hint', 'remarks']
