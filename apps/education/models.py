from django.db import models
from django.core.exceptions import ValidationError
from apps.core.models import ListingBase, TimeStampedModel

class EducationType(TimeStampedModel):
    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=150, unique=True)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        verbose_name = "Education Type"
        verbose_name_plural = "Education Types"
        ordering = ['name']

    def __str__(self):
        return self.name


class AccreditationBoard(TimeStampedModel):
    name = models.CharField(max_length=150, unique=True)
    abbreviation = models.CharField(max_length=30)
    website = models.URLField(blank=True)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        verbose_name = "Accreditation Board"
        verbose_name_plural = "Accreditation Boards"
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.abbreviation})"


class Institution(ListingBase):
    GENDER_POLICIES = [
        ('coed', 'Co-Education'),
        ('girls', 'Female Students Only'),
        ('boys', 'Male Students Only'),
    ]

    education_type = models.ForeignKey(EducationType, on_delete=models.PROTECT, related_name='institutions')
    accreditations = models.ManyToManyField(AccreditationBoard, related_name='institutions', blank=True)
    gender_policy = models.CharField(max_length=20, choices=GENDER_POLICIES, default='coed')
    established_year = models.PositiveIntegerField(null=True, blank=True)
    admission_cycles = models.CharField(max_length=200, blank=True, verbose_name="Admission Windows")
    prospectus_url = models.URLField(max_length=500, blank=True)

    class Meta:
        verbose_name = "Educational Institution"
        verbose_name_plural = "Educational Institutions"
        ordering = ['-is_featured', 'title']
        indexes = [
            models.Index(fields=['is_active', 'locality']),
            models.Index(fields=['is_active', 'education_type']),
            models.Index(fields=['is_featured', 'is_active']),
        ]

    def clean(self):
        super().clean()
        if self.established_year is not None:
            if self.established_year < 1000 or self.established_year > 2100:
                raise ValidationError({'established_year': 'Established year must be a realistic calendar year (e.g., 1864).'})
