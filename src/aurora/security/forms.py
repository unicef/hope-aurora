import logging

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm, UsernameField
from django.core.exceptions import ValidationError

from aurora.security.models import AuroraRole

logger = logging.getLogger(__name__)


class AuroraUserCreationForm(UserCreationForm):
    class Meta:
        model = get_user_model()
        fields = ()
        field_classes = {"username": UsernameField, "email": forms.EmailField}


class AuroraRoleForm(forms.ModelForm):
    class Meta:
        model = AuroraRole
        fields = "__all__"

    def clean(self):
        found = [
            self.cleaned_data.get(x) for x in ["organization", "project", "registration"] if self.cleaned_data.get(x)
        ]
        if not found:
            raise ValidationError("You must set one scope")
        if len(found) > 1:
            raise ValidationError("You must set only one scope")
