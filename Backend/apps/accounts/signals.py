from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Profile, User, UserSettings


@receiver(post_save, sender=User)
def create_related_objects(sender, instance, created, **kwargs):
    """Every user gets a Profile and a UserSettings row on creation, so the
    API never has to deal with a missing one-to-one."""
    if created:
        Profile.objects.get_or_create(user=instance)
        UserSettings.objects.get_or_create(user=instance)
