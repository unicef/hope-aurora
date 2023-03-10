from django import forms
from django.conf import settings
from django.utils.translation import gettext as _


class LanguageForm(forms.Form):
    locale = forms.ChoiceField(choices=settings.LANGUAGES)


class ImportForm(forms.Form):
    file = forms.FileField()


class TemplateForm(forms.Form):
    locale = forms.ChoiceField(choices=(["-", _("Any Language")],) + settings.LANGUAGES)


class ImportLanguageForm(forms.Form):
    locale = forms.ChoiceField(choices=settings.LANGUAGES)
    csv_file = forms.FileField(widget=forms.FileInput(attrs={"accept": ".csv"}))
