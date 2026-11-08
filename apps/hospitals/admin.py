from django.contrib import admin
from django.utils import timezone
from .models import MedicalSpecialty, Hospital


@admin.register(MedicalSpecialty)
class MedicalSpecialtyAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'is_active', 'hospitals_count', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at', 'updated_at')
    actions = ['make_active', 'make_inactive']

    def hospitals_count(self, obj):
        return obj.hospitals.count()
    hospitals_count.short_description = 'Hospitals / Clinics'

    def make_active(self, request, queryset):
        queryset.update(is_active=True)
    make_active.short_description = "Mark selected specialties as Active"

    def make_inactive(self, request, queryset):
        queryset.update(is_active=False)
    make_inactive.short_description = "Mark selected specialties as Inactive"


@admin.register(Hospital)
class HospitalAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'hospital_type',
        'locality',
        'is_24_7_emergency',
        'emergency_phone_display',
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
        'hospital_type',
        'is_24_7_emergency',
        'has_trauma_center',
        'has_blood_bank',
        'has_24_7_pharmacy',
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
        'phone_number',
        'emergency_phone',
        'ambulance_direct_phone',
        'source_url',
    )
    date_hierarchy = 'created_at'
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ('created_at', 'updated_at', 'last_verified_at', 'verified_by', 'view_count')
    filter_horizontal = ('specialties',)
    actions = ['make_verified', 'make_featured', 'unfeature', 'publish', 'unpublish']

    fieldsets = (
        ('Facility Identity & Classification', {
            'fields': ('title', 'title_ur', 'slug', 'hospital_type', 'summary', 'description')
        }),
        ('Location & Spatial Data', {
            'fields': (
                'locality',
                'address',
                'landmark',
                'latitude',
                'longitude',
                'google_maps_url'
            )
        }),
        ('Clinical Infrastructure & Specialties', {
            'fields': (
                'specialties',
                'bed_capacity',
                'has_trauma_center',
                'has_blood_bank',
                'has_24_7_pharmacy'
            )
        }),
        ('Verified Emergency Operations & Ambulance', {
            'fields': (
                'is_24_7_emergency',
                'emergency_phone',
                'ambulance_direct_phone',
                'emergency_notes'
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
        ('Verification, Governance & Registry Source', {
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

    def emergency_phone_display(self, obj):
        return obj.ambulance_direct_phone or obj.emergency_phone or obj.phone_number or "—"
    emergency_phone_display.short_description = 'Emergency Phone'

    def has_delete_permission(self, request, obj=None):
        """Only administrators can delete healthcare facilities."""
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
            self.message_user(request, f"{updated} facility/facilities marked as verified with timestamp.")
    make_verified.short_description = "Mark selected facilities as Verified Record"

    def make_featured(self, request, queryset):
        updated = queryset.update(is_featured=True)
        if request:
            self.message_user(request, f"{updated} facility/facilities marked as featured.")
    make_featured.short_description = "Feature on Homepage & Spotlight"

    def unfeature(self, request, queryset):
        updated = queryset.update(is_featured=False)
        if request:
            self.message_user(request, f"{updated} facility/facilities unfeatured.")
    unfeature.short_description = "Remove from Featured Spotlight"

    def publish(self, request, queryset):
        updated = queryset.update(is_active=True)
        if request:
            self.message_user(request, f"{updated} facility/facilities published.")
    publish.short_description = "Publish selected facilities (Set Active)"

    def unpublish(self, request, queryset):
        updated = queryset.update(is_active=False)
        if request:
            self.message_user(request, f"{updated} facility/facilities unpublished.")
    unpublish.short_description = "Unpublish selected facilities (Hide from public)"
