from django.contrib import admin
from django.utils import timezone
from .models import EducationType, AccreditationBoard, Institution


@admin.register(EducationType)
class EducationTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'icon_class', 'is_active', 'institutions_count', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at', 'updated_at')
    actions = ['make_active', 'make_inactive']

    def institutions_count(self, obj):
        return obj.institutions.count()
    institutions_count.short_description = 'Institutions'

    def make_active(self, request, queryset):
        queryset.update(is_active=True)
    make_active.short_description = "Mark selected types as Active"

    def make_inactive(self, request, queryset):
        queryset.update(is_active=False)
    make_inactive.short_description = "Mark selected types as Inactive"


@admin.register(AccreditationBoard)
class AccreditationBoardAdmin(admin.ModelAdmin):
    list_display = ('name', 'abbreviation', 'website', 'is_active', 'institutions_count', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'abbreviation', 'website')
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at', 'updated_at')

    def institutions_count(self, obj):
        return obj.institutions.count()
    institutions_count.short_description = 'Accredited Institutions'


@admin.register(Institution)
class InstitutionAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'education_type',
        'locality',
        'gender_policy',
        'established_year',
        'verification_status',
        'is_featured',
        'is_active',
        'last_verified_at',
        'view_count',
        'created_at',
    )
    list_filter = (
        'is_active',
        'is_featured',
        'verification_status',
        'education_type',
        'gender_policy',
        'accreditations',
        'locality__zone',
        'locality',
        'created_at',
    )
    search_fields = (
        'title',
        'title_ur',
        'address',
        'summary',
        'description',
        'programs_offered',
        'admission_info',
        'source_url',
    )
    date_hierarchy = 'created_at'
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ('created_at', 'updated_at', 'last_verified_at', 'verified_by', 'view_count')
    filter_horizontal = ('accreditations',)
    actions = ['make_verified', 'make_featured', 'unfeature', 'publish', 'unpublish']

    fieldsets = (
        ('Institution Identity & Classification', {
            'fields': ('title', 'title_ur', 'slug', 'education_type', 'summary', 'description')
        }),
        ('Campus Location & Transit', {
            'fields': (
                'locality',
                'address',
                'landmark',
                'latitude',
                'longitude',
                'google_maps_url'
            )
        }),
        ('Academic Programs & Accreditations', {
            'fields': (
                'programs_offered',
                'accreditations',
                'gender_policy',
                'established_year'
            )
        }),
        ('Admissions & Prospectus Guidance', {
            'fields': (
                'admission_info',
                'admission_cycles',
                'admission_url',
                'prospectus_url'
            )
        }),
        ('Official Contacts & Web Endpoints', {
            'fields': (
                'phone_number',
                'email',
                'website',
                'whatsapp_number'
            )
        }),
        ('Media & Imagery', {
            'fields': ('primary_image',)
        }),
        ('Verification, Governance & Audit Trail', {
            'fields': (
                'verification_status',
                'last_verified_at',
                'verified_by',
                'verification_notes',
                'source_url',
                'is_featured',
                'featured_until',
                'is_active'
            )
        }),
        ('Traffic & SEO Metadata', {
            'classes': ('collapse',),
            'fields': ('view_count', 'meta_title', 'meta_description', 'canonical_url', 'og_image')
        }),
    )

    def has_delete_permission(self, request, obj=None):
        """Only administrators can delete educational institutions."""
        if request.user.is_superuser or getattr(request.user, 'role', '') == 'admin':
            return True
        return False

    def make_verified(self, request, queryset):
        now = timezone.now()
        user = request.user if request and hasattr(request, 'user') and request.user.is_authenticated else None
        updated = queryset.update(
            verification_status='verified',
            verified_by=user,
            last_verified_at=now
        )
        if request:
            self.message_user(request, f"{updated} institution(s) marked as officially verified.")
    make_verified.short_description = "Mark selected institutions as Verified Record"

    def make_featured(self, request, queryset):
        updated = queryset.update(is_featured=True)
        if request:
            self.message_user(request, f"{updated} institution(s) marked as featured.")
    make_featured.short_description = "Feature on Homepage & Spotlight"

    def unfeature(self, request, queryset):
        updated = queryset.update(is_featured=False)
        if request:
            self.message_user(request, f"{updated} institution(s) unfeatured.")
    unfeature.short_description = "Remove from Featured Spotlight"

    def publish(self, request, queryset):
        updated = queryset.update(is_active=True)
        if request:
            self.message_user(request, f"{updated} institution(s) published.")
    publish.short_description = "Publish selected institutions (Set Active)"

    def unpublish(self, request, queryset):
        updated = queryset.update(is_active=False)
        if request:
            self.message_user(request, f"{updated} institution(s) unpublished.")
    unpublish.short_description = "Unpublish selected institutions (Hide from public)"
