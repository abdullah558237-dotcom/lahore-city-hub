from django.contrib import admin
from .models import JobCategory, Employer, JobListing

@admin.register(JobCategory)
class JobCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'icon_class')
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Employer)
class EmployerAdmin(admin.ModelAdmin):
    list_display = ('name', 'locality', 'is_verified', 'created_at')
    list_filter = ('is_verified', 'locality')
    search_fields = ('name', 'address')
    prepopulated_fields = {'slug': ('name',)}

@admin.register(JobListing)
class JobListingAdmin(admin.ModelAdmin):
    list_display = ('title', 'employer', 'locality', 'employment_type', 'deadline', 'is_active')
    list_filter = ('employment_type', 'experience_level', 'is_active', 'locality', 'category')
    search_fields = ('title', 'description', 'employer__name')
    prepopulated_fields = {'slug': ('title',)}
