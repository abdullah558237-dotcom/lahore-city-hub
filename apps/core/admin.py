from django.contrib import admin
from .models import LocalityZone, Locality, EmergencyHelpline

@admin.register(LocalityZone)
class LocalityZoneAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'created_at')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)

@admin.register(Locality)
class LocalityAdmin(admin.ModelAdmin):
    list_display = ('name', 'zone', 'postal_code', 'created_at')
    list_filter = ('zone',)
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name', 'postal_code')

@admin.register(EmergencyHelpline)
class EmergencyHelplineAdmin(admin.ModelAdmin):
    list_display = ('name', 'short_code', 'agency_name', 'is_active', 'display_order')
    list_editable = ('is_active', 'display_order')
    search_fields = ('name', 'short_code', 'agency_name')
