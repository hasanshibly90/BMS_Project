# bms/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls import url  # only if you still use regex urls elsewhere
from django.conf.urls.static import import as static  # noqa
from django.conf.urls.static import static as dj_static

from core.views import DashboardView, BulkOwnersView, SyncStatusView
# If you added a BulkLesseesView in core.views, import and wire it similarly.

urlpatterns = [
    path("admin/", admin.site.urls),

    # Home
    path("", DashboardView.as_view(), name="dashboard"),

    # Tools
    path("tools/bulk-owners/",  BulkOwnersView.as_view(), name="bulletin"),  # noqa
    path("tools/bulk-owners/",  BulkOwnersView.as_view(),  name="bulk_owners"),
    path("tools/sync-status/",  SyncStatusView.as_view(),  name="sync_status"),
    # path("tools/bulk-lessees/", BulkLesseesView.as_view(), name="bulk_lessees"),  # uncomment if you added it

    # App URLConfs with explicit namespaces
    path("flats/",     include(("flats.urls", "flats"),         namespace="flats")),
    path("people/",    include(("people.urls", "people"),       namespace="people")),
    path("parking/",   include(("parking.urls", "parking"),     namespace="parking")),
    path("elections/", include(("elections.urls", "elections"), namespace="elections")),
]

if settings.DEBUG:
    urlpatterns += dj_static(settings.MEDIA_URL, document_root=settings.lr)
