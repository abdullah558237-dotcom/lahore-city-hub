from django.db import models
from django.utils import timezone
from django.utils.text import slugify
from django.core.exceptions import ValidationError
from apps.core.models import TimeStampedModel, SEOModel

class UpdateCategory(TimeStampedModel):
    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=150, unique=True)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        verbose_name = "Update Category"
        verbose_name_plural = "Update Categories"
        ordering = ['name']

    def __str__(self):
        return self.name


class CityUpdate(TimeStampedModel, SEOModel):
    SEVERITY_LEVELS = [
        ('info', 'General Advisory'),
        ('notice', 'Civic Notice'),
        ('caution', 'Traffic / Weather Alert'),
        ('emergency', 'Urgent / Red Alert'),
    ]

    title = models.CharField(max_length=220, db_index=True)
    slug = models.SlugField(max_length=250, unique=True)
    category = models.ForeignKey(UpdateCategory, on_delete=models.PROTECT, related_name='updates')
    severity = models.CharField(max_length=20, choices=SEVERITY_LEVELS, default='info')
    summary = models.CharField(max_length=350)
    content = models.TextField()
    issuing_authority = models.CharField(max_length=150)
    official_source_url = models.URLField(max_length=500)
    valid_from = models.DateTimeField(default=timezone.now)
    valid_until = models.DateTimeField(null=True, blank=True)
    is_pinned = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        verbose_name = "City Update"
        verbose_name_plural = "City Updates"
        ordering = ['-is_pinned', '-valid_from']
        indexes = [
            models.Index(fields=['is_active', '-valid_from']),
            models.Index(fields=['is_pinned', '-valid_from']),
            models.Index(fields=['category', 'is_active']),
        ]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        if self.official_source_url:
            return self.official_source_url
        from django.urls import reverse
        return reverse('updates:list')

    @property
    def severity_label(self):
        return self.get_severity_display()

    @property
    def agency(self):
        return self.issuing_authority

    @property
    def source_url(self):
        return self.official_source_url

    @property
    def date(self):
        return self.valid_from.strftime("%d %b %Y") if self.valid_from else ""

    def clean(self):
        super().clean()
        if self.valid_from and self.valid_until:
            if self.valid_from > self.valid_until:
                raise ValidationError({'valid_until': 'Expiration datetime cannot precede valid from datetime.'})

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title) or "update"
            slug = base_slug
            counter = 1
            while CityUpdate.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)
