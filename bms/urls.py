from django.contrib import admin
from django.urls import path, include
from importlib import import_module
from core.views import DashboardView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', DashboardView.as_view(), name='dashboard'),
]

def optional_include(prefix: str, module_path: str):
    try:
        import_module(module_path)
        urlpatterns.append(path(prefix, include(module_path)))
    except ModuleNotFoundError:
        # app not created yet — skip
        pass

optional_include('flats/', 'flats.urls')
optional_include('people/', 'people.urls')
optional_include('parking/', 'parking.urls')
optional_include('elections/', 'elections.urls')
