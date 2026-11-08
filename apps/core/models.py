import os
from django.db import models
from django.utils.text import slugify
from django.conf import settings
from django.core.exceptions import ValidationError


def validate_listing_image(value):
    if hasattr(value, 'size') and value.size > 5 * 1024 * 1024:
        raise ValidationError('Image file size cannot exceed 5MB.')
    ext = os.path.splitext(value.name)[1].lower()
    valid_extensions = ['.jpg', '.jpeg', '.png', '.webp']
    if ext not in valid_extensions:
        raise ValidationError(f'Unsupported image format "{ext}". Allowed formats: JPG, PNG, WEBP.')


class TimeStampedModel(models.Model):
    """Abstract base model tracking creation and modification timestamps."""
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class SluggableModel(models.Model):
    """Abstract model enforcing unique slugs and bilingual titles."""
    title = models.CharField(max_length=255, db_index=True, verbose_name="English Title")
    title_ur = models.CharField(max_length=255, blank=True, null=True, verbose_name="Urdu Title")
    slug = models.SlugField(max_length=280, unique=True, db_index=True)

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title) or "listing"
            slug = base_slug
            counter = 1
            while self.__class__.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)


class VerifiableModel(models.Model):
    """Abstract model maintaining an explicit editorial verification trail."""
    STATUS_UNVERIFIED = 'unverified'
    STATUS_PENDING = 'pending'
    STATUS_VERIFIED = 'verified'
    STATUS_CLAIMED = 'claimed'

    VERIFICATION_STATUS_CHOICES = [
        (STATUS_UNVERIFIED, 'Unverified'),
        (STATUS_PENDING, 'Pending Editorial Audit'),
        (STATUS_VERIFIED, 'Verified Official Record'),
        (STATUS_CLAIMED, 'Claimed & Verified by Owner'),
    ]

    verification_status = models.CharField(
        max_length=20,
        choices=VERIFICATION_STATUS_CHOICES,
        default=STATUS_UNVERIFIED,
        db_index=True
    )
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )
    last_verified_at = models.DateTimeField(null=True, blank=True, db_index=True)
    source_url = models.URLField(max_length=500, blank=True, verbose_name="Primary Source URL")
    verification_notes = models.TextField(blank=True, verbose_name="Internal Audit Notes")

    class Meta:
        abstract = True

    @property
    def is_verified(self):
        return self.verification_status in [self.STATUS_VERIFIED, self.STATUS_CLAIMED]


class ContactableModel(models.Model):
    """Abstract model standardizing contact endpoints and WhatsApp links."""
    phone_number = models.CharField(max_length=35, blank=True, verbose_name="Telephone Number")
    emergency_phone = models.CharField(max_length=35, blank=True, verbose_name="Emergency Hotline")
    email = models.EmailField(blank=True, verbose_name="Official Email")
    website = models.URLField(max_length=500, blank=True, verbose_name="Official Website")
    whatsapp_number = models.CharField(max_length=35, blank=True, verbose_name="WhatsApp Number")

    class Meta:
        abstract = True


class LocalityZone(TimeStampedModel):
    """Broad administrative or cultural zones across Lahore."""
    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=150, unique=True)
    description = models.TextField(blank=True)

    class Meta:
        verbose_name = "Locality Zone"
        verbose_name_plural = "Locality Zones"
        ordering = ['name']

    def __str__(self):
        return self.name


class Locality(TimeStampedModel):
    """Specific neighborhood or commercial sector within Lahore."""
    zone = models.ForeignKey(LocalityZone, on_delete=models.CASCADE, related_name='localities')
    name = models.CharField(max_length=150, db_index=True)
    slug = models.SlugField(max_length=180, unique=True)
    postal_code = models.CharField(max_length=12, blank=True)

    class Meta:
        verbose_name = "Locality"
        verbose_name_plural = "Localities"
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.zone.name})"


class LocationModel(models.Model):
    """Abstract model for spatial coordinates and physical addresses."""
    locality = models.ForeignKey(
        Locality,
        on_delete=models.PROTECT,
        related_name='%(app_label)s_%(class)s_listings',
        null=True,
        blank=True
    )
    address = models.CharField(max_length=500, blank=False, verbose_name="Physical Address")
    landmark = models.CharField(max_length=255, blank=True, verbose_name="Nearby Landmark")
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    google_maps_url = models.URLField(max_length=500, blank=True, verbose_name="Google Maps Link")

    class Meta:
        abstract = True

    def clean(self):
        super().clean()
        if self.latitude is not None and not (-90 <= self.latitude <= 90):
            raise ValidationError({'latitude': 'Latitude must be between -90 and 90 degrees.'})
        if self.longitude is not None and not (-180 <= self.longitude <= 180):
            raise ValidationError({'longitude': 'Longitude must be between -180 and 180 degrees.'})


class SEOModel(models.Model):
    """Abstract model managing SEO meta tags and social open graph data."""
    meta_title = models.CharField(max_length=80, blank=True)
    meta_description = models.CharField(max_length=160, blank=True)
    canonical_url = models.URLField(max_length=500, blank=True)
    og_image = models.ImageField(upload_to='seo/', blank=True, null=True, validators=[validate_listing_image])

    class Meta:
        abstract = True


class ListingBase(TimeStampedModel, SluggableModel, VerifiableModel, ContactableModel, LocationModel, SEOModel):
    """
    Standard foundation for all directory listings in Lahore City Hub.
    Combines timestamps, slugging, verification, contacts, location, and SEO.
    """
    summary = models.CharField(max_length=350, verbose_name="Short Summary")
    description = models.TextField(verbose_name="Full Editorial Description")
    primary_image = models.ImageField(upload_to='listings/banners/', blank=True, null=True, validators=[validate_listing_image])
    is_active = models.BooleanField(default=True, db_index=True)
    is_featured = models.BooleanField(default=False, db_index=True)
    featured_until = models.DateTimeField(null=True, blank=True)
    view_count = models.PositiveIntegerField(default=0)

    class Meta:
        abstract = True

    def __str__(self):
        return self.title


class EmergencyHelpline(TimeStampedModel):
    """Civic emergency and disaster relief helplines for Lahore."""
    name = models.CharField(max_length=120)
    short_code = models.CharField(max_length=20)
    full_phone_number = models.CharField(max_length=35, blank=True)
    agency_name = models.CharField(max_length=180)
    badge_label = models.CharField(max_length=50, blank=True, default="24/7 Life Safety")
    is_active = models.BooleanField(default=True, db_index=True)
    display_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        verbose_name = "Emergency Helpline"
        verbose_name_plural = "Emergency Helplines"
        ordering = ['display_order', 'name']
        indexes = [
            models.Index(fields=['is_active', 'display_order']),
        ]

    def __str__(self):
        return f"{self.name} ({self.short_code})"
