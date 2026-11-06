from django.contrib import admin
from .models import PlaceCategory, Place, PlaceGalleryImage

class PlaceGalleryInline(admin.TabularInline):
    model = PlaceGalleryImage
    extra = 1

@admin.register(PlaceCategory)
class PlaceCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Place)
class PlaceAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'locality', 'verification_status', 'is_featured', 'is_active')
    list_filter = ('verification_status', 'is_featured', 'is_active', 'category', 'locality')
    search_fields = ('title', 'summary', 'address')
    prepopulated_fields = {'slug': ('title',)}
    inlines = [PlaceGalleryInline]
