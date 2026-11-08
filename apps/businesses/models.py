import os
from django.db import models
from django.conf import settings
from django.urls import reverse
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from apps.core.models import ListingBase, TimeStampedModel


def validate_image_extension(value):
    ext = os.path.splitext(value.name)[1].lower()
    valid_extensions = ['.jpg', '.jpeg', '.png', '.webp']
    if ext not in valid_extensions:
        raise ValidationError(f'Unsupported image format "{ext}". Allowed formats: JPG, PNG, WEBP.')


def validate_proof_document(value):
    if hasattr(value, 'size') and value.size > 10 * 1024 * 1024:
        raise ValidationError('Proof document file size cannot exceed 10MB.')
    ext = os.path.splitext(value.name)[1].lower()
    valid_extensions = ['.pdf', '.jpg', '.jpeg', '.png', '.webp']
    if ext not in valid_extensions:
        raise ValidationError(f'Unsupported file format "{ext}". Allowed document formats: PDF, JPG, PNG, WEBP.')


class BusinessCategory(TimeStampedModel):
    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=150, unique=True)
    icon_class = models.CharField(max_length=60, default="bi-shop")
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        verbose_name = "Business Category"
        verbose_name_plural = "Business Categories"
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return f"{reverse('businesses:list')}?category={self.slug}"


class Business(ListingBase):
    PROMOTION_TIER_STANDARD = 'standard'
    PROMOTION_TIER_VERIFIED_PRO = 'verified_pro'
    PROMOTION_TIER_FEATURED = 'featured_spotlight'

    PROMOTION_TIER_CHOICES = [
        (PROMOTION_TIER_STANDARD, 'Standard Organic'),
        (PROMOTION_TIER_VERIFIED_PRO, 'Verified Professional'),
        (PROMOTION_TIER_FEATURED, 'Featured Spotlight'),
    ]

    category = models.ForeignKey(BusinessCategory, on_delete=models.PROTECT, related_name='businesses')
    registration_number = models.CharField(max_length=100, blank=True, verbose_name="SECP / Chamber Reg No.")
    operating_hours = models.CharField(max_length=200, blank=True)
    promotion_tier = models.CharField(
        max_length=25,
        choices=PROMOTION_TIER_CHOICES,
        default=PROMOTION_TIER_STANDARD,
        db_index=True,
        verbose_name="Monetization / Promotion Tier"
    )
    promotion_notes = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Promotion Notes / Order Ref"
    )
    claimed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='owned_businesses'
    )
    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='submitted_businesses'
    )

    class Meta:
        verbose_name = "Local Business"
        verbose_name_plural = "Local Businesses"
        ordering = ['-is_featured', 'title']
        indexes = [
            models.Index(fields=['is_active', 'locality']),
            models.Index(fields=['is_active', 'category']),
            models.Index(fields=['is_featured', 'is_active']),
        ]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('businesses:detail', kwargs={'slug': self.slug})

    @property
    def is_verified(self):
        return self.verification_status in ['verified', 'claimed']

    def clean(self):
        super().clean()
        if self.primary_image:
            if hasattr(self.primary_image, 'size') and self.primary_image.size > 5 * 1024 * 1024:
                raise ValidationError({'primary_image': 'Image file size cannot exceed 5MB.'})
            validate_image_extension(self.primary_image)

        url_validator = URLValidator(schemes=['http', 'https'])
        if self.website:
            try:
                url_validator(self.website)
            except ValidationError:
                raise ValidationError({'website': 'Enter a valid website URL starting with http:// or https://.'})

        if self.source_url:
            try:
                url_validator(self.source_url)
            except ValidationError:
                raise ValidationError({'source_url': 'Enter a valid source URL starting with http:// or https://.'})


class BusinessClaim(TimeStampedModel):
    STATUS_CHOICES = [
        ('pending', 'Pending Editorial Audit'),
        ('under_review', 'Under Investigation'),
        ('approved', 'Approved & Verified'),
        ('rejected', 'Rejected as Unverified'),
    ]

    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='claims')
    claimant = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='business_claims')
    claimant_role = models.CharField(max_length=100, verbose_name="Role with Entity")
    official_email = models.EmailField()
    contact_phone = models.CharField(max_length=35)
    proof_document = models.FileField(
        upload_to='claims/proofs/',
        blank=True,
        null=True,
        validators=[validate_proof_document]
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', db_index=True)
    admin_notes = models.TextField(blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Business Claim Request"
        verbose_name_plural = "Business Claim Requests"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['business', 'status']),
            models.Index(fields=['claimant', 'status']),
        ]

    def __str__(self):
        return f"Claim for {self.business.title} by {self.claimant.email} ({self.status})"


class BusinessEditRequest(TimeStampedModel):
    STATUS_CHOICES = [
        ('pending', 'Pending Approval'),
        ('approved', 'Approved & Merged'),
        ('rejected', 'Rejected'),
    ]

    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='edit_requests')
    requested_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='business_edit_requests')
    title = models.CharField(max_length=200)
    summary = models.CharField(max_length=350, blank=True)
    description = models.TextField()
    address = models.CharField(max_length=300)
    phone_number = models.CharField(max_length=35, blank=True)
    website = models.URLField(max_length=500, blank=True)
    operating_hours = models.CharField(max_length=200, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', db_index=True)
    admin_notes = models.TextField(blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Business Edit Request"
        verbose_name_plural = "Business Edit Requests"
        ordering = ['-created_at']

    def __str__(self):
        return f"Edit Request for {self.business.title} by {self.requested_by.email} ({self.status})"


class BusinessReport(TimeStampedModel):
    REASON_CHOICES = [
        ('closed', 'Permanently Closed / Relocated'),
        ('wrong_phone', 'Incorrect Phone Number'),
        ('wrong_address', 'Incorrect Address / Location'),
        ('fake_business', 'Fraudulent / Fake Business'),
        ('wrong_hours', 'Incorrect Operating Hours'),
        ('other', 'Other Information Discrepancy'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('resolved', 'Investigated & Resolved'),
        ('dismissed', 'Dismissed as Inaccurate'),
    ]

    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='reports')
    reported_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='submitted_business_reports'
    )
    reporter_name = models.CharField(max_length=120)
    reporter_email = models.EmailField()
    reason = models.CharField(max_length=30, choices=REASON_CHOICES, default='other')
    details = models.TextField(verbose_name="Correction Details / Evidence")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', db_index=True)
    admin_notes = models.TextField(blank=True)
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Business Inaccuracy Report"
        verbose_name_plural = "Business Inaccuracy Reports"
        ordering = ['-created_at']

    def __str__(self):
        return f"Report on {self.business.title} ({self.get_reason_display()})"


class BusinessPromotionRequest(TimeStampedModel):
    STATUS_CHOICES = [
        ('pending', 'Pending Editorial Audit'),
        ('approved', 'Approved & Activated'),
        ('rejected', 'Declined'),
        ('cancelled', 'Cancelled by Owner'),
    ]

    TIER_CHOICES = [
        (Business.PROMOTION_TIER_VERIFIED_PRO, 'Verified Professional (Verified Seal + Contact Priority)'),
        (Business.PROMOTION_TIER_FEATURED, 'Featured Spotlight (Top Placement + Sponsored Badge)'),
    ]

    DURATION_CHOICES = [
        (30, '30 Days Spotlight'),
        (90, '90 Days (Quarterly Partner)'),
        (180, '180 Days (Half-Yearly Partner)'),
        (365, '365 Days (Annual Partner)'),
    ]

    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='promotion_requests')
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='business_promotion_requests'
    )
    target_tier = models.CharField(
        max_length=25,
        choices=TIER_CHOICES,
        default=Business.PROMOTION_TIER_FEATURED,
        verbose_name="Requested Promotion Tier"
    )
    duration_days = models.PositiveIntegerField(
        choices=DURATION_CHOICES,
        default=30,
        verbose_name="Campaign Duration (Days)"
    )
    contact_phone = models.CharField(
        max_length=35,
        verbose_name="Contact Phone / WhatsApp"
    )
    contact_email = models.EmailField(
        verbose_name="Official Billing Coordination Email"
    )
    campaign_goals = models.TextField(
        blank=True,
        verbose_name="Campaign Notes / Objectives",
        help_text="Provide any specific promotional highlights, target localities, or brand notes."
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        db_index=True
    )
    admin_notes = models.TextField(blank=True, verbose_name="Moderator Notes")
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Business Promotion Request"
        verbose_name_plural = "Business Promotion Requests"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['business', 'status']),
            models.Index(fields=['requested_by', 'status']),
        ]

    def __str__(self):
        return f"Promotion Request for {self.business.title} ({self.get_target_tier_display()}) by {self.requested_by.email}"

