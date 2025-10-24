from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, View
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Count, Q

from .models import Flat
from .forms import FlatForm


class FlatListView(ListView):
    model = Flat
    template_name = 'flats/flat_list.html'
    paginate_by = 40

    def get_queryset(self):
        qs = Flat.objects.all().order_by('floor', 'unit')

        q = (self.request.GET.get('q') or '').strip()
        status = (self.request.GET.get('status') or '').strip()
        floor = (self.request.GET.get('floor') or '').strip()

        if q:
            # numeric -> filter by floor, else try unit/remarks
            if q.isdigit():
                qs = qs.filter(floor=int(q))
            else:
                qs = qs.filter(Q(unit__iexact=q) | Q(remarks__icontains=q))

        if status in dict(Flat.STATUS_CHOICES):
            qs = qs.filter(status_hint=status)

        if floor.isdigit():
            qs = qs.filter(floor=int(floor))

        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        # filters
        ctx['q'] = (self.request.GET.get('q') or '').strip()
        ctx['status'] = (self.request.GET.get('status') or '').strip()
        ctx['floor'] = (self.request.GET.get('floor') or '').strip()

        # counts
        counts = dict(
            Flat.objects.values_list('status_hint')
            .annotate(c=Count('id'))
            .values_list('status_hint', 'c')
        )
        ctx['cnt_owner'] = counts.get('owner', 0)
        ctx['cnt_rented'] = counts.get('rented', 0)
        ctx['cnt_vacant'] = counts.get('vacant', 0)

        # for selects
        ctx['floors'] = list(range(1, 15))
        ctx['status_choices'] = Flat.STATUS_CHOICES
        return ctx


class FlatCreateView(CreateView):
    model = Flat
    form_class = FlatForm
    template_name = 'form.html'
    success_url = reverse_lazy('flats:list')


class FlatUpdateView(UpdateView):
    model = Flat
    form_class = FlatForm
    template_name = 'form.html'
    success_url = reverse_lazy('flats:list')


class FlatStatusUpdateView(View):
    """Inline status change from the list page."""
    def post(self, request, pk):
        obj = get_object_or_404(Flat, pk=pk)
        new_status = (request.POST.get('status_hint') or '').strip()
        valid = dict(Flat.STATUS_CHOICES).keys()
        if new_status in valid:
            obj.status_hint = new_status
            obj.save(update_fields=['status_hint'])
            messages.success(request, f'Status updated for {obj}.')
        else:
            messages.error(request, 'Invalid status.')
        return redirect(request.META.get('HTTP_REFERER') or reverse_lazy('flats:list'))
