from django.contrib import admin
from django.utils import timezone
from .models import EducationType, AccreditationBoard, Institution


@admin.register(EducationType)
class EducationTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'icon_class', 'is_active', 'institutions_count')
    list_filter = ('is_active',)
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}

    def institutions_count(self, obj):
        return obj.institutions.count()
    institutions_count.short_description = 'Institutions'


@admin.register(AccreditationBoard)
class AccreditationBoardAdmin(admin.ModelAdmin):
    list_display = ('name', 'abbreviation', 'website', 'is_active', 'institutions_count')
    list_filter = ('is_active',)
    search_fields = ('name', 'abbreviation')

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
        'view_count'
    )
    list_filter = (
        'is_active',
        'is_featured',
        'verification_status',
        'education_type',
        'gender_policy',
        'accreditations',
        'locality__zone'
    )
    search_fields = (
        'title',
        'title_ur',
        'address',
        'summary',
        'description',
        'programs_offered',
        'admission_info'
    )
    prepopulated_fields = {'slug': ('title',)}
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
        ('SEO Metadata', {
            'classes': ('collapse',),
            'fields': ('meta_title', 'meta_description', 'canonical_url')
        }),
    )

    def make_verified(self, request, queryset):
        updated = queryset.update(verification_status='verified', last_verified_at=timezone.now())
        if request:
            self.message_user(request, f"{updated} institution(s) marked as verified.")
    make_verified.short_description = "Mark selected institutions as Verified"

    def make_featured(self, request, queryset):
        updated = queryset.update(is_featured=True)
        if request:
            self.message_user(request, f"{updated} institution(s) marked as featured.")
    make_featured.short_description = "Mark selected institutions as Featured"

    def unfeature(self, request, queryset):
        updated = queryset.update(is_featured=False)
        if request:
            self.message_user(request, f"{updated} institution(s) unfeatured.")
    unfeature.short_description = "Remove featured status from selected institutions"

    def publish(self, request, queryset):
        updated = queryset.update(is_active=True)
        if request:
            self.message_user(request, f"{updated} institution(s) published.")
    publish.short_description = "Publish selected institutions"

    def unpublish(self, request, queryset):
        updated = queryset.update(is_active=False)
        if request:
            self.message_user(request, f"{updated} institution(s) unpublished.")
    unpublish.short_description = "Unpublish selected institutions"
