import logging

from django import forms
from django.conf import settings
from django.contrib.auth.forms import UserCreationForm, UsernameField

logger = logging.getLogger(__name__)


class AuroraUserCreationForm(UserCreationForm):
    class Meta:
        model = settings.AUTH_USER_MODEL
        fields = ()
        field_classes = {"username": UsernameField, "email": forms.EmailField}
