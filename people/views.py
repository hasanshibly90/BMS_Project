import re
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.shortcuts import get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.db.models import Q
from django.utils import timezone
from django.contrib import messages
from django.utils.text import slugify
from urllib.parse import quote

from .models import Owner, Lessee, Ownership, Tenancy
from .forms import OwnerForm, LesseeForm

# ───────────────────────── helpers ─────────────────────────

def _safe(txt):
    return (str(txt or "").encode("latin-1", "replace")).decode("latin-1")

def _draw_label_value(c, x, y, label, value, label_w=120):
    c.setFont("Helvetica-Bold", 10); c.drawString(x, y, _safe(label))
    c.setFont("Helvetica", 10); c.drawString(x + label_w, y, _safe(value))

def _try_image(c, path, x, y, w, h):
    try:
        if path:
            c.drawImage(path, x, y, width=w, height=h, preserveAspectRatio=True, anchor='n')
    except Exception:
        pass

def _file_path(instance, attr_name):
    f = getattr(instance, attr_name, None)
    if not f:
        return None
    try:
        if getattr(f, "name", None):
            return f.path
    except (ValueError, FileNotFoundError, OSError):
        return None
    return None

# ───────────────────────── Owners ─────────────────────────

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

class OwnerDeleteView(DeleteView):
    model = Owner
    template_name = "people/owner_confirm_delete.html"
    success_url = reverse_lazy("people:owners")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["ownership_count"] = Ownership.objects.filter(owner=self.object).count()
        return ctx

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        name = self.object.name
        count = Ownership.objects.filter(owner=self.object).count()
        response = super().delete(request, *args, **kwargs)
        messages.success(request, f"Deleted owner '{name}'. Removed {count} ownership record(s).")
        return response

def owner_pdf(request, pk):
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    obj = get_object_or_404(Owner, pk=pk)

    dl = (request.GET.get("dl") or request.GET.get("download") or "").lower()
    disposition = "attachment" if dl in ("1", "true", "yes", "download") else "inline"
    safe_name = slugify(obj.name) or f"owner-{obj.pk}"
    filename = f"{safe_name}.pdf"

    resp = HttpResponse(content_type="application/pdf")
    resp["Content-Disposition"] = f"{disposition}; filename*=UTF-8''{quote(filename)}"

    c = canvas.Canvas(resp, pagesize=A4)
    W, H = A4; margin = 18 * mm; x = margin; y = H - margin
    c.setFont("Helvetica-Bold", 16); c.drawString(x, y, "OWNER PROFILE")
    c.setFont("Helvetica", 9); c.drawRightString(W - margin, y, timezone.now().strftime("%d-%b-%Y %H:%M"))
    y -= 14 * mm

    photo_path = _file_path(obj, "photo")
    nid_path   = _file_path(obj, "nid_image")
    right_w = 38 * mm; right_x = W - margin - right_w
    _try_image(c, photo_path, right_x, y - 40 * mm, right_w, 40 * mm)
    _try_image(c, nid_path,   right_x, y - 88 * mm, right_w, 40 * mm)

    line = 8 * mm
    _draw_label_value(c, x, y, "Name:", obj.name); y -= line
    _draw_label_value(c, x, y, "Phone:", obj.phone); y -= line
    _draw_label_value(c, x, y, "Email:", obj.email); y -= line
    _draw_label_value(c, x, y, "Address:", obj.address); y -= line

    y -= 5 * mm; c.setFont("Helvetica-Bold", 11); c.drawString(x, y, "Ownership history")
    y -= 6 * mm; c.setFont("Helvetica", 10)
    owns = Ownership.objects.filter(owner=obj).order_by("-start_date")
    if not owns:
        c.drawString(x, y, "(no ownership records)"); y -= line
    for o in owns:
        flat = f"{o.flat.unit}-{o.flat.floor:02d}"
        span = f"{o.start_date} to {o.end_date or 'present'}"
        c.drawString(x, y, _safe(f"{flat} | {span}")); y -= line
        if y < margin + 20 * mm:
            c.showPage(); y = H - margin
    c.showPage(); c.save()
    return resp

# ───────────────────────── Lessees ─────────────────────────

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

class LesseeDeleteView(DeleteView):
    model = Lessee
    template_name = "people/lessee_confirm_delete.html"
    success_url = reverse_lazy("people:lessees")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["tenancy_count"] = Tenancy.objects.filter(lessee=self.object).count()
        return ctx

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        name = self.object.name
        count = Tenancy.objects.filter(lessee=self.object).count()
        response = super().delete(request, *args, **kwargs)
        messages.success(request, f"Deleted lessee '{name}'. Removed {count} tenancy record(s).")
        return response

def lessee_pdf(request, pk):
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    obj = get_object_or_404(Lessee, pk=pk)

    dl = (request.GET.get("dl") or request.GET.get("download") or "").lower()
    disposition = "attachment" if dl in ("1", "true", "yes", "download") else "inline"
    safe_name = slugify(obj.name) or f"lessee-{obj.pk}"
    filename = f"{safe_name}.pdf"

    resp = HttpResponse(content_type="application/pdf")
    resp["Content-Disposition"] = f"{disposition}; filename*=UTF-8''{quote(filename)}"

    c = canvas.Canvas(resp, pagesize=A4)
    W, H = A4; margin = 18 * mm; x = margin; y = H - margin
    c.setFont("Helvetica-Bold", 16); c.drawString(x, y, "LESSEE PROFILE")
    c.setFont("Helvetica", 9); c.drawRightString(W - margin, y, timezone.now().strftime("%d-%b-%Y %H:%M"))
    y -= 14 * mm

    photo_path = _file_path(obj, "photo")
    nid_path   = _file_path(obj, "nid_image")
    right_w = 38 * mm; right_x = W - margin - right_w
    _try_image(c, photo_path, right_x, y - 40 * mm, right_w, 40 * mm)
    _try_image(c, nid_path,   right_x, y - 88 * mm, right_w, 40 * mm)

    line = 8 * mm
    _draw_label_value(c, x, y, "Name:", obj.name); y -= line
    _draw_label_value(c, x, y, "Phone:", obj.phone); y -= line
    _draw_label_value(c, x, y, "Email:", obj.email); y -= line
    _draw_label_value(c, x, y, "Address:", obj.address); y -= line

    y -= 5 * mm; c.setFont("Helvetica-Bold", 11); c.drawString(x, y, "Tenancy history")
    y -= 6 * mm; c.setFont("Helvetica", 10)
    tens = Tenancy.objects.filter(lessee=obj).order_by("-start_date")
    if not tens:
        c.drawString(x, y, "(no tenancy records)"); y -= line
    for t in tens:
        flat = f"{t.flat.unit}-{t.flat.floor:02d}"
        span = f"{t.start_date} to {t.end_date or 'present'}"
        c.drawString(x, y, _safe(f"{flat} | {span}")); y -= line
        if y < margin + 20 * mm:
            c.showPage(); y = H - margin
    c.showPage(); c.save()
    return resp

# ───────────────────────── Type-ahead search APIs ─────────────────────────

_FLAT_RE = re.compile(r'^([A-Ha-h])[-_\s]?0?(\d{1,2})$')

def _active_code_for_owners(owner_ids):
    code = {oid: None for oid in owner_ids}
    owns = Ownership.objects.filter(owner_id__in=owner_ids, end_date__isnull=True).select_related("flat")
    for o in owns:
        code[o.owner_id] = f"{o.flat.unit}-{o.flat.floor:02d}"
    return code

def _active_code_for_lessees(lessee_ids):
    code = {lid: None for lid in lessee_ids}
    tens = Tenancy.objects.filter(lessee_id__in=lessee_ids, end_date__isnull=True).select_related("flat")
    for t in tens:
        code[t.lessee_id] = f"{t.flat.unit}-{t.flat.floor:02d}"
    return code

def owners_search(request):
    """Return up to 500 owners (or filtered) with label 'FLAT - Name'."""
    q = (request.GET.get("q") or "").strip()
    base_qs = Owner.objects.all()

    name_qs = base_qs.filter(name__icontains=q) if q else base_qs

    ids_by_flat = []
    m = _FLAT_RE.match(q.replace(" ", "")) if q else None
    if m:
        unit, fl = m.group(1).upper(), int(m.group(2))
        ids_by_flat = list(
            Ownership.objects.filter(end_date__isnull=True, flat__unit=unit, flat__floor=fl)
            .values_list("owner_id", flat=True)
        )

    qs = (name_qs | base_qs.filter(id__in=ids_by_flat)).order_by("name").distinct()[:500]
    id_list = list(qs.values_list("id", flat=True))
    codes = _active_code_for_owners(id_list)
    results = [{"id": o.id, "label": f"{(codes.get(o.id) or '—')} - {o.name}"} for o in qs]
    return JsonResponse({"results": results})

def lessees_search(request):
    """Return up to 500 lessees (or filtered) with label 'FLAT - Name'."""
    q = (request.GET.get("q") or "").strip()
    base_qs = Lessee.objects.all()

    name_qs = base_qs.filter(name__icontains=q) if q else base_qs

    ids_by_flat = []
    m = _FLAT_RE.match(q.replace(" ", "")) if q else None
    if m:
        unit, fl = m.group(1).upper(), int(m.group(2))
        ids_by_flat = list(
            Tenancy.objects.filter(end_date__isnull=True, flat__unit=unit, flat__floor=fl)
            .values_list("lessee_id", flat=True)
        )

    qs = (name_qs | base_qs.filter(id__in=ids_by_flat)).order_by("name").distinct()[:500]
    id_list = list(qs.values_list("id", flat=True))
    codes = _active_code_for_lessees(id_list)
    results = [{"id": l.id, "label": f"{(codes.get(l.id) or '—')} - {l.name}"} for l in qs]
    return JsonResponse({"results": results})
