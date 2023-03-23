import json
import logging

from admin_extra_buttons.decorators import button
from django import forms
from django.contrib.admin import register
from django.core.cache import caches
from smart_admin.modeladmin import SmartModelAdmin

from ...administration.mixin import LoadDumpMixin
from ..admin_sync import SyncMixin
from ..fields.widgets import JavascriptEditor
from ..forms import ValidatorForm
from ..models import Validator
from ..utils import render
from .base import ConcurrencyVersionAdmin

logger = logging.getLogger(__name__)

cache = caches["default"]


class ValidatorTestForm(forms.Form):
    code = forms.CharField(
        widget=JavascriptEditor,
    )
    input = forms.CharField(widget=JavascriptEditor(toolbar=False), required=False)


@register(Validator)
class ValidatorAdmin(LoadDumpMixin, SyncMixin, ConcurrencyVersionAdmin, SmartModelAdmin):
    form = ValidatorForm
    list_editable = ("trace", "active", "draft")
    list_display = ("label", "name", "target", "used_by", "trace", "active", "draft")
    list_filter = ("target", "active", "draft", "trace")
    readonly_fields = ("version", "last_update_date")
    search_fields = ("name",)
    DEFAULTS = {
        Validator.FORM: {},  # cleaned data
        Validator.FIELD: "",  # field value
        Validator.SCRIPT: "",  # field value
        Validator.MODULE: [{}],
        Validator.FORMSET: {"total_form_count": 2, "errors": {}, "non_form_errors": {}, "cleaned_data": []},
    }
    # change_list_template = "reversion/change_list.html"
    object_history_template = "reversion-compare/object_history.html"
    change_form_template = None
    inlines = []

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        cache.set(f"validator-{request.user.pk}-{obj.pk}-status", obj.STATUS_UNKNOWN)

    def used_by(self, obj):
        if obj.target == Validator.FORM:
            return ", ".join(obj.flexform_set.values_list("name", flat=True))
        elif obj.target == Validator.FIELD:
            return ", ".join(obj.flexformfield_set.values_list("name", flat=True))
        elif obj.target == Validator.FORMSET:
            return ", ".join(obj.formset_set.values_list("name", flat=True))
        elif obj.target == Validator.MODULE:
            return ", ".join(obj.validator_for.values_list("name", flat=True))
        elif obj.target == Validator.SCRIPT:
            return ", ".join(obj.script_for.values_list("name", flat=True))

    @button()
    def test(self, request, pk):
        ctx = self.get_common_context(request, pk)
        original = ctx["original"]
        stored = cache.get(f"validator-{request.user.pk}-{original.pk}-payload")
        ctx["traced"] = stored
        ctx["title"] = f"Test {original.target} validator: {original.name}"
        if stored:
            param = json.loads(stored)
        else:
            param = self.DEFAULTS[original.target]

        if request.method == "POST":
            form = ValidatorTestForm(request.POST)
            if form.is_valid():
                self.object.code = form.cleaned_data["code"]
                self.object.save()
                # return HttpResponseRedirect("..")
        else:
            form = ValidatorTestForm(
                initial={"code": self.object.code, "input": original.jspickle(param)},
            )

        ctx["jslib"] = Validator.LIB
        ctx["is_script"] = self.object.target in [Validator.SCRIPT]
        ctx["is_validator"] = self.object.target not in [Validator.SCRIPT]
        ctx["form"] = form
        return render(request, "admin/core/validator/test.html", ctx)
