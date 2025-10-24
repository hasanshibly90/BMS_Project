from django.urls import path
from django.http import HttpResponse
def placeholder(_): return HttpResponse('flats app placeholder')
app_name = 'flats'
urlpatterns = [ path('', placeholder, name='placeholder') ]
