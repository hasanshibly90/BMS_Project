from django import forms

class BulkOwnersForm(forms.Form):
    data = forms.CharField(
        label="Paste data",
        widget=forms.Textarea(attrs={
            "rows": 14,
            "placeholder": "Flat no, Owner, Cell\nA-01, John Doe, 01711123456"
        })
    )
    start_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={"type": "date"}),
        help_text="If empty, today will be used."
    )
    vacate_missing = forms.BooleanField(
        required=False,
        initial=False,
        help_text="Flats not present in the pasted data will be marked Vacant."
    )
    dry_run = forms.BooleanField(
        label="Preview only (no changes)",
        required=False,
        initial=True
    )
