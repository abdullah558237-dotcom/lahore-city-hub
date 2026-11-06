from django.db import models
from django.conf import settings
from apps.core.models import ListingBase, TimeStampedModel

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


class Business(ListingBase):
    category = models.ForeignKey(BusinessCategory, on_delete=models.PROTECT, related_name='businesses')
    registration_number = models.CharField(max_length=100, blank=True, verbose_name="SECP / Chamber Reg No.")
    operating_hours = models.CharField(max_length=200, blank=True)
    claimed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='owned_businesses'
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
    proof_document = models.FileField(upload_to='claims/proofs/', blank=True, null=True)
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
