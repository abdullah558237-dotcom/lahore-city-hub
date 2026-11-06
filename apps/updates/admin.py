from django.contrib import admin
from .models import UpdateCategory, CityUpdate

@admin.register(UpdateCategory)
class UpdateCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}

@admin.register(CityUpdate)
class CityUpdateAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'severity', 'issuing_authority', 'is_pinned', 'is_active', 'valid_from')
    list_filter = ('severity', 'is_pinned', 'is_active', 'category')
    search_fields = ('title', 'summary', 'issuing_authority')
    prepopulated_fields = {'slug': ('title',)}
