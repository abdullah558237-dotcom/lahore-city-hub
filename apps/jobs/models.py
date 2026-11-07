from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError
from apps.core.models import TimeStampedModel, SEOModel, Locality


class JobCategory(TimeStampedModel):
    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=150, unique=True)
    icon_class = models.CharField(max_length=60, default="bi-briefcase")
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        verbose_name = "Job Category"
        verbose_name_plural = "Job Categories"
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return f"{reverse('jobs:list')}?category={self.slug}"


class Employer(TimeStampedModel):
    name = models.CharField(max_length=200, unique=True)
    slug = models.SlugField(max_length=220, unique=True)
    logo = models.ImageField(upload_to='employers/logos/', blank=True, null=True)
    website = models.URLField(blank=True)
    locality = models.ForeignKey(Locality, on_delete=models.PROTECT, related_name='employers')
    address = models.CharField(max_length=300)
    is_verified = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Employer"
        verbose_name_plural = "Employers"
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return f"{reverse('jobs:list')}?employer={self.slug}"

    def clean(self):
        super().clean()
        if self.website:
            url_validator = URLValidator(schemes=['http', 'https'])
            try:
                url_validator(self.website)
            except ValidationError:
                raise ValidationError({'website': 'Enter a valid website URL starting with http:// or https://.'})


class JobListing(TimeStampedModel, SEOModel):
    EMPLOYMENT_TYPES = [
        ('full_time', 'Full-Time'),
        ('part_time', 'Part-Time'),
        ('contract', 'Contract'),
        ('internship', 'Internship'),
    ]

    EXPERIENCE_LEVELS = [
        ('entry', 'Entry Level (0-1 yrs)'),
        ('mid', 'Mid Level (2-4 yrs)'),
        ('senior', 'Senior Level (5+ yrs)'),
        ('lead', 'Lead / Executive'),
    ]

    VERIFICATION_STATUS_CHOICES = [
        ('pending', 'Pending Verification'),
        ('verified', 'Verified Legitimate'),
        ('flagged', 'Flagged / Suspicious'),
    ]

    title = models.CharField(max_length=200, db_index=True)
    slug = models.SlugField(max_length=250, unique=True)
    employer = models.ForeignKey(Employer, on_delete=models.CASCADE, related_name='jobs')
    category = models.ForeignKey(JobCategory, on_delete=models.PROTECT, related_name='jobs')
    locality = models.ForeignKey(Locality, on_delete=models.PROTECT, related_name='jobs')
    employment_type = models.CharField(max_length=20, choices=EMPLOYMENT_TYPES, default='full_time')
    experience_level = models.CharField(max_length=20, choices=EXPERIENCE_LEVELS, default='mid')
    salary_min_pkr = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    salary_max_pkr = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    is_salary_negotiable = models.BooleanField(default=True)
    description = models.TextField()
    requirements = models.TextField(blank=True, verbose_name="Requirements & Skills")
    qualifications = models.TextField(blank=True, verbose_name="Qualifications & Education")
    application_instructions = models.TextField(blank=True, verbose_name="Application Instructions")
    application_url = models.URLField(max_length=500, blank=True)
    application_email = models.EmailField(blank=True)
    source_url = models.URLField(max_length=500, blank=True, verbose_name="Source URL")
    deadline = models.DateField(db_index=True)
    is_active = models.BooleanField(default=True, db_index=True)
    is_featured = models.BooleanField(default=False, db_index=True)
    verification_status = models.CharField(
        max_length=20,
        choices=VERIFICATION_STATUS_CHOICES,
        default='pending',
        db_index=True
    )

    class Meta:
        verbose_name = "Job Listing"
        verbose_name_plural = "Job Listings"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['is_active', 'deadline']),
            models.Index(fields=['is_active', 'locality']),
            models.Index(fields=['is_active', 'category']),
            models.Index(fields=['is_featured', 'is_active']),
        ]

    def __str__(self):
        return f"{self.title} at {self.employer.name}"

    def get_absolute_url(self):
        return reverse('jobs:detail', kwargs={'slug': self.slug})

    @property
    def is_verified(self):
        return self.verification_status == 'verified' or (self.employer and self.employer.is_verified)

    @property
    def is_expired(self):
        if not self.deadline:
            return False
        return self.deadline < timezone.now().date()

    @property
    def days_remaining(self):
        if not self.deadline:
            return None
        delta = (self.deadline - timezone.now().date()).days
        return max(delta, 0)

    @property
    def publication_date(self):
        return self.created_at.date() if self.created_at else None

    @property
    def salary_display(self):
        if self.salary_min_pkr and self.salary_max_pkr:
            return f"PKR {self.salary_min_pkr:,.0f} – {self.salary_max_pkr:,.0f}"
        elif self.salary_min_pkr:
            return f"From PKR {self.salary_min_pkr:,.0f}"
        return "Market Competitive"

    @property
    def salary_range(self):
        return self.salary_display

    @property
    def summary(self):
        return self.description[:120] if self.description else ""

    @property
    def apply_url(self):
        if self.application_url:
            return self.application_url
        elif self.application_email:
            return f"mailto:{self.application_email}?subject=Application for {self.title}"
        return "#"

    def clean(self):
        super().clean()
        url_validator = URLValidator(schemes=['http', 'https'])
        if self.application_url:
            try:
                url_validator(self.application_url)
            except ValidationError:
                raise ValidationError({'application_url': 'Enter a valid application URL starting with http:// or https://.'})

        if self.source_url:
            try:
                url_validator(self.source_url)
            except ValidationError:
                raise ValidationError({'source_url': 'Enter a valid source URL starting with http:// or https://.'})

        if self.salary_min_pkr is not None and self.salary_min_pkr < 0:
            raise ValidationError({'salary_min_pkr': 'Minimum salary cannot be negative.'})
        if self.salary_max_pkr is not None and self.salary_max_pkr < 0:
            raise ValidationError({'salary_max_pkr': 'Maximum salary cannot be negative.'})
        if self.salary_min_pkr is not None and self.salary_max_pkr is not None:
            if self.salary_min_pkr > self.salary_max_pkr:
                raise ValidationError({'salary_min_pkr': 'Minimum salary cannot exceed maximum salary.'})

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(f"{self.title}-{self.employer.name}") or "job"
            slug = base_slug
            counter = 1
            while JobListing.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)
