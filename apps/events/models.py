from django.db import models
from django.utils.text import slugify
from django.core.exceptions import ValidationError
from apps.core.models import TimeStampedModel, SEOModel, VerifiableModel, Locality

class EventCategory(TimeStampedModel):
    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=150, unique=True)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        verbose_name = "Event Category"
        verbose_name_plural = "Event Categories"
        ordering = ['name']

    def __str__(self):
        return self.name


class EventVenue(TimeStampedModel):
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True)
    address = models.CharField(max_length=300)
    locality = models.ForeignKey(Locality, on_delete=models.PROTECT, related_name='event_venues')
    capacity = models.PositiveIntegerField(null=True, blank=True)
    google_maps_url = models.URLField(max_length=500, blank=True)

    class Meta:
        verbose_name = "Event Venue"
        verbose_name_plural = "Event Venues"
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.locality.name})"

    def clean(self):
        super().clean()
        if self.capacity is not None and self.capacity < 0:
            raise ValidationError({'capacity': 'Venue capacity cannot be negative.'})


class Event(TimeStampedModel, SEOModel, VerifiableModel):
    TICKET_POLICIES = [
        ('free', 'Free Public Entry'),
        ('ticketed', 'Paid Ticket Required'),
        ('registration', 'Free with Prior Registration'),
        ('invite_only', 'By Invitation Only'),
    ]

    title = models.CharField(max_length=220, db_index=True)
    slug = models.SlugField(max_length=250, unique=True)
    category = models.ForeignKey(EventCategory, on_delete=models.PROTECT, related_name='events')
    venue = models.ForeignKey(EventVenue, on_delete=models.PROTECT, related_name='events')
    start_datetime = models.DateTimeField(db_index=True)
    end_datetime = models.DateTimeField(db_index=True)
    ticket_policy = models.CharField(max_length=20, choices=TICKET_POLICIES, default='free')
    ticket_price_pkr = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    ticket_or_registration_url = models.URLField(max_length=500, blank=True)
    organizer_name = models.CharField(max_length=150)
    organizer_contact = models.CharField(max_length=100, blank=True)
    banner_image = models.ImageField(upload_to='events/banners/', blank=True, null=True)
    description = models.TextField()
    is_featured = models.BooleanField(default=False, db_index=True)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        verbose_name = "Event"
        verbose_name_plural = "Events"
        ordering = ['start_datetime']
        indexes = [
            models.Index(fields=['is_active', 'start_datetime']),
            models.Index(fields=['is_featured', 'start_datetime']),
            models.Index(fields=['category', 'start_datetime']),
        ]

    def __str__(self):
        return self.title

    @property
    def date_str(self):
        return self.start_datetime.strftime("%a, %d %b %Y") if self.start_datetime else ""

    @property
    def time_str(self):
        return self.start_datetime.strftime("%I:%M %p") if self.start_datetime else ""

    @property
    def summary(self):
        return self.description[:110] if self.description else ""

    def clean(self):
        super().clean()
        if self.ticket_price_pkr is not None and self.ticket_price_pkr < 0:
            raise ValidationError({'ticket_price_pkr': 'Ticket price cannot be negative.'})
        if self.start_datetime and self.end_datetime:
            if self.start_datetime > self.end_datetime:
                raise ValidationError({'end_datetime': 'Event end datetime cannot be before start datetime.'})

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title) or "event"
            slug = base_slug
            counter = 1
            while Event.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)
