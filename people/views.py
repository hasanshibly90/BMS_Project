import re
from urllib.parse import quote

from django.contrib import messages
from django.db.models import Q
from django.http import JsonResponse, HttpResponse, HttpRequest
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.text import slugify
from django.views.generic import ListView, CreateView, UpdateView, DeleteView

from .models import Owner, Lessee, Ownership, Tenancy
from .forms import OwnerForm, LesseeForm

# ───────────────── helpers ─────────────────

def _safe(txt) -> str:
    return (str(txt or "")).encode("latin-1", "replace").decode("latin-1")

def _file_path(instance, attr_name: str):
    f = getattr(instance, attr_name, None)
    if not f:
        return None
    try:
        if getattr(f, "name", None):
            return f.path
    except Exception:
        return None
    return None

# ───────────────── Owner pages ─────────────────

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
        nm = self.object.name
        cnt = Ownership.objects.filter(owner=self.object).count()
        resp = super().delete(request, *args, **kwargs)
        messages.success(request, f"Deleted owner '{nm}'. Removed {cnt} ownership record(s).")
        return resp

def owner_pdf(request: HttpRequest, pk: int) -> HttpResponse:
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm

    obj = get_object_or_404(Owner, pk=pk)

    dl = (request.GET.get("dl") or request.GET.get("download") or "").lower()
    disp = "attachment" if dl in ("1", "true", "yes", "download") else "inline"
    fname = f"{slugify(obj.name) or f'owner-{obj.pk}'}.pdf"

    resp = HttpResponse(content_type="application/pdf")
    resp["Content-Disposition"] = f"{disp}; filename*=UTF-8''{quote(fname)}"

    c = canvas.Canvas(resp, pagesize=A4)
    W, H = A4
    margin = 18 * mm
    x = margin
    y = H - margin

    c.setFont("Helvetica-Bold", 16); c.drawString(x, y, "OWNER PROFILE")
    c.setFont("Helvetica", 9); c.drawRightString(W - margin, y, timezone.now().strftime("%d-%b-%Y %H:%M"))
    y -= 14 * mm

    photo_path = _file_path(obj, "photo")
    nid_path   = _file_path(obj, "nid_image")
    right_w = 38 * mm; right_x = W - margin - right_w
    if photo_path: c.drawImage(photo_path, right_x, y - 40 * mm, width=right_w, height=40 * mm, preserveAspectRatio=True)
    if nid_path:   c.drawImage(nid_path,   right_x, y - 88 * mm, width=right_w, height=40 * mm, preserveAspectRatio=True)

    line = 8 * mm
    c.setFont("Helvetica-Bold", 11); c.drawString(x, y, "Details"); y -= 6 * mm; c.setFont("Helvetica", 10)
    c.drawString(x, y, _safe(f"Name: {obj.name}")); y -= line
    c.drawString(x, y, _safe(f"Phone: {obj.phone}")); y -= line
    c.drawString(x, y, _safe(f"Email: {obj.email}")); y -= line
    c.drawString(x, y, _safe(f"Address: {obj.address}")); y -= line

    y -= 6 * mm; c.setFont("Helvetica-Bold", 11); c.drawString(x, y, "Ownership history"); y -= 6 * mm; c.setFont("Helvetica", 10)
    rows = Ownership.objects.filter(owner=obj).select_related("flat").order_by("-start_date")
    if not rows:
        c.drawString(x, y, "(no ownership records)")
    for o in rows:
        c.drawString(x, y, _safe(f"{o.flat} | {o.start_date} → {o.end_date or 'present'}")); y -= line
        if y < margin + 20 * mm: c.showPage(); y = H - margin; c.setFont("Helvetica", 10)

    c.showPage(); c.save()
    return resp

# ─────────────── Lessee pages ───────────────

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
        nm = self.object.name
        cnt = Tenancy.objects.filter(lessee=self.object).count()
        resp = super().delete(request, *args, **kwargs)
        messages.success(request, f"Deleted lessee '{nm}'. Removed {cnt} tenancy record(s).")
        return resp

def lessee_pdf(request: HttpRequest, pk: int) -> HttpResponse:
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm

    obj = get_object_or_404(Lessee, pk=pk)

    dl = (request.GET.get("dl") or request.GET.get("download") or "").lower()
    disp = "attachment" if dl in ("1", "true", "yes", "download") else "inline"
    fname = f"{slugify(obj.name) or f'lessee-{obj.pk}'}.pdf"

    resp = HttpResponse(content_type="application/pdf")
    resp["Content-Disposition"] = f"{disp}; filename*=UTF-8''{quote(fname)}"

    c = canvas.Canvas(resp, pagesize=A4)
    W, H = A4; margin = 18 * mm; x = margin; y = H - margin

    c.setFont("Helvetica-Bold", 16); c.drawString(x, y, "LESSEE PROFILE")
    c.setFont("Helvetica", 9); c.drawRightString(W - margin, y, timezone.now().strftime("%d-%b-%Y %H:%M"))
    y -= 14 * mm

    photo_path = _file_path(obj, "photo")
    nid_path   = _file_path(obj, "nid_image")
    right_w = 38 * mm; right_x = W - margin - right_w
    if photo_path: c.drawImage(photo_path, right_x, y - 40 * mm, width=right_w, height=40 * mm, preserveAspectRatio=True)
    if nid_path:   c.drawImage(nid_path,   right_x, y - 88 * mm, width=right_w, height=40 * mm, preserveAspectRatio=True)

    line = 8 * mm
    _draw_label_value(c, x, y, "Name:", obj.name); y -= line
    _draw_label_value(c, x, y, "Phone:", obj.phone); y -= line
    _draw_label_value(c, x, y, "Email:", obj.email); y -= line
    _draw_label_value(c, x, y, "Address:", obj.address); y -= line

    y -= 6 * mm; c.setFont("Helvetica-Bold", 11); c.drawString(x, y, "Tenancy history"); y -= 6 * mm; c.setFont("Helvetica", 10)
    rows = Tenancy.objects.filter(lessee=obj).select_related("flat").order_by("-start_date")
    if not rows:
        c.drawString(x, y, "(no tenancy records)")
    for t in rows:
        c.drawString(x, y, _safe(f"{t.flat} | {t.start_date} → {t.end_date or 'present'}")); y -= line
        if y < margin + 20 * mm: c.showPage(); y = H - margin; c.setFont("Helvetica", 10)

    c.showPage(); c.save()
    return resp

# ─────────────── Search APIs (type-ahead) ───────────────

_FLAT_RE = re.compile(r"^([A-Ha-h])[-_\s]?0?(\d{1,2})$")

def _active_code_for_owners(owner_ids):
    code = {oid: None for oid in owner_ids}
    qs = Ownership.objects.filter(owner_id__in=owner_ids, end_date__isnull=True).select_related("flat")
    for row in qs:
        code[row.owner_id] = f"{row.flat.unit}-{row.flat.floor:02d}"
    return code

def _active_code_for_lessees(lessee_ids):
    code = {lid: None for lid in lessee_ids}
    qs = Tenancy.objects.filter(lessee_id__in=lessee_ids, end_date__isnull=True).select_related("flat")
    for row in qs:
        code[row.lessee_id] = f"{row.flat.unit}-{row.flat.floor:02d}"
    return code

def owners_search(request: HttpRequest) -> JsonResponse:
    q = (request.GET.get("q") or "").strip()
    base = Owner.objects.all()
    if not q:
        qs = base.order_by("name")[:500]
    else:
        name_qs = base.filter(Q(name__icontains=q) | Q(phone__icontains=q))
        ids_by_flat = []
        m = _FLAT_RE.match(q.replace(" ", ""))
        if m:
            u, f = m.group(1).upper(), int(m.group(2))
            ids_by_flat = list(
                Ownership.objects.filter(end_date__isnull=True, flat__unit=u, flat__floor=f)
                .values_list("owner_id", flat=True)
            )
        qs = (name_qs | base.filter(id__in=ids_by_flat)).order_by("name").distinct()
        if not qs.exists():
            qs = base.order_by("name")
    ids = list(qs.values_list("id", flat=True))
    codes = _active_code_for_owners(ids)
    data = [{"id": oid, "label": f"{(codes.get(oid) or '—')} - {name}"} for oid, name in qs.values_list("id", "name")[:500]]
    return JsonResponse({"results": data})

def lessees_search(request: HttpRequest) -> JsonResponse:
    q = (request.GET.get("q") or "").strip()
    base = Lessee.objects.all()
    if not q:
        qs = base.order_by("name")[:500]
    else:
        name_qs = base.filter(Q(name__icontains=q) | Q(phone__icontains=q))
        ids_by_flat = []
        m = _FLAT_RE.match(q.replace(" ", ""))
        if m:
            u, f = m.group(1).upper(), int(m.group(2))
            ids_by_flat = list(
                Tenancy.objects.filter(end_date__isnull=True, flat__unit=u, flat__floor=f)
                .values_list("lessee_id", flat=True)
            )
        qs = (name_qs | base.filter(id__in=ids_by_flat)).order_by("name").distinct()
        if not qs.exists():
            qs = base.order_by("name")
    ids = list(qs.values_list("id", flat=True))
    codes = _active_code_for_lessees(ids)
    data = [{"id": lid, "label": f"{(codes.get(lid) or '—')} - {name}"} for lid, name in qs.values_list("id", "name")[:500]]
    return JsonResponse({"results": data})
