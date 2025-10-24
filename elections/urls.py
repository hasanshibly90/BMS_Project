from django.urls import path
from django.http import HttpResponse
def placeholder(_): return HttpResponse('elections app placeholder')
app_name = 'elections'
urlpatterns = [ path('', placeholder, name='placeholder') ]
