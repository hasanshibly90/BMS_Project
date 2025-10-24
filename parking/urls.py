from django.urls import path
from django.http import HttpResponse
def placeholder(_): return HttpResponse('parking app placeholder')
app_name = 'parking'
urlpatterns = [ path('', placeholder, name='placeholder') ]
