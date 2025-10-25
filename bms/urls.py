from django.contrib import admin
from django.urls import path, include
from importlib import import_module
from django.conf import settings
from django.conf.urls.static import static

from core.views import DashboardView, BulkOwnersView, SyncStatusView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', DashboardView.as_view(), name='dashboard'),

    # Tools
    path('tools/bulk-owners/', BulkOwnersView.as_view(), name='bulk_owners'),
    path('tools/sync-status/', SyncStatusView.as_view(), name='sync_status'),
]


def optional_include(prefix: str, module_path: str):
    """
    Append app urls if the module is importable; otherwise silently skip.
    """
    try:
        import_module(module_path)
    except (ModuleNotFoundError, ImportError):
        return
    urlpatterns.append(path(prefix, include(module_path)))


# App routes (auto-skip if app not present yet)
optional_include('flats/', 'flats.urls')
optional_include('people/', 'people.urls')
optional_include('parking/', 'parking.urls')
optional_include('elections/', 'elections.urls')

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
