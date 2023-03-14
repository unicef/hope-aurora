import sqlparse
from django import forms
from django.core.exceptions import ValidationError


class ImportForm(forms.Form):
    file = forms.FileField()


class ExportForm(forms.Form):
    APPS = ("core", "registration", "i18n", "constance", "counters", "flatpages", "security", "dbtemplates")
    apps = forms.MultipleChoiceField(choices=zip(APPS, APPS), widget=forms.CheckboxSelectMultiple())


class SQLForm(forms.Form):
    command = forms.CharField()

    def clean_command(self):
        value = self.cleaned_data.pop("command")
        try:
            statements = sqlparse.split(value)
            if len(statements) > 1:
                raise ValidationError("Only one statement is allowed")
        except ValidationError:
            raise
        except Exception as e:
            raise ValidationError(e)
        return value
