from django.contrib import admin
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
    list_display = ('name', 'slug', 'is_active', 'restaurants_count')
    list_filter = ('is_active',)
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}

    def restaurants_count(self, obj):
        return obj.restaurants.count()
    restaurants_count.short_description = 'Restaurants'


@admin.register(RestaurantFeature)
class RestaurantFeatureAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'icon_class', 'restaurants_count')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}

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
        'view_count',
        'created_at'
    )
    list_filter = (
        'is_active',
        'is_featured',
        'verification_status',
        'price_tier',
        'cuisines',
        'locality__zone',
        'has_family_hall',
        'provides_takeaway',
        'provides_delivery'
    )
    search_fields = (
        'title',
        'title_ur',
        'summary',
        'description',
        'address',
        'landmark'
    )
    prepopulated_fields = {'slug': ('title',)}
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
                'is_featured',
                'featured_until',
                'is_active'
            )
        }),
        ('SEO Metadata', {
            'classes': ('collapse',),
            'fields': ('meta_title', 'meta_description', 'canonical_url')
        }),
    )

    def cuisines_summary(self, obj):
        return ", ".join([c.name for c in obj.cuisines.all()[:3]]) or "—"
    cuisines_summary.short_description = 'Cuisines'

    def make_verified(self, request, queryset):
        updated = queryset.update(verification_status='verified')
        if request:
            self.message_user(request, f"{updated} restaurant(s) marked as verified.")
    make_verified.short_description = "Mark selected restaurants as Verified"

    def make_featured(self, request, queryset):
        updated = queryset.update(is_featured=True)
        if request:
            self.message_user(request, f"{updated} restaurant(s) marked as featured.")
    make_featured.short_description = "Mark selected restaurants as Featured"

    def unfeature(self, request, queryset):
        updated = queryset.update(is_featured=False)
        if request:
            self.message_user(request, f"{updated} restaurant(s) unfeatured.")
    unfeature.short_description = "Remove featured status from selected restaurants"

    def publish(self, request, queryset):
        updated = queryset.update(is_active=True)
        if request:
            self.message_user(request, f"{updated} restaurant(s) published.")
    publish.short_description = "Publish selected restaurants"

    def unpublish(self, request, queryset):
        updated = queryset.update(is_active=False)
        if request:
            self.message_user(request, f"{updated} restaurant(s) unpublished.")
    unpublish.short_description = "Unpublish selected restaurants"
