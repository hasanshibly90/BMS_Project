import re
from django.contrib import messages
from django.db.models import Q, Count
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.generic import ListView, DetailView, View

from .models import ParkingSpot, ParkingAssignment
from .forms import ParkingAssignmentForm, ParkingAssignmentQuickForm


class SpotListView(ListView):
    model = ParkingSpot
    template_name = "parking/spot_list.html"
    paginate_by = 40

    def get_queryset(self):
        qs = ParkingSpot.objects.select_related("flat").all().order_by("flat__floor", "flat__unit")
        q = (self.request.GET.get("q") or "").strip()
        status = (self.request.GET.get("status") or "").strip()  # assigned / unassigned

        if q:
            s = re.sub(r"\s+", "", q).upper()
            m = re.match(r"^([A-H])[-_]?0?(\d{1,2})$", s)
            if m:
                unit, fl = m.group(1), int(m.group(2))
                qs = qs.filter(flat__unit__iexact=unit, flat__floor=fl)
            elif s.isdigit():
                qs = qs.filter(flat__floor=int(s))
            elif len(s) == 1 and s in "ABCDEFGH":
                qs = qs.filter(flat__unit__iexact=s)
            else:
                qs = qs.filter(Q(code__icontains=q) | Q(location__icontains=q))

        if status == "assigned":
            qs = qs.filter(assignments__end_date__isnull=True).distinct()
        elif status == "unassigned":
            qs = qs.exclude(assignments__end_date__isnull=True)

        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["q"] = (self.request.GET.get("q") or "").strip()
        ctx["status"] = (self.request.GET.get("status") or "").strip()
        ctx["cnt_assigned"] = ParkingAssignment.objects.filter(end_date__isnull=True).count()
        ctx["cnt_total"] = ParkingSpot.objects.count()
        ctx["cnt_unassigned"] = ctx["cnt_total"] - ctx["cnt_assigned"]
        return ctx


class SpotDetailView(DetailView):
    model = ParkingSpot
    template_name = "parking/spot_detail.html"
    context_object_name = "spot"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        spot = self.object
        ctx["active"] = spot.active_assignment()
        ctx["history"] = spot.assignments.all()
        ctx["form"] = ParkingAssignmentQuickForm()
        return ctx


class AssignParkingView(View):
    """
    Assign this spot to a new usage (vehicle_no/note optional).
    Ends current active assignment at new start_date if overlapping.
    """
    def post(self, request, pk):
        spot = get_object_or_404(ParkingSpot, pk=pk)
        form = ParkingAssignmentQuickForm(request.POST)
        if form.is_valid():
            start = form.cleaned_data["start_date"]
            end = form.cleaned_data.get("end_date")
            vehicle_no = form.cleaned_data.get("vehicle_no", "")
            note = form.cleaned_data.get("note", "")

            current = spot.active_assignment()
            if current and current.start_date <= start and current.end_date is None:
                current.end_date = start
                current.save(update_fields=["end_date"])

            ParkingAssignment.objects.create(
                spot=spot, start_date=start, end_date=end, vehicle_no=vehicle_no, note=note
            )
            messages.success(request, f"Assigned parking {spot.code}.")
        else:
            messages.error(request, "Invalid parking assignment.")
        return redirect(reverse("parking:spot_detail", args=[spot.pk]))


class EndParkingView(View):
    """
    End the current active assignment for this spot now (today).
    """
    def post(self, request, pk):
        spot = get_object_or_404(ParkingSpot, pk=pk)
        current = spot.active_assignment()
        if current:
            current.end_date = timezone.localdate()
            current.save(update_fields=["end_date"])
            messages.success(request, f"Ended parking assignment for {spot.code}.")
        else:
            messages.info(request, "No active parking assignment to end.")
        return redirect(reverse("parking:spot_detail", args=[spot.pk]))
