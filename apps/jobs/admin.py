from datetime import timedelta
from django.contrib import admin
from django.utils import timezone
from .models import JobCategory, Employer, JobListing


@admin.register(JobCategory)
class JobCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'icon_class', 'is_active', 'jobs_count', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at', 'updated_at')
    actions = ['make_active', 'make_inactive']

    def jobs_count(self, obj):
        return obj.jobs.count()
    jobs_count.short_description = 'Total Jobs'

    def make_active(self, request, queryset):
        queryset.update(is_active=True)
    make_active.short_description = "Mark selected categories as Active"

    def make_inactive(self, request, queryset):
        queryset.update(is_active=False)
    make_inactive.short_description = "Mark selected categories as Inactive"


@admin.register(Employer)
class EmployerAdmin(admin.ModelAdmin):
    list_display = ('name', 'locality', 'website', 'is_verified', 'jobs_count', 'created_at')
    list_filter = ('is_verified', 'locality__zone', 'locality', 'created_at')
    search_fields = ('name', 'address', 'website')
    prepopulated_fields = {'slug': ('name',)}
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at', 'updated_at')
    actions = ['mark_as_verified', 'unmark_verified']

    def jobs_count(self, obj):
        return obj.jobs.count()
    jobs_count.short_description = 'Active Postings'

    def mark_as_verified(self, request, queryset):
        updated = queryset.update(is_verified=True)
        if request:
            self.message_user(request, f"{updated} employer(s) successfully marked as verified.")
    mark_as_verified.short_description = "Mark selected employers as Verified"

    def unmark_verified(self, request, queryset):
        updated = queryset.update(is_verified=False)
        if request:
            self.message_user(request, f"{updated} employer(s) unmarked from verified.")
    unmark_verified.short_description = "Remove verified status from selected employers"


@admin.register(JobListing)
class JobListingAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'employer',
        'category',
        'locality',
        'employment_type',
        'deadline',
        'deadline_status',
        'verification_status',
        'is_featured',
        'is_active',
        'created_at',
    )
    list_filter = (
        'is_active',
        'verification_status',
        'is_featured',
        'employment_type',
        'experience_level',
        'category',
        'locality__zone',
        'created_at',
        'deadline',
    )
    search_fields = (
        'title',
        'employer__name',
        'description',
        'requirements',
        'qualifications',
        'source_url',
    )
    date_hierarchy = 'created_at'
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ('created_at', 'updated_at')
    actions = [
        'mark_verified',
        'mark_flagged',
        'publish_jobs',
        'unpublish_jobs',
        'mark_as_featured',
        'unmark_featured',
        'extend_deadline_30_days',
    ]

    fieldsets = (
        ('Job Title & Classification', {
            'fields': ('title', 'slug', 'employer', 'category')
        }),
        ('Location & Employment Specs', {
            'fields': ('locality', 'employment_type', 'experience_level')
        }),
        ('Role Description & Requirements', {
            'fields': ('description', 'requirements', 'qualifications')
        }),
        ('Compensation Structure', {
            'fields': ('salary_min_pkr', 'salary_max_pkr', 'is_salary_negotiable')
        }),
        ('Application Channels & Source Verification', {
            'fields': (
                'application_url',
                'application_email',
                'application_instructions',
                'source_url',
                'deadline'
            )
        }),
        ('Moderation & Publishing Status', {
            'fields': (
                'verification_status',
                'is_active',
                'is_featured'
            )
        }),
        ('SEO Metadata', {
            'classes': ('collapse',),
            'fields': ('meta_title', 'meta_description', 'canonical_url')
        }),
    )

    def deadline_status(self, obj):
        if obj.is_expired:
            return "Expired"
        days = obj.days_remaining
        if days == 0:
            return "Closes Today"
        elif days <= 3:
            return f"Urgent ({days}d left)"
        return f"Active ({days}d left)"
    deadline_status.short_description = 'Deadline Status'

    def has_delete_permission(self, request, obj=None):
        """Only administrators can delete employment vacancies."""
        if request.user.is_superuser or getattr(request.user, 'role', '') == 'admin':
            return True
        return False

    def mark_verified(self, request, queryset):
        updated = queryset.update(verification_status='verified')
        if request:
            self.message_user(request, f"{updated} job(s) marked as verified.")
    mark_verified.short_description = "Mark selected jobs as Verified"

    def mark_flagged(self, request, queryset):
        updated = queryset.update(verification_status='flagged')
        if request:
            self.message_user(request, f"{updated} job(s) flagged for review.")
    mark_flagged.short_description = "Flag selected jobs as Suspicious"

    def publish_jobs(self, request, queryset):
        updated = queryset.update(is_active=True)
        if request:
            self.message_user(request, f"{updated} job(s) published.")
    publish_jobs.short_description = "Publish selected jobs (Set Active)"

    def unpublish_jobs(self, request, queryset):
        updated = queryset.update(is_active=False)
        if request:
            self.message_user(request, f"{updated} job(s) unpublished.")
    unpublish_jobs.short_description = "Unpublish selected jobs (Hide from public)"

    def mark_as_featured(self, request, queryset):
        updated = queryset.update(is_featured=True)
        if request:
            self.message_user(request, f"{updated} job(s) marked as featured.")
    mark_as_featured.short_description = "Mark selected jobs as Featured"

    def unmark_featured(self, request, queryset):
        updated = queryset.update(is_featured=False)
        if request:
            self.message_user(request, f"{updated} job(s) removed from featured.")
    unmark_featured.short_description = "Remove from Featured Spotlight"

    def extend_deadline_30_days(self, request, queryset):
        count = 0
        for job in queryset:
            base_date = max(job.deadline or timezone.now().date(), timezone.now().date())
            job.deadline = base_date + timedelta(days=30)
            job.save(update_fields=['deadline'])
            count += 1
        if request:
            self.message_user(request, f"Extended deadline by 30 days for {count} job(s).")
    extend_deadline_30_days.short_description = "Extend deadline by 30 days"
