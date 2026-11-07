from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import CustomUser, UserProfile


@receiver(post_save, sender=CustomUser)
def create_or_save_user_profile(sender, instance, created, **kwargs):
    """
    Ensure every CustomUser automatically has an associated UserProfile.
    Prevents RelatedObjectDoesNotExist errors across the platform.
    """
    if created:
        UserProfile.objects.get_or_create(user=instance)
    else:
        if hasattr(instance, 'profile'):
            instance.profile.save()
        else:
            UserProfile.objects.get_or_create(user=instance)
