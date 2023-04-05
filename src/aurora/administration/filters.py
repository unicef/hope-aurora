from adminfilters.autocomplete import get_real_field
from adminfilters.mixin import MediaDefinitionFilter, SmartFieldListFilter
from django.conf import settings
from django.contrib.admin.widgets import SELECT2_TRANSLATIONS
from django.urls import reverse
from django.utils.translation import get_language

from aurora.core.version_media import VersionMedia


class BaseAutoCompleteFilter(SmartFieldListFilter, MediaDefinitionFilter):
    template = "adminfilters/autocomplete.html"
    url_name = "%s:%s_%s_autocomplete"
    filter_title = None

    def __init__(self, field, request, params, model, model_admin, field_path):
        self.lookup_kwarg = "%s__exact" % field_path
        self.lookup_kwarg_isnull = "%s__isnull" % field_path
        self.lookup_val = params.get(self.lookup_kwarg)
        self.request = request
        super().__init__(field, request, params, model, model_admin, field_path)
        self.admin_site = model_admin.admin_site
        self.query_string = ""
        self.target_field = get_real_field(model, field_path)
        self.target_model = self.target_field.related_model

        self.target_opts = self.target_field.model._meta

        self.url = self.get_url()

    def expected_parameters(self):
        return [self.lookup_kwarg, self.lookup_kwarg_isnull]

    def get_url(self):
        return reverse("%s:autocomplete" % self.admin_site.name)

    def choices(self, changelist):
        self.query_string = changelist.get_query_string(remove=[self.lookup_kwarg, self.lookup_kwarg_isnull])
        if self.lookup_val:
            return [str(self.target_model.objects.get(pk=self.lookup_val)) or ""]
        return []

    @property
    def media(self):
        extra = "" if settings.DEBUG else ".min"
        i18n_name = SELECT2_TRANSLATIONS.get(get_language())
        i18n_file = ("admin/js/vendor/select2/i18n/%s.js" % i18n_name,) if i18n_name else ()
        return VersionMedia(
            js=(
                "admin/js/vendor/jquery/jquery%s.js" % extra,
                "admin/js/jquery.init.js",
                "jquery.compat%s.js" % extra,
                "admin/js/vendor/select2/select2.full%s.js" % extra,
            )
            + i18n_file
            + (
                "admin/js/jquery.init.js",
                "admin/js/autocomplete.js",
                "adminfilters/autocomplete%s.js" % extra,
            ),
            css={
                "screen": (
                    "admin/css/vendor/select2/select2%s.css" % extra,
                    "adminfilters/adminfilters.css",
                ),
            },
        )

    @classmethod
    def factory(cls, *, title=None, lookup_name="exact", **kwargs):
        kwargs["filter_title"] = title
        kwargs["lookup_name"] = lookup_name
        return type("ValueFilter", (cls,), kwargs)

    def get_title(self):
        if not self.can_negate and self.negated:
            if self.negated_title:
                return self.negated_title
            else:
                return f"not {self.title}"
        return self.filter_title or self.title
