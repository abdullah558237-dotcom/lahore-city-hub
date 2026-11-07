from django.contrib import admin
from django.utils import timezone
from .models import EventCategory, EventVenue, Event


@admin.register(EventCategory)
class EventCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'icon_class', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(EventVenue)
class EventVenueAdmin(admin.ModelAdmin):
    list_display = ('name', 'locality', 'capacity', 'address')
    list_filter = ('locality',)
    search_fields = ('name', 'address', 'locality__name')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'category',
        'venue',
        'start_datetime',
        'end_datetime',
        'ticket_policy',
        'is_featured',
        'is_active',
    )
    list_filter = (
        'is_active',
        'is_featured',
        'category',
        'ticket_policy',
        'start_datetime',
        'verification_status',
    )
    search_fields = (
        'title',
        'description',
        'organizer_name',
        'venue__name',
        'venue__address',
    )
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ('created_at', 'updated_at')
    actions = [
        'publish_events',
        'unpublish_events',
        'mark_as_featured',
        'unmark_featured',
        'mark_as_verified',
    ]

    fieldsets = (
        ('Event Core Details', {
            'fields': ('title', 'slug', 'category', 'venue', 'custom_address', 'banner_image')
        }),
        ('Schedule & Timings', {
            'fields': ('start_datetime', 'end_datetime')
        }),
        ('Ticketing & Access', {
            'fields': ('ticket_policy', 'ticket_price_pkr', 'ticket_or_registration_url')
        }),
        ('Organization & Editorial', {
            'fields': ('organizer_name', 'organizer_contact', 'description')
        }),
        ('Publication & Provenance', {
            'fields': (
                'is_active',
                'is_featured',
                'verification_status',
                'verified_by',
                'last_verified_at',
                'source_url',
                'verification_notes',
            )
        }),
        ('SEO & Social Sharing', {
            'fields': ('meta_title', 'meta_description', 'canonical_url', 'og_image'),
            'classes': ('collapse',),
        }),
    )

    def publish_events(self, request, queryset):
        count = queryset.update(is_active=True)
        if request:
            self.message_user(request, f"{count} event(s) published successfully.")
    publish_events.short_description = "Publish selected events"

    def unpublish_events(self, request, queryset):
        count = queryset.update(is_active=False)
        if request:
            self.message_user(request, f"{count} event(s) unpublished.")
    unpublish_events.short_description = "Unpublish selected events"

    def mark_as_featured(self, request, queryset):
        count = queryset.update(is_featured=True)
        if request:
            self.message_user(request, f"{count} event(s) marked as featured.")
    mark_as_featured.short_description = "Mark selected as Featured"

    def unmark_featured(self, request, queryset):
        count = queryset.update(is_featured=False)
        if request:
            self.message_user(request, f"{count} event(s) removed from featured.")
    unmark_featured.short_description = "Remove from Featured"

    def mark_as_verified(self, request, queryset):
        now = timezone.now()
        user = request.user if request and hasattr(request, 'user') and request.user.is_authenticated else None
        count = queryset.update(verification_status='verified', last_verified_at=now, verified_by=user)
        if request:
            self.message_user(request, f"{count} event(s) verified.")
    mark_as_verified.short_description = "Mark selected as Verified Official Record"
