from django.contrib import admin
from django.utils import timezone
from datetime import timedelta
from .models import (
    BusinessCategory,
    Business,
    BusinessClaim,
    BusinessEditRequest,
    BusinessReport,
    BusinessPromotionRequest,
)


@admin.register(BusinessCategory)
class BusinessCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'icon_class', 'is_active', 'businesses_count', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at', 'updated_at')
    actions = ['make_active', 'make_inactive']

    def businesses_count(self, obj):
        return obj.businesses.count()
    businesses_count.short_description = 'Businesses'

    def make_active(self, request, queryset):
        queryset.update(is_active=True)
    make_active.short_description = "Mark selected categories as Active"

    def make_inactive(self, request, queryset):
        queryset.update(is_active=False)
    make_inactive.short_description = "Mark selected categories as Inactive"


@admin.register(Business)
class BusinessAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'category',
        'locality',
        'claimed_by',
        'submitted_by',
        'verification_status',
        'promotion_tier',
        'is_featured',
        'is_active',
        'last_verified_at',
        'view_count',
        'created_at',
    )
    list_filter = (
        'is_active',
        'verification_status',
        'promotion_tier',
        'is_featured',
        'category',
        'locality__zone',
        'locality',
        'created_at',
    )
    search_fields = (
        'title',
        'title_ur',
        'summary',
        'description',
        'address',
        'registration_number',
        'phone_number',
        'source_url',
    )
    date_hierarchy = 'created_at'
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ('created_at', 'updated_at', 'last_verified_at', 'verified_by', 'view_count')
    actions = [
        'approve_and_publish',
        'unpublish',
        'set_as_featured_spotlight_30',
        'set_as_verified_pro',
        'demote_to_standard',
        'extend_spotlight_30',
        'mark_as_verified',
    ]

    fieldsets = (
        ('Core Identification', {
            'fields': ('title', 'title_ur', 'slug', 'category', 'primary_image')
        }),
        ('Editorial Details', {
            'fields': ('summary', 'description', 'operating_hours', 'registration_number')
        }),
        ('Location & Coordinates', {
            'fields': ('locality', 'address', 'landmark', 'latitude', 'longitude', 'google_maps_url')
        }),
        ('Contact & Connectivity', {
            'fields': ('phone_number', 'emergency_phone', 'email', 'website', 'whatsapp_number')
        }),
        ('Publication & Moderation', {
            'fields': (
                'is_active',
                'verification_status',
                'promotion_tier',
                'promotion_notes',
                'is_featured',
                'featured_until',
                'claimed_by',
                'submitted_by',
                'verified_by',
                'last_verified_at',
                'source_url',
                'verification_notes',
            )
        }),
        ('Traffic & SEO Metadata', {
            'fields': ('view_count', 'meta_title', 'meta_description', 'canonical_url', 'og_image'),
            'classes': ('collapse',),
        }),
    )

    def has_delete_permission(self, request, obj=None):
        """Only administrators can delete registered local businesses."""
        if request.user.is_superuser or getattr(request.user, 'role', '') == 'admin':
            return True
        return False

    def approve_and_publish(self, request, queryset):
        count = 0
        now = timezone.now()
        for biz in queryset:
            biz.is_active = True
            biz.last_verified_at = now
            if biz.verification_status == 'pending':
                biz.verification_status = 'verified'
            if request and hasattr(request, 'user') and request.user.is_authenticated:
                biz.verified_by = request.user
            biz.save()
            count += 1
        if request:
            self.message_user(request, f"{count} business listing(s) successfully approved and published.")
    approve_and_publish.short_description = "Approve & Publish selected businesses (Set Active & Verified)"

    def unpublish(self, request, queryset):
        count = queryset.update(is_active=False)
        if request:
            self.message_user(request, f"{count} business listing(s) unpublished.")
    unpublish.short_description = "Unpublish selected businesses (Set Inactive)"

    def mark_as_verified(self, request, queryset):
        now = timezone.now()
        user = request.user if request and hasattr(request, 'user') and request.user.is_authenticated else None
        count = queryset.update(verification_status='verified', last_verified_at=now, verified_by=user)
        if request:
            self.message_user(request, f"{count} business listing(s) marked as Verified.")
    mark_as_verified.short_description = "Mark selected businesses as Verified"

    def set_as_featured_spotlight_30(self, request, queryset):
        now = timezone.now()
        count = 0
        for biz in queryset:
            biz.is_featured = True
            biz.promotion_tier = Business.PROMOTION_TIER_FEATURED
            biz.featured_until = now + timedelta(days=30)
            biz.promotion_notes = f"Activated by Admin on {now.strftime('%Y-%m-%d')} for 30 days."
            biz.save()
            count += 1
        if request:
            self.message_user(request, f"{count} business(es) set to Featured Spotlight (30 Days active).")
    set_as_featured_spotlight_30.short_description = "⭐ Set to Featured Spotlight (30 Days)"

    def set_as_verified_pro(self, request, queryset):
        now = timezone.now()
        user = request.user if request and hasattr(request, 'user') and request.user.is_authenticated else None
        count = queryset.update(
            promotion_tier=Business.PROMOTION_TIER_VERIFIED_PRO,
            verification_status='verified',
            last_verified_at=now,
            verified_by=user,
            is_featured=False
        )
        if request:
            self.message_user(request, f"{count} business(es) set to Verified Professional tier.")
    set_as_verified_pro.short_description = "🛡️ Set to Verified Professional tier"

    def demote_to_standard(self, request, queryset):
        count = queryset.update(
            promotion_tier=Business.PROMOTION_TIER_STANDARD,
            is_featured=False,
            featured_until=None
        )
        if request:
            self.message_user(request, f"{count} business(es) returned to Standard Organic (Free).")
    demote_to_standard.short_description = "⬇️ Demote to Standard Organic (Remove Promotion)"

    def extend_spotlight_30(self, request, queryset):
        now = timezone.now()
        count = 0
        for biz in queryset.filter(is_featured=True):
            base_date = biz.featured_until if biz.featured_until and biz.featured_until > now else now
            biz.featured_until = base_date + timedelta(days=30)
            biz.save()
            count += 1
        if request:
            self.message_user(request, f"{count} active spotlight(s) extended by 30 days.")
    extend_spotlight_30.short_description = "➕ Extend Active Spotlight by 30 Days"


@admin.register(BusinessEditRequest)
class BusinessEditRequestAdmin(admin.ModelAdmin):
    list_display = ('business', 'requested_by', 'title', 'status', 'created_at', 'reviewed_by', 'reviewed_at')
    list_filter = ('status', 'created_at')
    search_fields = ('business__title', 'title', 'requested_by__email', 'address')
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at', 'updated_at', 'reviewed_at', 'reviewed_by')
    actions = ['approve_and_merge', 'reject_request']

    def approve_and_merge(self, request, queryset):
        now = timezone.now()
        count = 0
        for req in queryset.filter(status='pending'):
            biz = req.business
            biz.title = req.title
            if req.summary:
                biz.summary = req.summary
            if req.description:
                biz.description = req.description
            if req.address:
                biz.address = req.address
            if req.phone_number:
                biz.phone_number = req.phone_number
            if req.website:
                biz.website = req.website
            if req.operating_hours:
                biz.operating_hours = req.operating_hours
            biz.save()

            req.status = 'approved'
            req.reviewed_by = request.user if request and hasattr(request, 'user') else None
            req.reviewed_at = now
            req.save()
            count += 1
        if request:
            self.message_user(request, f"{count} edit request(s) approved and merged into live business records.")
    approve_and_merge.short_description = "Approve & Merge changes into Business"

    def reject_request(self, request, queryset):
        now = timezone.now()
        user = request.user if request and hasattr(request, 'user') else None
        count = queryset.filter(status='pending').update(status='rejected', reviewed_by=user, reviewed_at=now)
        if request:
            self.message_user(request, f"{count} edit request(s) rejected.")
    reject_request.short_description = "Reject selected edit requests"


@admin.register(BusinessReport)
class BusinessReportAdmin(admin.ModelAdmin):
    list_display = ('business', 'reason', 'reporter_name', 'reporter_email', 'status', 'created_at', 'resolved_by', 'resolved_at')
    list_filter = ('status', 'reason', 'created_at')
    search_fields = ('business__title', 'reporter_name', 'reporter_email', 'details')
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at', 'updated_at', 'resolved_at', 'resolved_by')
    actions = ['mark_resolved', 'dismiss_report']

    def mark_resolved(self, request, queryset):
        now = timezone.now()
        user = request.user if request and hasattr(request, 'user') else None
        count = queryset.filter(status='pending').update(status='resolved', resolved_by=user, resolved_at=now)
        if request:
            self.message_user(request, f"{count} report(s) marked as Resolved.")
    mark_resolved.short_description = "Mark selected reports as Resolved"

    def dismiss_report(self, request, queryset):
        now = timezone.now()
        user = request.user if request and hasattr(request, 'user') else None
        count = queryset.filter(status='pending').update(status='dismissed', resolved_by=user, resolved_at=now)
        if request:
            self.message_user(request, f"{count} report(s) dismissed.")
    dismiss_report.short_description = "Dismiss selected reports"


@admin.register(BusinessClaim)
class BusinessClaimAdmin(admin.ModelAdmin):
    list_display = ('business', 'claimant', 'claimant_role', 'official_email', 'status', 'created_at', 'reviewed_by')
    list_filter = ('status', 'created_at')
    search_fields = ('business__title', 'claimant__email', 'official_email', 'contact_phone')
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at', 'updated_at', 'reviewed_at', 'reviewed_by')
    actions = ['approve_claim', 'reject_claim']

    def approve_claim(self, request, queryset):
        now = timezone.now()
        count = 0
        for claim in queryset.filter(status='pending'):
            biz = claim.business
            biz.claimed_by = claim.claimant
            biz.verification_status = 'claimed'
            biz.last_verified_at = now
            if request and hasattr(request, 'user') and request.user.is_authenticated:
                biz.verified_by = request.user
            biz.save()

            claim.status = 'approved'
            claim.reviewed_by = request.user if request and hasattr(request, 'user') else None
            claim.reviewed_at = now
            claim.save()
            count += 1
        if request:
            self.message_user(request, f"{count} ownership claim(s) approved and business assigned to claimant.")
    approve_claim.short_description = "Approve Ownership Claim (Assign Business)"

    def reject_claim(self, request, queryset):
        now = timezone.now()
        user = request.user if request and hasattr(request, 'user') else None
        count = queryset.filter(status='pending').update(status='rejected', reviewed_by=user, reviewed_at=now)
        if request:
            self.message_user(request, f"{count} claim(s) rejected.")
    reject_claim.short_description = "Reject selected claims"


@admin.register(BusinessPromotionRequest)
class BusinessPromotionRequestAdmin(admin.ModelAdmin):
    list_display = (
        'business',
        'target_tier',
        'duration_days',
        'requested_by',
        'contact_phone',
        'status',
        'created_at',
        'reviewed_by',
        'reviewed_at',
    )
    list_filter = ('status', 'target_tier', 'duration_days', 'created_at')
    search_fields = (
        'business__title',
        'requested_by__email',
        'contact_phone',
        'contact_email',
        'campaign_goals',
        'admin_notes',
    )
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at', 'updated_at', 'reviewed_at', 'reviewed_by')
    actions = ['approve_and_activate', 'decline_request']

    def approve_and_activate(self, request, queryset):
        now = timezone.now()
        count = 0
        for promo in queryset.filter(status='pending'):
            biz = promo.business
            biz.promotion_tier = promo.target_tier
            if promo.target_tier == Business.PROMOTION_TIER_FEATURED:
                biz.is_featured = True
                biz.featured_until = now + timedelta(days=promo.duration_days)
            elif promo.target_tier == Business.PROMOTION_TIER_VERIFIED_PRO:
                if biz.verification_status == 'unverified':
                    biz.verification_status = 'verified'
                    biz.last_verified_at = now
            biz.promotion_notes = f"Activated tier {promo.target_tier} for {promo.duration_days} days on {now.strftime('%Y-%m-%d')}."
            biz.save()

            promo.status = 'approved'
            promo.reviewed_by = request.user if request and hasattr(request, 'user') else None
            promo.reviewed_at = now
            promo.admin_notes = f"Approved and activated by admin on {now.strftime('%Y-%m-%d %H:%M')}."
            promo.save()
            count += 1
        if request:
            self.message_user(request, f"{count} promotion request(s) approved and active tier applied to listings.")
    approve_and_activate.short_description = "Approve & Activate Promotion Campaign"

    def decline_request(self, request, queryset):
        now = timezone.now()
        user = request.user if request and hasattr(request, 'user') else None
        count = queryset.filter(status='pending').update(
            status='rejected',
            reviewed_by=user,
            reviewed_at=now,
            admin_notes="Declined during editorial review."
        )
        if request:
            self.message_user(request, f"{count} promotion request(s) declined.")
    decline_request.short_description = "Decline selected promotion requests"

