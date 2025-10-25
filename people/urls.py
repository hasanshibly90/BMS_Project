from django.urls import path
from .views import (
    OwnerListView, OwnerCreateView, OwnerUpdateView, owner_pdf,
    LesseeListView, LesseeCreateView, LesseeUpdateView, lessee_pdf,
)

app_name = "people"

urlpatterns = [
    path("owners/", OwnerListView.as_view(), name="owners"),
    path("owners/create/", OwnerCreateView.as_view(), name="owner_create"),
    path("owners/<int:pk>/edit/", OwnerUpdateView.as_view(), name="owner_edit"),
    path("owners/<int:pk>/pdf/", owner_pdf, name="owner_pdf"),
    path("lessees/", LesseeListView.as_view(), name="lessees"),
    path("lessees/create/", LesseeCreateView.as_view(), name="lessee_create"),
    path("lessees/<int:pk>/edit/", LesseeUpdateView.as_view(), name="lessee_edit"),
    path("lessees/<int:pk>/pdf/", lessee_pdf, name="lessee_pdf"),
]
