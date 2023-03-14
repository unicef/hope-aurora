from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import AuroraUser

User = get_user_model()


@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    if not isinstance(instance, AuroraUser):  # be safe
        AuroraUser.objects.get_or_create(id=instance.pk, user=instance)
        instance.profile.save()


# @receiver(post_save, sender=User)
# def save_profile(sender, instance, **kwargs):
#     instance.profile.save()
