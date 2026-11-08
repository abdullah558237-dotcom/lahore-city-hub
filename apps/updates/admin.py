from django.contrib import admin
from django.utils import timezone
from .models import UpdateCategory, CityUpdate


@admin.register(UpdateCategory)
class UpdateCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'is_active', 'updates_count', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at', 'updated_at')
    actions = ['make_active', 'make_inactive']

    def updates_count(self, obj):
        return obj.updates.count()
    updates_count.short_description = 'Notices'

    def make_active(self, request, queryset):
        queryset.update(is_active=True)
    make_active.short_description = "Mark selected categories as Active"

    def make_inactive(self, request, queryset):
        queryset.update(is_active=False)
    make_inactive.short_description = "Mark selected categories as Inactive"


@admin.register(CityUpdate)
class CityUpdateAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'category',
        'severity',
        'issuing_authority',
        'is_pinned',
        'is_active',
        'valid_from',
        'valid_until',
        'created_at',
    )
    list_filter = (
        'severity',
        'is_pinned',
        'is_active',
        'category',
        'valid_from',
        'created_at',
    )
    search_fields = (
        'title',
        'summary',
        'content',
        'issuing_authority',
        'official_source_url',
    )
    date_hierarchy = 'valid_from'
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ('created_at', 'updated_at')
    actions = [
        'publish_updates',
        'unpublish_updates',
        'pin_updates',
        'unpin_updates',
    ]

    fieldsets = (
        ('Update Core & Headline', {
            'fields': ('title', 'slug', 'category', 'severity', 'summary')
        }),
        ('Full Announcement Text', {
            'fields': ('content',)
        }),
        ('Issuing Authority & Provenance', {
            'fields': ('issuing_authority', 'official_source_url')
        }),
        ('Validity Window', {
            'fields': ('valid_from', 'valid_until')
        }),
        ('Publication & Pinning', {
            'fields': ('is_active', 'is_pinned')
        }),
        ('SEO & Metadata', {
            'classes': ('collapse',),
            'fields': ('meta_title', 'meta_description', 'canonical_url', 'created_at', 'updated_at')
        }),
    )

    def has_delete_permission(self, request, obj=None):
        """Only administrators can delete civic notices and smog alerts."""
        if request.user.is_superuser or getattr(request.user, 'role', '') == 'admin':
            return True
        return False

    def publish_updates(self, request, queryset):
        count = queryset.update(is_active=True)
        if request:
            self.message_user(request, f"{count} city update(s) published.")
    publish_updates.short_description = "Publish selected updates (Set Active)"

    def unpublish_updates(self, request, queryset):
        count = queryset.update(is_active=False)
        if request:
            self.message_user(request, f"{count} city update(s) unpublished.")
    unpublish_updates.short_description = "Unpublish selected updates (Set Inactive)"

    def pin_updates(self, request, queryset):
        count = queryset.update(is_pinned=True)
        if request:
            self.message_user(request, f"{count} update(s) pinned to top of notices.")
    pin_updates.short_description = "Pin to top (Emergency Banner)"

    def unpin_updates(self, request, queryset):
        count = queryset.update(is_pinned=False)
        if request:
            self.message_user(request, f"{count} update(s) unpinned.")
    unpin_updates.short_description = "Unpin from top"
