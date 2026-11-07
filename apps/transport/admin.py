from django.contrib import admin
from django.utils import timezone
from .models import TransitMode, TransitRoute, TransitStation, TransitGuide


class TransitStationInline(admin.TabularInline):
    model = TransitStation
    extra = 1
    fields = ('station_number', 'station_name', 'urdu_name', 'is_interchange', 'is_terminal', 'is_underground', 'locality')
    ordering = ('station_number',)


@admin.register(TransitMode)
class TransitModeAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'icon_class', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'slug', 'description')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(TransitRoute)
class TransitRouteAdmin(admin.ModelAdmin):
    list_display = (
        'route_code',
        'route_name',
        'mode',
        'origin_station',
        'destination_station',
        'total_stations',
        'total_distance_km',
        'operating_schedule',
        'is_featured',
        'is_active',
        'last_updated_date',
    )
    list_filter = ('mode', 'is_active', 'is_featured')
    search_fields = ('route_name', 'route_code', 'origin_station', 'destination_station', 'operator')
    prepopulated_fields = {'slug': ('route_code', 'route_name')}
    inlines = [TransitStationInline]
    actions = ['make_active', 'make_inactive', 'mark_as_featured', 'unmark_featured']

    fieldsets = (
        ('Route Identification', {
            'fields': ('route_code', 'route_name', 'slug', 'mode', 'operator')
        }),
        ('Terminals & Scope', {
            'fields': ('origin_station', 'destination_station', 'total_stations', 'total_distance_km')
        }),
        ('Schedules & Fares', {
            'fields': ('operating_schedule', 'frequency', 'fare_info', 'description')
        }),
        ('Provenance & Governance', {
            'fields': ('source_url', 'last_updated_date', 'is_active', 'is_featured')
        }),
    )

    def make_active(self, request, queryset):
        count = queryset.update(is_active=True)
        if request:
            self.message_user(request, f"{count} transit route(s) marked as active.")
    make_active.short_description = "Publish selected routes (Set Active)"

    def make_inactive(self, request, queryset):
        count = queryset.update(is_active=False)
        if request:
            self.message_user(request, f"{count} transit route(s) marked as inactive.")
    make_inactive.short_description = "Unpublish selected routes (Set Inactive)"

    def mark_as_featured(self, request, queryset):
        count = queryset.update(is_featured=True)
        if request:
            self.message_user(request, f"{count} route(s) marked as featured.")
    mark_as_featured.short_description = "Mark selected as Featured"

    def unmark_featured(self, request, queryset):
        count = queryset.update(is_featured=False)
        if request:
            self.message_user(request, f"{count} route(s) removed from featured.")
    unmark_featured.short_description = "Remove from Featured"


@admin.register(TransitStation)
class TransitStationAdmin(admin.ModelAdmin):
    list_display = (
        'station_name',
        'urdu_name',
        'route',
        'station_number',
        'locality',
        'is_interchange',
        'is_terminal',
        'is_underground',
        'has_wheelchair_access',
    )
    list_filter = (
        'route__mode',
        'route',
        'is_interchange',
        'is_terminal',
        'is_underground',
        'has_wheelchair_access',
        'has_parking',
    )
    search_fields = ('station_name', 'urdu_name', 'nearby_landmarks', 'interchange_details')
    prepopulated_fields = {'slug': ('station_name',)}
    ordering = ('route', 'station_number')


@admin.register(TransitGuide)
class TransitGuideAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'category',
        'route',
        'is_published',
        'is_featured',
        'display_order',
        'last_verified_date',
    )
    list_filter = ('category', 'is_published', 'is_featured')
    search_fields = ('title', 'summary', 'content')
    prepopulated_fields = {'slug': ('title',)}
    actions = ['publish_guides', 'unpublish_guides', 'mark_featured', 'unmark_featured']

    def publish_guides(self, request, queryset):
        count = queryset.update(is_published=True)
        if request:
            self.message_user(request, f"{count} travel guide(s) published.")
    publish_guides.short_description = "Publish selected guides"

    def unpublish_guides(self, request, queryset):
        count = queryset.update(is_published=False)
        if request:
            self.message_user(request, f"{count} travel guide(s) unpublished.")
    unpublish_guides.short_description = "Unpublish selected guides"

    def mark_featured(self, request, queryset):
        count = queryset.update(is_featured=True)
        if request:
            self.message_user(request, f"{count} guide(s) marked as featured.")
    mark_featured.short_description = "Mark selected as Featured"

    def unmark_featured(self, request, queryset):
        count = queryset.update(is_featured=False)
        if request:
            self.message_user(request, f"{count} guide(s) removed from featured.")
    unmark_featured.short_description = "Remove from Featured"
