from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from django.db.models import Q
from django.conf import settings

from .models import Owner, Lessee, Ownership, Tenancy
from .forms import OwnerForm, LesseeForm

# --- Helpers -----------------------------------------------------------------

def _safe(txt):
    # ReportLab default fonts are Latin-1; prevent crashes on non-latin text.
    # This keeps ASCII and replaces other glyphs with '?'. You can later
    # register a Unicode TTF if you want full Bangla support.
    return (str(txt or "").encode("latin-1", "replace")).decode("latin-1")

def _draw_label_value(c, x, y, label, value, label_w=120):
    c.setFont("Helvetica-Bold", 10)
    c.drawString(x, y, _safe(label))
    c.setFont("Helvetica", 10)
    c.drawString(x + label_w, y, _safe(value))

def _try_image(c, path, x, y, w, h):
    try:
        if path:
            c.drawImage(path, x, y, width=w, height=h, preserveAspectRatio=True, anchor='n')
    except Exception:
        pass

# --- Owners ------------------------------------------------------------------

class OwnerListView(ListView):
    model = Owner
    template_name = "people/owner_list.html"
    paginate_by = 30

    def get_queryset(self):
        qs = Owner.objects.all().order_by("name")
        q = (self.request.GET.get("q") or "").strip()
        if q:
            qs = qs.filter(Q(name__icontains=q) | Q(phone__icontains=q) | Q(email__icontains=q))
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["q"] = (self.request.GET.get("q") or "").strip()
        return ctx

class OwnerCreateView(CreateView):
    model = Owner
    form_class = OwnerForm
    template_name = "form.html"
    success_url = reverse_lazy("people:owners")

class OwnerUpdateView(UpdateView):
    model = Owner
    form_class = OwnerForm
    template_name = "form.html"
    success_url = reverse_lazy("people:owners")

def owner_pdf(request, pk):
    """Generate a clean A4 profile PDF for an Owner (with photo and NID image)."""
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from django.utils import timezone
    import os

    obj = get_object_or_404(Owner, pk=pk)

    resp = HttpResponse(content_type="application/pdf")
    resp["Content-Disposition"] = f'inline; filename="Owner_{obj.pk}.pdf"'

    c = canvas.Canvas(resp, pagesize=A4)
    W, H = A4
    margin = 18 * mm
    x = margin
    y = H - margin

    # Header
    c.setFont("Helvetica-Bold", 16)
    c.drawString(x, y, "OWNER PROFILE")
    c.setFont("Helvetica", 9)
    c.drawRightString(W - margin, y, timezone.now().strftime("%d-%b-%Y %H:%M"))
    y -= 14 * mm

    # Photo (top-right) and NID (below)
    photo_path = None
    nid_path = None
    try:
        if obj.photo and obj.photo.name:
            photo_path = obj.photo.path
    except Exception:
        pass
    try:
        if obj.nid_image and obj.nid_image.name:
            nid_path = obj.nid_image.path
    except Exception:
        pass

    # Reserve right column for images
    right_w = 38 * mm
    right_x = W - margin - right_w
    _try_image(c, photo_path, right_x, y - 40 * mm, right_w, 40 * mm)
    _try_image(c, nid_path, right_x, y - 88 * mm, right_w, 40 * mm)

    # Left column fields
    line = 8 * mm
    _draw_label_value(c, x, y, "Name:", obj.name); y -= line
    _draw_label_value(c, x, y, "Phone:", obj.phone); y -= line
    _draw_label_value(c, x, y, "Email:", obj.email); y -= line
    _draw_label_value(c, x, y, "Address:", obj.address); y -= line

    # Ownerships (current first)
    y -= 5 * mm
    c.setFont("Helvetica-Bold", 11)
    c.drawString(x, y, "Ownership history")
    y -= 6 * mm

    c.setFont("Helvetica", 10)
    owns = Ownership.objects.filter(owner=obj).order_by("-start_date")
    if not owns:
        c.drawString(x, y, "(no ownership records)"); y -= line
    for o in owns:
        flat = f"{o.flat.unit}-{o.flat.floor:02d}"
        span = f"{o.start_date} to {o.end_date or 'present'}"
        c.drawString(x, y, _safe(f"{flat}  |  {span}"))
        y -= line
        if y < margin + 20 * mm:
            c.showPage(); y = H - margin

    c.showPage()
    c.save()
    return resp

# --- Lessees -----------------------------------------------------------------

class LesseeListView(ListView):
    model = Lessee
    template_name = "people/lessee_list.html"
    paginate_by = 30

    def get_queryset(self):
        qs = Lessee.objects.all().order_by("name")
        q = (self.request.GET.get("q") or "").strip()
        if q:
            qs = qs.filter(Q(name__icontains=q) | Q(phone__icontains=q) | Q(email__icontains=q))
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["q"] = (self.request.GET.get("q") or "").strip()
        return ctx

class LesseeCreateView(CreateView):
    model = Lessee
    form_class = LesseeForm
    template_name = "form.html"
    success_url = reverse_lazy("people:lessees")

class LesseeUpdateView(UpdateView):
    model = Lessee
    form_class = LesseeForm
    template_name = "form.html"
    success_url = reverse_lazy("people:lessees")

def lessee_pdf(request, pk):
    """Generate a clean A4 profile PDF for a Lessee (with photo and NID image)."""
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from django.utils import timezone

    obj = get_object_or_404(Lessee, pk=pk)

    resp = HttpResponse(content_type="application/pdf")
    resp["Content-Disposition"] = f'inline; filename="Lessee_{obj.pk}.pdf"'

    c = canvas.Canvas(resp, pagesize=A4)
    W, H = A4
    margin = 18 * mm
    x = margin
    y = H - margin

    # Header
    c.setFont("Helvetica-Bold", 16)
    c.drawString(x, y, "LESSEE PROFILE")
    c.setFont("Helvetica", 9)
    c.drawRightString(W - margin, y, timezone.now().strftime("%d-%b-%Y %H:%M"))
    y -= 14 * mm

    # Images
    photo_path = None
    nid_path = None
    try:
        if obj.photo and obj.photo.name:
            photo_path = obj.photo.path
    except Exception:
        pass
    try:
        if obj.nid_image and obj.nid_image.name:
            nid_path = obj.nid_image.path
    except Exception:
        pass

    right_w = 38 * mm
    right_x = W - margin - right_w
    _try_image(c, photo_path, right_x, y - 40 * mm, right_w, 40 * mm)
    _try_image(c, nid_path, right_x, y - 88 * mm, right_w, 40 * mm)

    # Fields
    line = 8 * mm
    _draw_label_value(c, x, y, "Name:", obj.name); y -= line
    _draw_label_value(c, x, y, "Phone:", obj.phone); y -= line
    _draw_label_value(c, x, y, "Email:", obj.email); y -= line
    _draw_label_value(c, x, y, "Address:", obj.address); y -= line

    # Tenancy history
    y -= 5 * mm
    c.setFont("Helvetica-Bold", 11)
    c.drawString(x, y, "Tenancy history")
    y -= 6 * mm

    c.setFont("Helvetica", 10)
    tens = Tenancy.objects.filter(lessee=obj).order_by("-start_date")
    if not tens:
        c.drawString(x, y, "(no tenancy records)"); y -= line
    for t in tens:
        flat = f"{t.flat.unit}-{t.flat.floor:02d}"
        span = f"{t.start_date} to {t.end_date or 'present'}"
        c.drawString(x, y, _safe(f"{flat}  |  {span}"))
        y -= line
        if y < margin + 20 * mm:
            c.showPage(); y = H - margin

    c.showPage()
    c.save()
    return resp
