from django.contrib import admin
from .models import Owner, Lessee, Ownership, Tenancy

@admin.register(Owner)
class OwnerAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'email')
    search_fields = ('name', 'phone', 'email')

@admin.register(Lessee)
class LesseeAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'email')
    search_fields = ('name', 'phone', 'email')

@admin.register(Ownership)
class OwnershipAdmin(admin.ModelAdmin):
    list_display = ('flat', 'owner', 'start_date', 'end_date')
    list_filter = ('start_date', 'end_date')

@admin.register(Tenancy)
class TenancyAdmin(admin.ModelAdmin):
    list_display = ('flat', 'lessee', 'start_date', 'end_date')
    list_filter = ('start_date', 'end_date')
