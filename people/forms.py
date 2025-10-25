from django import forms
from django.db.models import Prefetch
from .models import Owner, Lessee, Ownership, Tenancy

# ---- existing simple forms (unchanged) ----
class OwnerForm(forms.ModelForm):
    class Meta:
        model = Owner
        fields = ["name", "phone", "email", "photo", "nid_image", "address"]

class LesseeForm(forms.ModelForm):
    class Meta:
        model = Lessee
        fields = ["name", "phone", "email", "photo", "nid_image", "address"]

# date widget for both assignment forms
_date = forms.DateInput(attrs={"type": "date"})

# ---- enhanced assignment forms with custom labels ----
class OwnershipForm(forms.ModelForm):
    # we override queryset/labels in __init__
    owner = forms.ModelChoiceField(queryset=Owner.objects.none(), label="Owner")

    class Meta:
        model = Ownership
        fields = ["owner", "start_date", "end_date"]
        widgets = {"start_date": _date, "end_date": _date}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Prefetch active ownership (if any) for each owner to get current flat quickly
        qs = (
            Owner.objects.all()
            .order_by("name")
            .prefetch_related(
                Prefetch(
                    "ownerships",
                    queryset=Ownership.objects.filter(end_date__isnull=True).select_related("flat"),
                    to_attr="active_owns",
                )
            )
        )
        self.fields["owner"].queryset = qs

        def label_from_owner(o: Owner):
            code = "—"
            if hasattr(o, "active_owns") and o.active_owns:
                own = o.active_owns[0]
                if own.flat:
                    code = f"{own.flat.unit}-{own.flat.floor:02d}"
            return f"{code} - {o.name}"  # e.g., "E-10 - Ashikur Rahman"

        self.fields["owner"].label_from_instance = label_from_owner


class TenancyForm(forms.ModelForm):
    lessee = forms.ModelChoiceField(queryset=Lessee.objects.none(), label="Lessee")

    class Meta:
        model = Tenancy
        fields = ["lessee", "start_date", "end_date"]
        widgets = {"start_date": _date, "end_date": _date}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        qs = (
            Lessee.objects.all()
            .order_by("name")
            .prefetch_related(
                Prefetch(
                    "tenancies",
                    queryset=Tenancy.objects.filter(end_date__isnull=True).select_related("flat"),
                    to_attr="active_tens",
                )
            )
        )
        self.fields["lessee"].queryset = qs

        def label_from_lessee(l: Lessee):
            code = "—"
            if hasattr(l, "active_tens") and l.active_tens:
                t = l.active_tens[0]
                if t.flat:
                    code = f"{t.flat.unit}-{t.flat.floor:02d}"
            return f"{code} - {l.name}"  # e.g., "E-10 - John Tenant"

        self.fields["lessee"].label_from_instance = label_from_lessee
