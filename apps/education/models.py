from django.db import models
from django.urls import reverse
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from apps.core.models import ListingBase, TimeStampedModel


class EducationType(TimeStampedModel):
    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=150, unique=True)
    icon_class = models.CharField(max_length=60, default="bi-mortarboard")
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        verbose_name = "Education Type"
        verbose_name_plural = "Education Types"
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return f"{reverse('education:list')}?type={self.slug}"


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

    def clean(self):
        super().clean()
        if self.website:
            url_validator = URLValidator(schemes=['http', 'https'])
            try:
                url_validator(self.website)
            except ValidationError:
                raise ValidationError({'website': 'Enter a valid website URL starting with http:// or https://.'})


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
    programs_offered = models.TextField(blank=True, verbose_name="Academic Programs & Degrees")
    admission_info = models.TextField(blank=True, verbose_name="Admission Information & Criteria")
    admission_cycles = models.CharField(max_length=200, blank=True, verbose_name="Admission Windows")
    admission_url = models.URLField(max_length=500, blank=True, verbose_name="Official Admission Portal")
    prospectus_url = models.URLField(max_length=500, blank=True, verbose_name="Download Prospectus URL")

    class Meta:
        verbose_name = "Educational Institution"
        verbose_name_plural = "Educational Institutions"
        ordering = ['-is_featured', 'title']
        indexes = [
            models.Index(fields=['is_active', 'locality']),
            models.Index(fields=['is_active', 'education_type']),
            models.Index(fields=['is_featured', 'is_active']),
        ]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('education:detail', kwargs={'slug': self.slug})

    @property
    def last_verified_date(self):
        return self.last_verified_at.date() if self.last_verified_at else None

    def clean(self):
        super().clean()
        if self.established_year is not None:
            if self.established_year < 1000 or self.established_year > 2100:
                raise ValidationError({'established_year': 'Established year must be a realistic calendar year (e.g., 1864).'})

        url_validator = URLValidator(schemes=['http', 'https'])
        if self.website:
            try:
                url_validator(self.website)
            except ValidationError:
                raise ValidationError({'website': 'Enter a valid website URL starting with http:// or https://.'})

        if self.admission_url:
            try:
                url_validator(self.admission_url)
            except ValidationError:
                raise ValidationError({'admission_url': 'Enter a valid admission URL starting with http:// or https://.'})

        if self.prospectus_url:
            try:
                url_validator(self.prospectus_url)
            except ValidationError:
                raise ValidationError({'prospectus_url': 'Enter a valid prospectus URL starting with http:// or https://.'})

        if self.source_url:
            try:
                url_validator(self.source_url)
            except ValidationError:
                raise ValidationError({'source_url': 'Enter a valid source URL starting with http:// or https://.'})
