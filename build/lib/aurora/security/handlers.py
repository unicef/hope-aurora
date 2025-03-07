from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver

from aurora.security.models import UserProfile

User = get_user_model()


@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    UserProfile.objects.get_or_create(id=instance.pk, user=instance)
