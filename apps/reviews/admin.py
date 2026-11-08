from django.contrib import admin
from .models import Review


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('user', 'content_object', 'rating', 'moderation_status', 'created_at')
    list_filter = ('moderation_status', 'rating', 'created_at')
    search_fields = ('user__email', 'title', 'comment')
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at', 'updated_at')
    actions = ['approve_reviews', 'reject_reviews', 'flag_reviews']

    def has_delete_permission(self, request, obj=None):
        """Only administrators can delete user community reviews."""
        if request.user.is_superuser or getattr(request.user, 'role', '') == 'admin':
            return True
        return False

    def approve_reviews(self, request, queryset):
        count = queryset.update(moderation_status=Review.STATUS_APPROVED)
        if request:
            self.message_user(request, f"{count} review(s) approved and published.")
    approve_reviews.short_description = "Approve & Publish selected reviews"

    def reject_reviews(self, request, queryset):
        count = queryset.update(moderation_status=Review.STATUS_REJECTED)
        if request:
            self.message_user(request, f"{count} review(s) rejected.")
    reject_reviews.short_description = "Reject selected reviews"

    def flag_reviews(self, request, queryset):
        count = queryset.update(moderation_status=Review.STATUS_FLAGGED)
        if request:
            self.message_user(request, f"{count} review(s) flagged for audit.")
    flag_reviews.short_description = "Flag selected reviews for audit"
