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
    list_display = ('name', 'slug', 'icon_class', 'is_active', 'places_count', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at', 'updated_at')
    actions = ['make_active', 'make_inactive']

    def places_count(self, obj):
        return obj.places.count()
    places_count.short_description = 'Places'

    def make_active(self, request, queryset):
        queryset.update(is_active=True)
    make_active.short_description = "Mark selected categories as Active"

    def make_inactive(self, request, queryset):
        queryset.update(is_active=False)
    make_inactive.short_description = "Mark selected categories as Inactive"


@admin.register(Place)
class PlaceAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'category',
        'locality',
        'verification_status',
        'is_featured',
        'is_active',
        'last_verified_at',
        'view_count',
        'created_at',
    )
    list_filter = (
        'is_active',
        'is_featured',
        'verification_status',
        'category',
        'locality__zone',
        'locality',
        'wheelchair_accessible',
        'created_at',
    )
    search_fields = (
        'title',
        'title_ur',
        'summary',
        'description',
        'address',
        'architectural_era',
        'landmark',
        'source_url',
    )
    date_hierarchy = 'created_at'
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ('created_at', 'updated_at', 'last_verified_at', 'verified_by', 'view_count')
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
        ('Editorial Verification & Provenance', {
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
        ('Traffic & SEO Metadata', {
            'fields': ('view_count', 'meta_title', 'meta_description', 'canonical_url', 'og_image'),
            'classes': ('collapse',),
        }),
    )

    def has_delete_permission(self, request, obj=None):
        """Only administrators can delete verified heritage & tourist listings."""
        if request.user.is_superuser or getattr(request.user, 'role', '') == 'admin':
            return True
        return False

    def make_verified(self, request, queryset):
        rows = queryset.update(
            verification_status='verified',
            verified_by=request.user if request.user.is_authenticated else None,
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
    publish.short_description = "Publish selected places (Set Active)"

    def unpublish(self, request, queryset):
        rows = queryset.update(is_active=False)
        self.message_user(request, f"{rows} place(s) unpublished.")
    unpublish.short_description = "Unpublish selected places (Hide from public)"
