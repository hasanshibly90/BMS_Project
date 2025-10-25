from django.contrib import admin
from .models import ServiceCategory, ServiceProvider

@admin.register(ServiceCategory)
class ServiceCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name",)

@admin.register(ServiceProvider)
class ServiceProviderAdmin(admin.ModelAdmin):
    list_display = ("full_name", "category", "phone", "email", "is_active", "created_at")
    list_filter = ("is_active", "category")
    search_fields = ("full_name", "phone", "email", "address", "nid_number")
