from django.contrib import admin
from .models import MedicalSpecialty, Hospital

@admin.register(MedicalSpecialty)
class MedicalSpecialtyAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Hospital)
class HospitalAdmin(admin.ModelAdmin):
    list_display = ('title', 'hospital_type', 'locality', 'is_24_7_emergency', 'has_trauma_center', 'verification_status', 'is_active')
    list_filter = ('hospital_type', 'is_24_7_emergency', 'has_trauma_center', 'has_blood_bank', 'verification_status', 'locality')
    search_fields = ('title', 'summary', 'address', 'ambulance_direct_phone')
    prepopulated_fields = {'slug': ('title',)}
    filter_horizontal = ('specialties',)
