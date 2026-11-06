from django.db import models
from django.core.exceptions import ValidationError
from apps.core.models import ListingBase, TimeStampedModel

class MedicalSpecialty(TimeStampedModel):
    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=150, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        verbose_name = "Medical Specialty"
        verbose_name_plural = "Medical Specialties"
        ordering = ['name']

    def __str__(self):
        return self.name


class Hospital(ListingBase):
    HOSPITAL_TYPES = [
        ('public', 'Public Government Hospital'),
        ('private', 'Private Multi-Specialty Hospital'),
        ('trust', 'Charitable / Trust Hospital'),
    ]

    hospital_type = models.CharField(max_length=20, choices=HOSPITAL_TYPES, default='private')
    specialties = models.ManyToManyField(MedicalSpecialty, related_name='hospitals', blank=True)
    is_24_7_emergency = models.BooleanField(default=True, db_index=True, verbose_name="24/7 Emergency Care")
    has_trauma_center = models.BooleanField(default=False, verbose_name="Level-1 Trauma Center")
    has_blood_bank = models.BooleanField(default=False, verbose_name="On-site Blood Bank")
    has_24_7_pharmacy = models.BooleanField(default=True, verbose_name="24/7 Pharmacy")
    bed_capacity = models.PositiveIntegerField(null=True, blank=True)
    ambulance_direct_phone = models.CharField(max_length=35, blank=True)

    class Meta:
        verbose_name = "Hospital & Medical Facility"
        verbose_name_plural = "Hospitals & Medical Facilities"
        ordering = ['-is_featured', 'title']
        indexes = [
            models.Index(fields=['is_active', 'locality']),
            models.Index(fields=['is_active', 'is_24_7_emergency']),
            models.Index(fields=['is_active', 'hospital_type']),
            models.Index(fields=['is_featured', 'is_active']),
        ]

    def clean(self):
        super().clean()
        if self.bed_capacity is not None and self.bed_capacity < 0:
            raise ValidationError({'bed_capacity': 'Bed capacity cannot be negative.'})
