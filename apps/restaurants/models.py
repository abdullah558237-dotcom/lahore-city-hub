import os
from django.db import models
from django.urls import reverse
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from apps.core.models import ListingBase, TimeStampedModel


def validate_image_extension(value):
    ext = os.path.splitext(value.name)[1].lower()
    valid_extensions = ['.jpg', '.jpeg', '.png', '.webp']
    if ext not in valid_extensions:
        raise ValidationError(f'Unsupported image format "{ext}". Allowed formats: JPG, PNG, WEBP.')


class Cuisine(TimeStampedModel):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        verbose_name = "Cuisine"
        verbose_name_plural = "Cuisines"
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return f"{reverse('restaurants:list')}?cuisine={self.slug}"


class RestaurantFeature(TimeStampedModel):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True)
    icon_class = models.CharField(max_length=60, default="bi-check-circle")

    class Meta:
        verbose_name = "Restaurant Feature"
        verbose_name_plural = "Restaurant Features"
        ordering = ['name']

    def __str__(self):
        return self.name


class Restaurant(ListingBase):
    PRICE_CHOICES = [
        ('$', 'Budget / Street Food ($)'),
        ('$$', 'Casual Dining ($$)'),
        ('$$$', 'Upscale / Fine Casual ($$$)'),
        ('$$$$', 'Fine Dining / Luxury ($$$$)'),
    ]

    price_tier = models.CharField(max_length=5, choices=PRICE_CHOICES, default='$$')
    cuisines = models.ManyToManyField(Cuisine, related_name='restaurants', blank=True)
    features = models.ManyToManyField(RestaurantFeature, related_name='restaurants', blank=True)
    seating_capacity = models.PositiveIntegerField(null=True, blank=True)
    has_family_hall = models.BooleanField(default=True)
    provides_takeaway = models.BooleanField(default=True)
    provides_delivery = models.BooleanField(default=False)
    opening_time = models.TimeField(null=True, blank=True, verbose_name="Opening Time")
    closing_time = models.TimeField(null=True, blank=True, verbose_name="Closing Time")
    closed_on_days = models.CharField(max_length=60, blank=True, verbose_name="Closed Days")
    ramadan_timings = models.CharField(max_length=255, blank=True)

    class Meta:
        verbose_name = "Restaurant"
        verbose_name_plural = "Restaurants"
        ordering = ['-is_featured', 'title']
        indexes = [
            models.Index(fields=['is_active', 'locality']),
            models.Index(fields=['is_active', 'price_tier']),
            models.Index(fields=['is_featured', 'is_active']),
        ]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('restaurants:detail', kwargs={'slug': self.slug})

    @property
    def has_verified_hours(self):
        return bool(self.opening_time and self.closing_time)

    @property
    def formatted_hours(self):
        if self.opening_time and self.closing_time:
            return f"{self.opening_time.strftime('%I:%M %p')} – {self.closing_time.strftime('%I:%M %p')}"
        return "Timings on inquiry"

    @property
    def price_tier_display(self):
        mapping = {
            '$': 'Budget / Street Food',
            '$$': 'Casual Dining',
            '$$$': 'Upscale / Fine Casual',
            '$$$$': 'Fine Dining / Luxury',
        }
        return mapping.get(self.price_tier, self.price_tier)

    def clean(self):
        super().clean()
        if self.seating_capacity is not None and self.seating_capacity < 0:
            raise ValidationError({'seating_capacity': 'Seating capacity cannot be negative.'})
        if self.primary_image:
            if hasattr(self.primary_image, 'size') and self.primary_image.size > 5 * 1024 * 1024:
                raise ValidationError({'primary_image': 'Banner image cannot exceed 5MB.'})
            validate_image_extension(self.primary_image)
        if self.website:
            url_validator = URLValidator(schemes=['http', 'https'])
            try:
                url_validator(self.website)
            except ValidationError:
                raise ValidationError({'website': 'Enter a valid website URL starting with http:// or https://.'})


class RestaurantGalleryImage(TimeStampedModel):
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='gallery_images')
    image = models.ImageField(upload_to='restaurants/gallery/', validators=[validate_image_extension])
    caption = models.CharField(max_length=255, blank=True)
    photographer_credit = models.CharField(max_length=150, blank=True)
    display_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        verbose_name = "Restaurant Gallery Image"
        verbose_name_plural = "Restaurant Gallery Images"
        ordering = ['display_order']

    def __str__(self):
        return f"Photo for {self.restaurant.title} (#{self.display_order})"

    def clean(self):
        super().clean()
        if self.image:
            if hasattr(self.image, 'size') and self.image.size > 5 * 1024 * 1024:
                raise ValidationError({'image': 'Gallery image file size cannot exceed 5MB.'})


class MenuHighlight(TimeStampedModel):
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='menu_highlights')
    item_name = models.CharField(max_length=150)
    description = models.CharField(max_length=255, blank=True)
    price_pkr = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    is_signature = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Menu Highlight"
        verbose_name_plural = "Menu Highlights"
        ordering = ['-is_signature', 'item_name']

    def __str__(self):
        return f"{self.item_name} ({self.restaurant.title})"

    def clean(self):
        super().clean()
        if self.price_pkr is not None and self.price_pkr < 0:
            raise ValidationError({'price_pkr': 'Price cannot be negative.'})
