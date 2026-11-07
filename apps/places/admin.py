from django.contrib import admin
from django.utils import timezone
from .models import PlaceCategory, Place, PlaceGalleryImage


class PlaceGalleryImageInline(admin.TabularInline):
    model = PlaceGalleryImage
    extra = 1
    fields = ('image', 'caption', 'photographer_credit', 'display_order')
    ordering = ('display_order',)


@admin.register(PlaceCategory)
class PlaceCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'icon_class', 'is_active', 'places_count')
    list_filter = ('is_active',)
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}

    def places_count(self, obj):
        return obj.places.count()
    places_count.short_description = 'Places'


@admin.register(Place)
class PlaceAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'category',
        'locality',
        'verification_status',
        'is_featured',
        'is_active',
        'view_count',
        'created_at'
    )
    list_filter = (
        'is_active',
        'is_featured',
        'verification_status',
        'category',
        'locality__zone',
        'wheelchair_accessible'
    )
    search_fields = (
        'title',
        'title_ur',
        'summary',
        'description',
        'address',
        'architectural_era',
        'landmark'
    )
    prepopulated_fields = {'slug': ('title',)}
    autocomplete_fields = ()
    inlines = [PlaceGalleryImageInline]
    actions = ['make_verified', 'make_featured', 'unfeature', 'publish', 'unpublish']

    fieldsets = (
        ('Identity & Taxonomy', {
            'fields': ('title', 'title_ur', 'slug', 'category', 'summary', 'description')
        }),
        ('Location & Transit Access', {
            'fields': (
                'locality',
                'address',
                'landmark',
                'latitude',
                'longitude',
                'google_maps_url',
                'nearest_metro_station'
            )
        }),
        ('Visitor Logistics & Access', {
            'fields': (
                'architectural_era',
                'opening_time',
                'closing_time',
                'closed_on_days',
                'entry_fee_pkr',
                'entry_fee_foreigner_pkr',
                'photography_policy',
                'wheelchair_accessible'
            )
        }),
        ('Contact Endpoints', {
            'fields': (
                'phone_number',
                'emergency_phone',
                'email',
                'website',
                'whatsapp_number'
            )
        }),
        ('Media & Imagery', {
            'fields': ('primary_image',)
        }),
        ('Editorial Verification', {
            'fields': (
                'verification_status',
                'verified_by',
                'last_verified_at',
                'source_url',
                'verification_notes'
            )
        }),
        ('Publishing Controls', {
            'fields': ('is_active', 'is_featured', 'featured_until')
        }),
        ('SEO Metadata', {
            'fields': ('meta_title', 'meta_description', 'canonical_url', 'og_image'),
            'classes': ('collapse',)
        }),
    )

    def make_verified(self, request, queryset):
        rows = queryset.update(
            verification_status='verified',
            verified_by=request.user,
            last_verified_at=timezone.now()
        )
        self.message_user(request, f"{rows} place(s) marked as officially verified.")
    make_verified.short_description = "Mark selected as Verified Record"

    def make_featured(self, request, queryset):
        rows = queryset.update(is_featured=True)
        self.message_user(request, f"{rows} place(s) marked as Featured.")
    make_featured.short_description = "Feature on Homepage & Spotlight"

    def unfeature(self, request, queryset):
        rows = queryset.update(is_featured=False)
        self.message_user(request, f"{rows} place(s) removed from Featured.")
    unfeature.short_description = "Remove from Featured Spotlight"

    def publish(self, request, queryset):
        rows = queryset.update(is_active=True)
        self.message_user(request, f"{rows} place(s) published.")
    publish.short_description = "Publish selected places"

    def unpublish(self, request, queryset):
        rows = queryset.update(is_active=False)
        self.message_user(request, f"{rows} place(s) unpublished.")
    unpublish.short_description = "Unpublish selected places (Hide from public)"
