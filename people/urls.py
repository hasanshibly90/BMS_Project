from django.urls import path
from django.http import HttpResponse
def placeholder(_): return HttpResponse('people app placeholder')
app_name = 'people'
urlpatterns = [ path('', placeholder, name='placeholder') ]
