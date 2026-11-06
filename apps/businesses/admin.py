from django.contrib import admin
from .models import BusinessCategory, Business, BusinessClaim

@admin.register(BusinessCategory)
class BusinessCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'icon_class')
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Business)
class BusinessAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'locality', 'claimed_by', 'verification_status', 'is_featured', 'is_active')
    list_filter = ('category', 'verification_status', 'is_featured', 'is_active', 'locality')
    search_fields = ('title', 'summary', 'address')
    prepopulated_fields = {'slug': ('title',)}

@admin.register(BusinessClaim)
class BusinessClaimAdmin(admin.ModelAdmin):
    list_display = ('business', 'claimant', 'claimant_role', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('business__title', 'claimant__email', 'official_email')
    readonly_fields = ('created_at', 'updated_at')
