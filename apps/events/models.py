import os
from django.db import models
from django.utils.text import slugify
from django.urls import reverse
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from apps.core.models import TimeStampedModel, SEOModel, VerifiableModel, Locality


def validate_image_extension(value):
    ext = os.path.splitext(value.name)[1].lower()
    valid_extensions = ['.jpg', '.jpeg', '.png', '.webp', '.svg']
    if ext not in valid_extensions:
        raise ValidationError(f'Unsupported image format "{ext}". Allowed formats: JPG, PNG, WEBP, SVG.')


class EventCategory(TimeStampedModel):
    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=150, unique=True)
    icon_class = models.CharField(max_length=60, default="bi-calendar-event")
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        verbose_name = "Event Category"
        verbose_name_plural = "Event Categories"
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return f"{reverse('events:list')}?category={self.slug}"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


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
        if self.google_maps_url:
            validator = URLValidator(schemes=['http', 'https'])
            try:
                validator(self.google_maps_url)
            except ValidationError:
                raise ValidationError({'google_maps_url': 'Enter a valid Google Maps URL starting with http:// or https://.'})

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


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
    custom_address = models.CharField(max_length=300, blank=True, verbose_name="Specific Hall / Room Address Override")
    start_datetime = models.DateTimeField(db_index=True)
    end_datetime = models.DateTimeField(db_index=True)
    ticket_policy = models.CharField(max_length=20, choices=TICKET_POLICIES, default='free')
    ticket_price_pkr = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    ticket_or_registration_url = models.URLField(max_length=500, blank=True, verbose_name="Official Booking / Registration URL")
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

    def get_absolute_url(self):
        return reverse('events:detail', kwargs={'slug': self.slug})

    @property
    def address(self):
        if self.custom_address:
            return self.custom_address
        return self.venue.address if self.venue else ""

    @property
    def organizer(self):
        return self.organizer_name

    @property
    def booking_url(self):
        return self.ticket_or_registration_url

    @property
    def image(self):
        return self.banner_image

    @property
    def last_verified_date(self):
        return self.last_verified_at

    @property
    def is_expired(self):
        return timezone.now() > self.end_datetime

    @property
    def is_ongoing(self):
        now = timezone.now()
        return self.start_datetime <= now <= self.end_datetime

    @property
    def is_upcoming(self):
        return self.end_datetime >= timezone.now()

    @property
    def date_str(self):
        if not self.start_datetime:
            return ""
        local_start = timezone.localtime(self.start_datetime)
        return local_start.strftime("%a, %d %b %Y")

    @property
    def time_str(self):
        if not self.start_datetime:
            return ""
        local_start = timezone.localtime(self.start_datetime)
        return local_start.strftime("%I:%M %p")

    @property
    def summary(self):
        return self.description[:140] if self.description else ""

    def clean(self):
        super().clean()
        if self.ticket_price_pkr is not None and self.ticket_price_pkr < 0:
            raise ValidationError({'ticket_price_pkr': 'Ticket price cannot be negative.'})
        if self.start_datetime and self.end_datetime:
            if self.start_datetime > self.end_datetime:
                raise ValidationError({'end_datetime': 'Event end date and time must be after start date and time.'})
        if self.ticket_or_registration_url:
            validator = URLValidator(schemes=['http', 'https'])
            try:
                validator(self.ticket_or_registration_url)
            except ValidationError:
                raise ValidationError({'ticket_or_registration_url': 'Enter a valid booking / registration URL starting with http:// or https://.'})
        if self.source_url:
            validator = URLValidator(schemes=['http', 'https'])
            try:
                validator(self.source_url)
            except ValidationError:
                raise ValidationError({'source_url': 'Enter a valid source URL starting with http:// or https://.'})
        if not self.slug and self.title:
            self.slug = slugify(self.title)
        if self.banner_image:
            if hasattr(self.banner_image, 'size') and self.banner_image.size > 5 * 1024 * 1024:
                raise ValidationError({'banner_image': 'Image file size cannot exceed 5MB.'})
            try:
                validate_image_extension(self.banner_image)
            except ValidationError as e:
                raise ValidationError({'banner_image': e.message})

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
