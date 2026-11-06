from django.db import models
from django.core.exceptions import ValidationError
from apps.core.models import ListingBase, TimeStampedModel

class PlaceCategory(TimeStampedModel):
    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=150, unique=True)
    icon_class = models.CharField(max_length=60, default="bi-bank")
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        verbose_name = "Place Category"
        verbose_name_plural = "Place Categories"
        ordering = ['name']

    def __str__(self):
        return self.name


class Place(ListingBase):
    category = models.ForeignKey(PlaceCategory, on_delete=models.PROTECT, related_name='places')
    architectural_era = models.CharField(max_length=120, blank=True, verbose_name="Architectural Era")
    entry_fee_pkr = models.DecimalField(max_digits=8, decimal_places=2, default=0.00, verbose_name="Entry Fee (PKR)")
    entry_fee_foreigner_pkr = models.DecimalField(max_digits=8, decimal_places=2, default=0.00, verbose_name="Foreigner Fee (PKR)")
    opening_time = models.TimeField(null=True, blank=True)
    closing_time = models.TimeField(null=True, blank=True)
    closed_on_days = models.CharField(max_length=60, blank=True, verbose_name="Closed Days")
    photography_policy = models.CharField(max_length=180, blank=True)
    wheelchair_accessible = models.BooleanField(default=False)
    nearest_metro_station = models.ForeignKey(
        'transport.TransitStation',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='nearby_places',
        verbose_name="Nearest Transit Station"
    )

    class Meta:
        verbose_name = "Tourist Place"
        verbose_name_plural = "Tourist Places"
        ordering = ['-is_featured', 'title']
        indexes = [
            models.Index(fields=['is_active', 'locality']),
            models.Index(fields=['is_featured', 'is_active']),
            models.Index(fields=['category', 'is_active']),
        ]

    def clean(self):
        super().clean()
        if self.entry_fee_pkr is not None and self.entry_fee_pkr < 0:
            raise ValidationError({'entry_fee_pkr': 'Entry fee cannot be negative.'})
        if self.entry_fee_foreigner_pkr is not None and self.entry_fee_foreigner_pkr < 0:
            raise ValidationError({'entry_fee_foreigner_pkr': 'Foreigner entry fee cannot be negative.'})


class PlaceGalleryImage(TimeStampedModel):
    place = models.ForeignKey(Place, on_delete=models.CASCADE, related_name='gallery_images')
    image = models.ImageField(upload_to='places/gallery/')
    caption = models.CharField(max_length=255, blank=True)
    photographer_credit = models.CharField(max_length=150, blank=True)
    display_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        verbose_name = "Place Gallery Image"
        verbose_name_plural = "Place Gallery Images"
        ordering = ['display_order']

    def __str__(self):
        return f"Photo for {self.place.title} (#{self.display_order})"
