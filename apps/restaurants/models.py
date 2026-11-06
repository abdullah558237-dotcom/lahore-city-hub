from django.db import models
from django.core.exceptions import ValidationError
from apps.core.models import ListingBase, TimeStampedModel

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
        ('$', 'Budget / Street Food'),
        ('$$', 'Casual Dining'),
        ('$$$', 'Upscale / Fine Casual'),
        ('$$$$', 'Fine Dining / Luxury'),
    ]

    price_tier = models.CharField(max_length=5, choices=PRICE_CHOICES, default='$$')
    cuisines = models.ManyToManyField(Cuisine, related_name='restaurants', blank=True)
    features = models.ManyToManyField(RestaurantFeature, related_name='restaurants', blank=True)
    seating_capacity = models.PositiveIntegerField(null=True, blank=True)
    has_family_hall = models.BooleanField(default=True)
    provides_takeaway = models.BooleanField(default=True)
    provides_delivery = models.BooleanField(default=False)
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

    def clean(self):
        super().clean()
        if self.seating_capacity is not None and self.seating_capacity < 0:
            raise ValidationError({'seating_capacity': 'Seating capacity cannot be negative.'})


class MenuHighlight(TimeStampedModel):
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='menu_highlights')
    item_name = models.CharField(max_length=150)
    description = models.CharField(max_length=255, blank=True)
    price_pkr = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    is_signature = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Menu Highlight"
        verbose_name_plural = "Menu Highlights"

    def __str__(self):
        return f"{self.item_name} ({self.restaurant.title})"

    def clean(self):
        super().clean()
        if self.price_pkr is not None and self.price_pkr < 0:
            raise ValidationError({'price_pkr': 'Price cannot be negative.'})
