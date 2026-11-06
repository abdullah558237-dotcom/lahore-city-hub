from django.contrib import admin
from .models import EducationType, AccreditationBoard, Institution

@admin.register(EducationType)
class EducationTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}

@admin.register(AccreditationBoard)
class AccreditationBoardAdmin(admin.ModelAdmin):
    list_display = ('name', 'abbreviation', 'website')

@admin.register(Institution)
class InstitutionAdmin(admin.ModelAdmin):
    list_display = ('title', 'education_type', 'locality', 'established_year', 'verification_status', 'is_active')
    list_filter = ('education_type', 'gender_policy', 'verification_status', 'is_active', 'locality')
    search_fields = ('title', 'summary', 'address')
    prepopulated_fields = {'slug': ('title',)}
    filter_horizontal = ('accreditations',)
