from django import forms
from .models import ServiceProvider, ServiceCategory

class ServiceProviderForm(forms.ModelForm):
    class Meta:
        model = ServiceProvider
        fields = [
            "category", "full_name", "phone", "email", "address",
            "nid_number", "experience_years", "notes", "photo",
        ]
        widgets = {
            "notes": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only active categories in the dropdown
        self.fields["category"].queryset = ServiceCategory.objects.filter(is_active=True).order_by("name")
