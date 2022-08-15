from django_filters import FilterSet

from smart_register.steficon.models import Rule


class SteficonRuleFilter(FilterSet):
    class Meta:
        fields = ("enabled", "deprecated")
        model = Rule
