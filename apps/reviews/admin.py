from django.contrib import admin
from .models import Review

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('user', 'content_object', 'rating', 'moderation_status', 'created_at')
    list_filter = ('moderation_status', 'rating', 'created_at')
    search_fields = ('user__email', 'title', 'comment')
    actions = ['approve_reviews', 'reject_reviews']

    def approve_reviews(self, request, queryset):
        queryset.update(moderation_status=Review.STATUS_APPROVED)

    def reject_reviews(self, request, queryset):
        queryset.update(moderation_status=Review.STATUS_REJECTED)
