from django.db.models.signals import post_save
from django.dispatch import receiver

from aurora.security.models import User, UserProfile


@receiver(post_save, sender=User)
def create_profile(instance: User, **kwargs) -> None:
    UserProfile.objects.get_or_create(id=instance.pk, user=instance)
