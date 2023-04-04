from django import forms


class DebugForm(forms.Form):
    search = forms.CharField(required=False)
