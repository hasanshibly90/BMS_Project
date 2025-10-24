from django.conf import settings

def app_meta(request):
    return {
        "APP_NAME": getattr(settings, "APP_NAME", "BMS"),
        "APP_VERSION": getattr(settings, "APP_VERSION", "0.1.0"),
    }
