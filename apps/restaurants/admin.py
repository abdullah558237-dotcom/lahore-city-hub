from django.contrib import admin
from django.utils import timezone
from .models import Cuisine, RestaurantFeature, Restaurant, MenuHighlight, RestaurantGalleryImage


class MenuHighlightInline(admin.TabularInline):
    model = MenuHighlight
    extra = 1
    fields = ('item_name', 'description', 'price_pkr', 'is_signature')


class RestaurantGalleryImageInline(admin.TabularInline):
    model = RestaurantGalleryImage
    extra = 1
    fields = ('image', 'caption', 'photographer_credit', 'display_order')
    ordering = ('display_order',)


@admin.register(Cuisine)
class CuisineAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'is_active', 'restaurants_count', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at', 'updated_at')
    actions = ['make_active', 'make_inactive']

    def restaurants_count(self, obj):
        return obj.restaurants.count()
    restaurants_count.short_description = 'Restaurants'

    def make_active(self, request, queryset):
        queryset.update(is_active=True)
    make_active.short_description = "Mark selected cuisines as Active"

    def make_inactive(self, request, queryset):
        queryset.update(is_active=False)
    make_inactive.short_description = "Mark selected cuisines as Inactive"


@admin.register(RestaurantFeature)
class RestaurantFeatureAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'icon_class', 'restaurants_count', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at', 'updated_at')

    def restaurants_count(self, obj):
        return obj.restaurants.count()
    restaurants_count.short_description = 'Restaurants'


@admin.register(Restaurant)
class RestaurantAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'locality',
        'price_tier',
        'cuisines_summary',
        'has_family_hall',
        'provides_delivery',
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
        'price_tier',
        'cuisines',
        'locality__zone',
        'locality',
        'has_family_hall',
        'provides_takeaway',
        'provides_delivery',
        'created_at',
    )
    search_fields = (
        'title',
        'title_ur',
        'summary',
        'description',
        'address',
        'landmark',
        'source_url',
    )
    date_hierarchy = 'created_at'
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ('created_at', 'updated_at', 'last_verified_at', 'verified_by', 'view_count')
    filter_horizontal = ('cuisines', 'features')
    inlines = [MenuHighlightInline, RestaurantGalleryImageInline]
    actions = ['make_verified', 'make_featured', 'unfeature', 'publish', 'unpublish']

    fieldsets = (
        ('Identity & Overview', {
            'fields': ('title', 'title_ur', 'slug', 'summary', 'description')
        }),
        ('Dining Classification & Ambience', {
            'fields': ('price_tier', 'cuisines', 'features', 'seating_capacity')
        }),
        ('Location & Directions', {
            'fields': (
                'locality',
                'address',
                'landmark',
                'latitude',
                'longitude',
                'google_maps_url'
            )
        }),
        ('Operational Schedule & Facilities', {
            'fields': (
                'opening_time',
                'closing_time',
                'closed_on_days',
                'ramadan_timings',
                'has_family_hall',
                'provides_takeaway',
                'provides_delivery'
            )
        }),
        ('Contact Channels', {
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
        ('Editorial Verification & Moderation', {
            'fields': (
                'verification_status',
                'verified_by',
                'last_verified_at',
                'source_url',
                'verification_notes',
                'is_featured',
                'featured_until',
                'is_active'
            )
        }),
        ('Traffic & SEO Metadata', {
            'classes': ('collapse',),
            'fields': ('view_count', 'meta_title', 'meta_description', 'canonical_url', 'og_image')
        }),
    )

    def cuisines_summary(self, obj):
        return ", ".join([c.name for c in obj.cuisines.all()[:3]]) or "—"
    cuisines_summary.short_description = 'Cuisines'

    def has_delete_permission(self, request, obj=None):
        """Only administrators can delete restaurant entries."""
        if request.user.is_superuser or getattr(request.user, 'role', '') == 'admin':
            return True
        return False

    def make_verified(self, request, queryset):
        now = timezone.now()
        user = request.user if request and hasattr(request, 'user') and request.user.is_authenticated else None
        updated = queryset.update(
            verification_status='verified',
            verified_by=user,
            last_verified_at=now
        )
        if request:
            self.message_user(request, f"{updated} restaurant(s) marked as officially verified.")
    make_verified.short_description = "Mark selected restaurants as Verified Record"

    def make_featured(self, request, queryset):
        updated = queryset.update(is_featured=True)
        if request:
            self.message_user(request, f"{updated} restaurant(s) marked as featured.")
    make_featured.short_description = "Feature on Homepage & Spotlight"

    def unfeature(self, request, queryset):
        updated = queryset.update(is_featured=False)
        if request:
            self.message_user(request, f"{updated} restaurant(s) unfeatured.")
    unfeature.short_description = "Remove from Featured Spotlight"

    def publish(self, request, queryset):
        updated = queryset.update(is_active=True)
        if request:
            self.message_user(request, f"{updated} restaurant(s) published.")
    publish.short_description = "Publish selected restaurants (Set Active)"

    def unpublish(self, request, queryset):
        updated = queryset.update(is_active=False)
        if request:
            self.message_user(request, f"{updated} restaurant(s) unpublished.")
    unpublish.short_description = "Unpublish selected restaurants (Hide from public)"
