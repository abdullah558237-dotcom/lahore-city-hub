from django.db import models
from django.utils.text import slugify
from django.urls import reverse
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from apps.core.models import TimeStampedModel, Locality


class TransitMode(TimeStampedModel):
    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=150, unique=True)
    icon_class = models.CharField(max_length=60, default="bi-train-front")
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        verbose_name = "Transit Mode"
        verbose_name_plural = "Transit Modes"
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class TransitRoute(TimeStampedModel):
    mode = models.ForeignKey(TransitMode, on_delete=models.CASCADE, related_name='routes')
    route_name = models.CharField(max_length=150)
    route_code = models.CharField(max_length=30)
    slug = models.SlugField(max_length=180, unique=True, blank=True)
    origin_station = models.CharField(max_length=120)
    destination_station = models.CharField(max_length=120)
    total_stations = models.PositiveSmallIntegerField(default=1)
    total_distance_km = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)
    operating_schedule = models.CharField(max_length=150, default="06:00 AM – 10:00 PM Daily")
    frequency = models.CharField(max_length=120, blank=True, default="Every 5–10 minutes during peak hours")
    fare_info = models.TextField(blank=True)
    description = models.TextField(blank=True)
    operator = models.CharField(max_length=150, default="Punjab Masstransit Authority (PMA)")
    source_url = models.URLField(max_length=500, blank=True)
    last_updated_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True, db_index=True)
    is_featured = models.BooleanField(default=False, db_index=True)

    class Meta:
        verbose_name = "Transit Route"
        verbose_name_plural = "Transit Routes"
        ordering = ['mode', 'route_name']
        indexes = [
            models.Index(fields=['mode', 'is_active']),
            models.Index(fields=['route_code', 'is_active']),
            models.Index(fields=['is_featured', 'is_active']),
        ]

    def __str__(self):
        return f"{self.route_code}: {self.route_name}"

    def get_absolute_url(self):
        return reverse('transport:route_detail', kwargs={'slug': self.slug})

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(f"{self.route_code}-{self.route_name}") or "transit-route"
            slug = base_slug
            counter = 1
            while TransitRoute.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def clean(self):
        super().clean()
        if self.total_stations < 1:
            raise ValidationError({'total_stations': 'Total stations must be at least 1.'})
        if self.total_distance_km < 0:
            raise ValidationError({'total_distance_km': 'Total distance cannot be negative.'})
        if self.source_url:
            validator = URLValidator(schemes=['http', 'https'])
            try:
                validator(self.source_url)
            except ValidationError:
                raise ValidationError({'source_url': 'Enter a valid official source URL starting with http:// or https://.'})


class TransitStation(TimeStampedModel):
    route = models.ForeignKey(TransitRoute, on_delete=models.CASCADE, related_name='stations')
    station_name = models.CharField(max_length=120)
    urdu_name = models.CharField(max_length=120, blank=True)
    slug = models.SlugField(max_length=180, unique=True, blank=True)
    station_number = models.PositiveSmallIntegerField()
    locality = models.ForeignKey(
        Locality,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transit_stations'
    )
    is_interchange = models.BooleanField(default=False)
    is_terminal = models.BooleanField(default=False)
    is_underground = models.BooleanField(default=False)
    has_wheelchair_access = models.BooleanField(default=True)
    has_parking = models.BooleanField(default=False)
    interchange_details = models.CharField(max_length=255, blank=True)
    nearby_landmarks = models.CharField(max_length=300, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    source_url = models.URLField(max_length=500, blank=True)
    last_verified_date = models.DateField(null=True, blank=True)

    class Meta:
        verbose_name = "Transit Station"
        verbose_name_plural = "Transit Stations"
        ordering = ['route', 'station_number']
        unique_together = [('route', 'station_number')]
        indexes = [
            models.Index(fields=['route', 'station_number']),
            models.Index(fields=['locality', 'is_interchange']),
        ]

    def __str__(self):
        return f"{self.station_name} (#{self.station_number}) - {self.route.route_code}"

    def get_absolute_url(self):
        return reverse('transport:station_detail', kwargs={'slug': self.slug})

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(f"{self.station_name}-{self.route.route_code}") or "station"
            slug = base_slug
            counter = 1
            while TransitStation.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def clean(self):
        super().clean()
        if self.station_number < 1:
            raise ValidationError({'station_number': 'Station number must be at least 1.'})
        if self.source_url:
            validator = URLValidator(schemes=['http', 'https'])
            try:
                validator(self.source_url)
            except ValidationError:
                raise ValidationError({'source_url': 'Enter a valid source URL starting with http:// or https://.'})


class TransitGuide(TimeStampedModel):
    CATEGORY_CHOICES = [
        ('smart_cards', 'Smart Cards, Tokens & Fares'),
        ('rules_safety', 'Platform Rules & Safety Guidelines'),
        ('accessibility', 'Women, Senior Citizens & Special Needs'),
        ('interchange', 'Station Interchanges & Transfers'),
        ('commuter_tips', 'Commuter Advice & Peak Hours'),
    ]

    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    category = models.CharField(max_length=40, choices=CATEGORY_CHOICES, default='smart_cards', db_index=True)
    route = models.ForeignKey(
        TransitRoute,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='guides'
    )
    summary = models.CharField(max_length=350)
    content = models.TextField()
    icon_class = models.CharField(max_length=60, default="bi-info-circle")
    source_url = models.URLField(max_length=500, blank=True)
    last_verified_date = models.DateField(null=True, blank=True)
    is_published = models.BooleanField(default=True, db_index=True)
    is_featured = models.BooleanField(default=False, db_index=True)
    display_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        verbose_name = "Transit Guide & Travel Advice"
        verbose_name_plural = "Transit Guides & Travel Advice"
        ordering = ['display_order', 'title']
        indexes = [
            models.Index(fields=['is_published', 'category']),
            models.Index(fields=['is_featured', 'is_published']),
        ]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('transport:guide_detail', kwargs={'slug': self.slug})

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title) or "transit-guide"
            slug = base_slug
            counter = 1
            while TransitGuide.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def clean(self):
        super().clean()
        if self.source_url:
            validator = URLValidator(schemes=['http', 'https'])
            try:
                validator(self.source_url)
            except ValidationError:
                raise ValidationError({'source_url': 'Enter a valid official source URL starting with http:// or https://.'})
