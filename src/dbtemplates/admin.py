import logging

from admin_extra_buttons.decorators import button, view
from admin_sync.mixins import SyncModelAdmin
from adminfilters.mixin import AdminFiltersMixin
from adminfilters.value import ValueFilter
from django import forms
from django.contrib import admin
from django.core.exceptions import ImproperlyConfigured
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.utils.translation import gettext_lazy as _
from django.utils.translation import ngettext

from .conf import settings
from .models import Template, add_template_to_cache, remove_cached_template
from .utils.template import check_template_syntax
from .widgets import HtmlEditor

if settings.DBTEMPLATES_USE_REVERSION:
    from reversion.admin import VersionAdmin as TemplateModelAdmin
else:
    from django.contrib.admin import ModelAdmin as TemplateModelAdmin  # noqa

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from django.db.models import QuerySet


logger = logging.getLogger(__name__)


if settings.DBTEMPLATES_AUTO_POPULATE_CONTENT:
    content_help_text = _(
        "Leaving this empty causes Django to look for a "
        "template with the given name and populate this "
        "field with its content."
    )
else:
    content_help_text = ""

if settings.DBTEMPLATES_USE_CODEMIRROR and settings.DBTEMPLATES_USE_TINYMCE:
    raise ImproperlyConfigured(
        "You may use either CodeMirror or TinyMCE with dbtemplates, not both. Please disable one of them."
    )


class TemplateAdminForm(forms.ModelForm):
    """Custom AdminForm to make the content textarea wider."""

    content = forms.CharField(
        widget=HtmlEditor(attrs={"rows": "24"}),
        help_text=content_help_text,
        required=False,
    )

    class Meta:
        model = Template
        fields = ("name", "content", "sites", "creation_date", "last_changed")


class TemplateAdmin(SyncModelAdmin, AdminFiltersMixin, TemplateModelAdmin):
    form = TemplateAdminForm
    fieldsets = (
        (
            None,
            {
                "fields": (
                    (
                        "name",
                        "active",
                    ),
                    "content",
                ),
                "classes": ("monospace",),
            },
        ),
        (
            _("Advanced"),
            {
                "fields": (("sites"),),
            },
        ),
        (
            _("Date/time"),
            {
                "fields": (("creation_date", "last_changed"),),
                "classes": ("collapse",),
            },
        ),
    )
    filter_horizontal = ("sites",)
    list_display = ("name", "creation_date", "last_changed", "site_list", "active")
    list_filter = (
        "sites",
        "active",
        ("name", ValueFilter.factory(lookup_name="endswith")),
    )
    save_as = True
    search_fields = ("name", "content")
    actions = ["invalidate_cache", "repopulate_cache", "check_syntax"]
    change_form_template = "admin/dbtemplates/template/change_form.html"

    def invalidate_cache(self, request: "HttpRequest", queryset: "QuerySet") -> None:
        for template in queryset:
            remove_cached_template(template)
        count = queryset.count()
        message = ngettext(
            "Cache of one template successfully invalidated.",
            "Cache of %(count)d templates successfully invalidated.",
            count,
        )
        self.message_user(request, message % {"count": count})

    invalidate_cache.short_description = _("Invalidate cache of selected templates")

    def repopulate_cache(self, request: "HttpRequest", queryset: "QuerySet") -> None:
        for template in queryset:
            add_template_to_cache(template)
        count = queryset.count()
        message = ngettext(
            "Cache successfully repopulated with one template.",
            "Cache successfully repopulated with %(count)d templates.",
            count,
        )
        self.message_user(request, message % {"count": count})

    repopulate_cache.short_description = _("Repopulate cache with selected templates")

    def check_syntax(self, request: "HttpRequest", queryset: "QuerySet") -> None:
        errors = []
        for template in queryset:
            valid, error = check_template_syntax(template)
            if not valid:
                errors.append("%s: %s" % (template.name, error))
        if errors:
            count = len(errors)
            message = ngettext(
                "Template syntax check FAILED for %(names)s.",
                "Template syntax check FAILED for %(count)d templates: %(names)s.",
                count,
            )
            self.message_user(request, message % {"count": count, "names": ", ".join(errors)})
        else:
            count = queryset.count()
            message = ngettext(
                "Template syntax OK.",
                "Template syntax OK for %(count)d templates.",
                count,
            )
            self.message_user(request, message % {"count": count})

    check_syntax.short_description = _("Check template syntax")

    def site_list(self, template: str) -> str:
        return ", ".join([site.name for site in template.sites.all()])

    site_list.short_description = _("sites")

    def check_publish_permission(self, request: "HttpRequest", obj: Template | None = None) -> bool:
        return True

    def check_sync_permission(self, request: "HttpRequest", obj: Template | None = None) -> bool:
        return True

    @view()
    def xrender(self, request: "HttpRequest", pk: str) -> HttpResponse:
        obj: Template = self.get_object(request, pk)
        from django.template import Context
        from django.template import Template as DjangoTemplate

        tpl = DjangoTemplate(obj.content)
        content = tpl.render(Context({}))
        return HttpResponse(content)

    @button()
    def preview(self, request: "HttpRequest", pk: str) -> HttpResponse:
        ctx = self.get_common_context(request, pk, title="Preview", preview_template=True)
        return render(request, "admin/dbtemplates/template/preview.html", ctx)


admin.site.register(Template, TemplateAdmin)
