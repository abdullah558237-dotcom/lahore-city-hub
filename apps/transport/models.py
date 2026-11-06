from django.db import models
from django.core.exceptions import ValidationError
from apps.core.models import TimeStampedModel, Locality

class TransitMode(TimeStampedModel):
    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=150, unique=True)
    icon_class = models.CharField(max_length=60, default="bi-train-front")
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        verbose_name = "Transit Mode"
        verbose_name_plural = "Transit Modes"
        ordering = ['name']

    def __str__(self):
        return self.name


class TransitRoute(TimeStampedModel):
    mode = models.ForeignKey(TransitMode, on_delete=models.CASCADE, related_name='routes')
    route_name = models.CharField(max_length=150)
    route_code = models.CharField(max_length=30)
    origin_station = models.CharField(max_length=120)
    destination_station = models.CharField(max_length=120)
    total_stations = models.PositiveSmallIntegerField(default=1)
    total_distance_km = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)
    operating_schedule = models.CharField(max_length=150, default="06:00 AM – 10:00 PM Daily")
    fare_info = models.TextField(blank=True)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        verbose_name = "Transit Route"
        verbose_name_plural = "Transit Routes"
        ordering = ['mode', 'route_name']
        indexes = [
            models.Index(fields=['mode', 'is_active']),
            models.Index(fields=['route_code', 'is_active']),
        ]

    def __str__(self):
        return f"{self.route_code}: {self.route_name}"

    def clean(self):
        super().clean()
        if self.total_stations < 1:
            raise ValidationError({'total_stations': 'Total stations must be at least 1.'})
        if self.total_distance_km < 0:
            raise ValidationError({'total_distance_km': 'Total distance cannot be negative.'})


class TransitStation(TimeStampedModel):
    route = models.ForeignKey(TransitRoute, on_delete=models.CASCADE, related_name='stations')
    station_name = models.CharField(max_length=120)
    station_number = models.PositiveSmallIntegerField()
    locality = models.ForeignKey(Locality, on_delete=models.PROTECT, related_name='transit_stations')
    is_interchange = models.BooleanField(default=False)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

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

    def clean(self):
        super().clean()
        if self.station_number < 1:
            raise ValidationError({'station_number': 'Station number must be at least 1.'})
