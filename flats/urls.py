from django.urls import path
from .views import FlatListView, FlatCreateView, FlatUpdateView, FlatStatusUpdateView

app_name = 'flats'

urlpatterns = [
    path('', FlatListView.as_view(), name='list'),
    path('create/', FlatCreateView.as_view(), name='create'),
    path('<int:pk>/edit/', FlatUpdateView.as_view(), name='edit'),
    path('<int:pk>/status/', FlatStatusUpdateView.as_view(), name='status'),
]
