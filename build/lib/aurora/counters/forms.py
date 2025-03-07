from django import forms

from aurora.registration.models import Registration


class ChartForm(forms.Form):
    registration = forms.ModelChoiceField(Registration.objects.all())
