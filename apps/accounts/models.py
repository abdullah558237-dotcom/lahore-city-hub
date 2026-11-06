from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey

class CustomUserManager(BaseUserManager):
    """Custom manager for CustomUser with email as unique identifier."""

    def create_user(self, email, username=None, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        if not username:
            username = email.split('@')[0]
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        user = self.model(email=email, username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, username=None, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'admin')

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, username, password, **extra_fields)


class CustomUser(AbstractUser):
    """
    Primary user model for Lahore City Hub.
    Uses email as the unique identifier and enforces role-based permissions.
    """
    ROLE_MEMBER = 'member'
    ROLE_BUSINESS_OWNER = 'business_owner'
    ROLE_MODERATOR = 'moderator'
    ROLE_ADMIN = 'admin'

    ROLE_CHOICES = [
        (ROLE_MEMBER, 'Community Member'),
        (ROLE_BUSINESS_OWNER, 'Business Owner'),
        (ROLE_MODERATOR, 'Content Moderator'),
        (ROLE_ADMIN, 'Administrator'),
    ]

    email = models.EmailField(unique=True, db_index=True, verbose_name="Email Address")
    phone_number = models.CharField(max_length=25, blank=True, verbose_name="Phone Number")
    is_verified = models.BooleanField(default=False, verbose_name="Account Verified")
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_MEMBER, verbose_name="User Role")
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True, verbose_name="Profile Picture")

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    class Meta:
        verbose_name = "User Account"
        verbose_name_plural = "User Accounts"
        ordering = ['-date_joined']

    def __str__(self):
        return self.email


class UserProfile(models.Model):
    """Extended user profile data for Lahore residents and visitors."""
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='profile')
    bio = models.TextField(max_length=500, blank=True, verbose_name="Biography")
    home_locality = models.CharField(max_length=120, blank=True, verbose_name="Home Locality")
    receive_smog_alerts = models.BooleanField(default=True, verbose_name="Receive Smog Alerts")
    receive_event_digests = models.BooleanField(default=False, verbose_name="Receive Cultural Digest")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "User Profile"
        verbose_name_plural = "User Profiles"

    def __str__(self):
        return f"Profile of {self.user.email}"


class UserBookmark(models.Model):
    """Generic bookmarking mechanism for any directory entity."""
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='bookmarks')
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    notes = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Saved Bookmark"
        verbose_name_plural = "Saved Bookmarks"
        unique_together = [('user', 'content_type', 'object_id')]
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.email} saved {self.content_object}"
