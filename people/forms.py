from django import forms
from .models import Owner, Lessee

class OwnerForm(forms.ModelForm):
    class Meta:
        model = Owner
        fields = ["name", "phone", "email", "photo", "nid_image", "address"]

class LesseeForm(forms.ModelForm):
    class Meta:
        model = Lessee
        fields = ["name", "phone", "email", "photo", "nid_image", "address"]
