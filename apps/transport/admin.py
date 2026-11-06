from django.contrib import admin
from .models import TransitMode, TransitRoute, TransitStation

class TransitStationInline(admin.TabularInline):
    model = TransitStation
    extra = 2

@admin.register(TransitMode)
class TransitModeAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'icon_class')
    prepopulated_fields = {'slug': ('name',)}

@admin.register(TransitRoute)
class TransitRouteAdmin(admin.ModelAdmin):
    list_display = ('route_code', 'route_name', 'mode', 'origin_station', 'destination_station', 'total_stations')
    list_filter = ('mode',)
    search_fields = ('route_name', 'route_code')
    inlines = [TransitStationInline]

@admin.register(TransitStation)
class TransitStationAdmin(admin.ModelAdmin):
    list_display = ('station_name', 'route', 'station_number', 'locality', 'is_interchange')
    list_filter = ('route__mode', 'is_interchange', 'locality')
    search_fields = ('station_name',)
