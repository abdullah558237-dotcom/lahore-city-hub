from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, UserProfile, UserBookmark


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ('email', 'username', 'role', 'is_verified', 'is_active', 'is_staff', 'is_superuser', 'date_joined')
    list_filter = ('role', 'is_verified', 'is_active', 'is_staff', 'is_superuser', 'date_joined')
    search_fields = ('email', 'username', 'first_name', 'last_name', 'phone_number')
    ordering = ('-date_joined',)
    date_hierarchy = 'date_joined'
    actions = ['verify_users', 'unverify_users', 'activate_users', 'deactivate_users']

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('username', 'first_name', 'last_name', 'phone_number', 'avatar')}),
        ('Permissions & Role', {
            'fields': (
                'role',
                'is_verified',
                'is_active',
                'is_staff',
                'is_superuser',
                'groups',
                'user_permissions'
            )
        }),
        ('Important Dates', {'fields': ('last_login', 'date_joined')}),
    )

    def has_delete_permission(self, request, obj=None):
        """Only superusers can delete user accounts."""
        if request.user.is_superuser:
            return True
        return False

    def verify_users(self, request, queryset):
        count = queryset.update(is_verified=True)
        if request:
            self.message_user(request, f"{count} user account(s) marked as verified.")
    verify_users.short_description = "Mark selected accounts as Verified"

    def unverify_users(self, request, queryset):
        count = queryset.update(is_verified=False)
        if request:
            self.message_user(request, f"{count} user account(s) marked as unverified.")
    unverify_users.short_description = "Mark selected accounts as Unverified"

    def activate_users(self, request, queryset):
        count = queryset.update(is_active=True)
        if request:
            self.message_user(request, f"{count} user account(s) activated.")
    activate_users.short_description = "Activate selected user accounts"

    def deactivate_users(self, request, queryset):
        count = queryset.update(is_active=False)
        if request:
            self.message_user(request, f"{count} user account(s) deactivated.")
    deactivate_users.short_description = "Deactivate selected user accounts"


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'home_locality', 'receive_smog_alerts', 'receive_event_digests', 'created_at')
    list_filter = ('receive_smog_alerts', 'receive_event_digests', 'created_at')
    search_fields = ('user__email', 'user__username', 'home_locality', 'bio')
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at', 'updated_at')


@admin.register(UserBookmark)
class UserBookmarkAdmin(admin.ModelAdmin):
    list_display = ('user', 'content_type', 'object_id', 'created_at')
    list_filter = ('content_type', 'created_at')
    search_fields = ('user__email', 'user__username', 'notes')
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at',)
