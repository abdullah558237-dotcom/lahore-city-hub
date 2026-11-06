from django.contrib import admin
from .models import Cuisine, RestaurantFeature, Restaurant, MenuHighlight

class MenuHighlightInline(admin.TabularInline):
    model = MenuHighlight
    extra = 1

@admin.register(Cuisine)
class CuisineAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}

@admin.register(RestaurantFeature)
class RestaurantFeatureAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'icon_class')
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Restaurant)
class RestaurantAdmin(admin.ModelAdmin):
    list_display = ('title', 'price_tier', 'locality', 'has_family_hall', 'verification_status', 'is_featured', 'is_active')
    list_filter = ('price_tier', 'has_family_hall', 'verification_status', 'is_featured', 'is_active', 'locality')
    search_fields = ('title', 'summary', 'address')
    prepopulated_fields = {'slug': ('title',)}
    filter_horizontal = ('cuisines', 'features')
    inlines = [MenuHighlightInline]
