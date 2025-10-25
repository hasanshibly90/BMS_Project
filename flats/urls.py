from django.urls import path
from .views import (
    FlatListView, FlatCreateView, FlatUpdateView, FlatStatusUpdateView,
    FlatOccupancyView, AssignOwnerView, EndOwnerView, AssignLesseeView, EndLesseeView
)

app_name = 'flats'

urlpatterns = [
    path('', FlatListView.as_view(), name='list'),
    path('create/', FlatCreateView.as_view(), name='create'),
    path('<int:pk>/edit/', FlatUpdateView.as_view(), name='edit'),
    path('<int:pk>/status/', FlatStatusUpdateView.as_view(), name='status'),

    # Occupancy editors (by flat)
    path('<int:pk>/occupancy/', FlatOccupancyView.as_view(), name='occupancy'),
    path('<int:pk>/assign-owner/', AssignOwnerView.as_view(), name='assign_owner'),
    path('<int:pk>/end-owner/', EndOwnerView.as_view(), name='end_owner'),
    path('<int:pk>/assign-lessee/', AssignLesseeView.as_view(), name='assign_lessee'),
    path('<int:pk>/end-lessee/', EndLesseeView.as_view(), name='end_lessee'),
]
