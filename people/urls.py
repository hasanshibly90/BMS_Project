from django.urls import path
from .views import (
    # HTML views
    OwnerListView, OwnerCreateView, OwnerUpdateView, OwnerDeleteView, owner_pdf,
    LesseeListView, LesseeCreateView, LesseeUpdateView, LesseeDeleteView, lessee_pdf,
    # APIs used by Occupancy type-ahead
    owners_search, lessees_search,
)

app_name = "people"

urlpatterns = [
    # Owners
    path("owners/",                 OwnerListView.as_view(),   name="owners"),
    path("owners/create/",          OwnerCreateView.as_view(), name="owner_create"),
    path("owners/<int:pk>/edit/",   OwnerUpdateView.as_view(), name="owner_edit"),
    path("owners/<int:pk>/delete/", OwnerDeleteView.as_view(), name="owner_delete"),
    path("owners/<int:pk>/pdf/",    owner_pdf,                 name="owner_pdf"),

    # Lessees
    path("lessees/",                 LesseeListView.as_view(),   name="lessees"),
    path("lessees/create/",          LesseeCreateView.as_view(), name="lessee_create"),
    path("lessees/<int:pk>/edit/",   LesseeUpdateView.as_view(), name="lessee_edit"),
    path("lessees/<int:pk>/delete/", LesseeDeleteView.as_view(), name="lessee_delete"),
    path("lessees/<int:pk>/pdf/",    lessee_pdf,                 name="lessee_pdf"),

    # Type-ahead APIs
    path("api/owners",  owners_search,  name="owners_search"),
    path("api/lessees", lessees_search, name="lessees_search"),
]
