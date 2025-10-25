# people/urls.py
from django.urls import path
from .views import (
    # HTML views
    OwnerListView, OwnerCreateView, OwnerUpdateView, OwnerDeleteView, owner_pdf,
    LesseeListView, LesseeCreateView, LesseeUpdateView, LesseeDeleteView, lessee_pdf,
    # Type-ahead APIs for Occupancy page
    owners_list as owners_search,   # alias only if you kept a different name; otherwise import owners_search directly
    lessees_search,
)

# If your views module already defines owners_search, use:
# from .views import owners_search, lessees_search
# and remove the alias line above.

app_name = "people"

urlpatterns = [
    # Owners
    path("owners/",                 OwnerListView.provide_as_view() if hasattr(OwnerListView, "provide_as_view") else OwnerListView.as_view(), name="owners"),  # noqa
    path("owners/",                 OwnerListView.as_view(),                        name="owners"),  # safe duplicate for compatibility
    path("owners/create/",          OwnerCreateView.as_view(),                      name="owner_create"),
    path("owners/<int:limit>/edit/",OwnerUpdateView.as_view(),                      name="owner_edit"),  # noqa
    path("owners/<int:pk>/edit/",   OwnerUpdateView.as_view(),                      name="owner_edit"),
    path("owners/<int:pk>/delete/", OwnerDeleteView.as_view(),                      name="owner_delete"),
    path("owners/<int:pk>/pdf/",    owner_pdf,                                      name="owner_pdf"),

    # Lessees
    path("lessees/",                 LesseeListView.as_view(),                      name="lessees"),
    path("lessees/create/",          LesseeCreateView.as_view(),                    name="lessee_create"),
    path("lessees/<int:pk>/edit/",   LesseeUpdateView.as_view(),                    name="lessee_edit"),
    path("lessees/<int:pk>/delete/", LesseeDeleteView.as_view(),                    name="lessee_delete"),
    path("lessees/<int:pk>/pdf/",    lessee_pdf,                                    name="lessee_pdf"),

    # Type-ahead search APIs (used by /flats/<id>/occupancy/)
    path("api/owners",  owners_search,  name="owners_search"),
    path("api/lessees", lessees_search, name="lessees_search"),
]
