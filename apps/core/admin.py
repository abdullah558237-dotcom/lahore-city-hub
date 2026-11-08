from django.contrib import admin
from .models import LocalityZone, Locality, EmergencyHelpline


@admin.register(LocalityZone)
class LocalityZoneAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'localities_count', 'created_at')
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at', 'updated_at')

    def localities_count(self, obj):
        return obj.localities.count()
    localities_count.short_description = 'Localities'


@admin.register(Locality)
class LocalityAdmin(admin.ModelAdmin):
    list_display = ('name', 'zone', 'postal_code', 'created_at')
    list_filter = ('zone', 'created_at')
    search_fields = ('name', 'postal_code', 'zone__name')
    prepopulated_fields = {'slug': ('name',)}
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at', 'updated_at')


@admin.register(EmergencyHelpline)
class EmergencyHelplineAdmin(admin.ModelAdmin):
    list_display = ('name', 'short_code', 'agency_name', 'full_phone_number', 'is_active', 'display_order', 'created_at')
    list_editable = ('is_active', 'display_order')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'short_code', 'agency_name', 'full_phone_number')
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at', 'updated_at')
