# bms/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from core.views import DashboardView, BulkOwnersView, SyncStatusView, OverviewBoardView  # ← add OverviewBoardView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("django.contrib.auth.urls")),

    path("", DashboardView.as_view(), name="dashboard"),

    # Tools
    path("tools/bulk-owners/", BulkOwnersView.as_view(), name="bulk_owners"),
    path("tools/sync-status/", SyncStatusView.as_view(), name="sync_status"),

    # Overview (at-a-glance)
    path("overview/", OverviewBoardView.as_view(), name="overview"),   # ← add this

    # Apps (namespaced)
    path("flats/",     include(("flats.urls", "flats"),         namespace="flats")),
    path("people/",    include(("people.urls", "people"),       namespace="people")),
    path("parking/",   include(("parking.urls", "parking"),     namespace="parking")),
    path("elections/", include(("elections.urls", "elections"), namespace="elections")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
