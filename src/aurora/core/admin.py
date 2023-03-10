import json
import logging
from django.contrib import messages

from admin_extra_buttons.decorators import button, link, view
from admin_ordering.admin import OrderableAdmin
from admin_sync.utils import is_local
from adminfilters.autocomplete import AutoCompleteFilter
from adminfilters.combo import ChoicesFieldComboFilter, RelatedFieldComboFilter
from adminfilters.querystring import QueryStringFilter
from adminfilters.value import ValueFilter
from concurrency.api import disable_concurrency
from django import forms
from django.conf import settings
from django.contrib.admin import TabularInline, register
from django.contrib.admin.options import IncorrectLookupParameters
from django.core.cache import caches
from django.core.exceptions import ValidationError
from django.db.models import JSONField, Q
from django.http import HttpResponseRedirect
from django.urls import NoReverseMatch, reverse
from jsoneditor.forms import JSONEditor
from mptt.admin import MPTTModelAdmin
from reversion_compare.admin import CompareVersionAdmin
from smart_admin.modeladmin import SmartModelAdmin

from ..administration.filters import BaseAutoCompleteFilter
from ..administration.mixin import LoadDumpMixin
from .admin_sync import SyncMixin
from .field_editor import FieldEditor
from .fields.widgets import JavascriptEditor
from .forms import Select2Widget, ValidatorForm
from .models import (
    FIELD_KWARGS,
    CustomFieldType,
    FlexForm,
    FlexFormField,
    FormSet,
    OptionSet,
    Organization,
    Project,
    Validator,
)
from .protocols import AuroraSyncOrganizationProtocol, AuroraSyncProjectProtocol
from .utils import dict_setdefault, is_root, render

logger = logging.getLogger(__name__)

cache = caches["default"]


class ConcurrencyVersionAdmin(CompareVersionAdmin):
    change_list_template = "admin_extra_buttons/change_list.html"

    @button(label="Recover deleted")
    def _recoverlist_view(self, request):
        return super().recoverlist_view(request)

    def reversion_register(self, model, **options):
        options["exclude"] = ("version",)
        super().reversion_register(model, **options)

    def revision_view(self, request, object_id, version_id, extra_context=None):
        with disable_concurrency():
            return super().revision_view(request, object_id, version_id, extra_context)

    def recover_view(self, request, version_id, extra_context=None):
        with disable_concurrency():
            return super().recover_view(request, version_id, extra_context)

    def has_change_permission(self, request, obj=None):
        orig = super().has_change_permission(request, obj)
        return orig and (settings.DEBUG or is_root(request) or is_local(request))


class Select2FieldComboFilter(ChoicesFieldComboFilter):
    template = "adminfilters/select2.html"


class Select2RelatedFieldComboFilter(RelatedFieldComboFilter):
    template = "adminfilters/select2.html"


class ValidatorTestForm(forms.Form):
    code = forms.CharField(
        widget=JavascriptEditor,
    )
    input = forms.CharField(widget=JavascriptEditor(toolbar=False), required=False)


@register(Organization)
class OrganizationAdmin(SyncMixin, MPTTModelAdmin):
    list_display = ("name",)
    mptt_level_indent = 20
    mptt_indent_field = "name"
    search_fields = ("name",)
    protocol_class = AuroraSyncOrganizationProtocol
    change_list_template = "admin/core/organization/change_list.html"

    def admin_sync_show_inspect(self):
        return True

    def get_readonly_fields(self, request, obj=None):
        ro = super().get_readonly_fields(request, obj)
        if obj and obj.pk:
            ro = list(ro) + ["slug"]
        return ro


@register(Project)
class ProjectAdmin(SyncMixin, MPTTModelAdmin):
    list_display = ("name",)
    list_filter = ("organization",)
    mptt_level_indent = 20
    mptt_indent_field = "name"
    search_fields = ("name",)
    protocol_class = AuroraSyncProjectProtocol
    autocomplete_fields = "parent, "

    def get_search_results(self, request, queryset, search_term):
        queryset, may_have_duplicates = super().get_search_results(request, queryset, search_term)
        if "oid" in request.GET:
            queryset = queryset.filter(organization__id=request.GET["oid"])
        return queryset, may_have_duplicates

    def get_readonly_fields(self, request, obj=None):
        ro = super().get_readonly_fields(request, obj)
        if obj and obj.pk:
            ro = list(ro) + ["slug"]
        return ro


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


@register(FormSet)
class FormSetAdmin(LoadDumpMixin, SyncMixin, SmartModelAdmin):
    list_display = (
        "name",
        "title",
        "parent",
        "flex_form",
        "enabled",
        "validator",
        "min_num",
        "max_num",
        "extra",
        "dynamic",
    )
    search_fields = ("name", "title")
    list_editable = ("enabled",)
    readonly_fields = ("version", "last_update_date")
    list_filter = (
        ("parent", AutoCompleteFilter),
        ("flex_form", AutoCompleteFilter),
    )
    formfield_overrides = {
        JSONField: {"widget": JSONEditor},
    }

    def get_search_results(self, request, queryset, search_term):
        queryset, may_have_duplicates = super().get_search_results(request, queryset, search_term)
        if "oid" in request.GET:
            queryset = queryset.filter(flex_form__organization__id=request.GET["oid"])
        return queryset, may_have_duplicates


class FormSetInline(OrderableAdmin, TabularInline):
    model = FormSet
    fk_name = "parent"
    extra = 0
    fields = ("name", "flex_form", "extra", "max_num", "min_num", "ordering")
    show_change_link = True
    ordering_field = "ordering"
    ordering_field_hide_input = True

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        return super().formfield_for_dbfield(db_field, request, **kwargs)


class FlexFormFieldFormInline(forms.ModelForm):
    class Meta:
        model = FlexFormField
        exclude = ()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields["name"].widget.attrs = {"readonly": True, "tyle": "background-color:#f8f8f8;border:none"}


class FlexFormFieldForm(forms.ModelForm):
    class Meta:
        model = FlexFormField
        exclude = ()

    def clean(self):
        ret = super().clean()
        dict_setdefault(ret["advanced"], FlexFormField.FLEX_FIELD_DEFAULT_ATTRS)
        dict_setdefault(ret["advanced"], {"kwargs": FIELD_KWARGS.get(ret["field_type"], {})})
        return ret


@register(FlexFormField)
class FlexFormFieldAdmin(LoadDumpMixin, SyncMixin, ConcurrencyVersionAdmin, OrderableAdmin, SmartModelAdmin):
    search_fields = ("name", "label")
    list_display = ("label", "name", "flex_form", "field_type", "required", "enabled")
    list_editable = ["required", "enabled"]
    list_filter = (
        ("flex_form", AutoCompleteFilter),
        ("field_type", Select2FieldComboFilter),
        QueryStringFilter,
    )
    autocomplete_fields = ("flex_form", "validator")
    save_as = True
    readonly_fields = ("version", "last_update_date")
    formfield_overrides = {
        JSONField: {"widget": JSONEditor},
    }
    form = FlexFormFieldForm
    ordering_field = "ordering"
    order = "ordering"

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("flex_form")

    # change_list_template = "reversion/change_list.html"

    def field_type(self, obj):
        if obj.field_type:
            return obj.field_type.__name__
        else:
            return "[[ removed ]]"

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if db_field.name == "advanced":
            kwargs["widget"] = JSONEditor()
        return super().formfield_for_dbfield(db_field, request, **kwargs)

    def formfield_for_choice_field(self, db_field, request, **kwargs):
        if db_field.name == "field_type":
            kwargs["widget"] = Select2Widget()
            return db_field.formfield(**kwargs)
        return super().formfield_for_choice_field(db_field, request, **kwargs)

    def get_changeform_initial_data(self, request):
        initial = super().get_changeform_initial_data(request)
        initial.setdefault("advanced", FlexFormField.FLEX_FIELD_DEFAULT_ATTRS)
        return initial

    @button(label="editor")
    def field_editor(self, request, pk):
        self.editor = FieldEditor(self, request, pk)
        if request.method == "POST":
            ret = self.editor.post(request, pk)
            self.message_user(request, "Saved", messages.SUCCESS)
            return ret
        else:
            return self.editor.get(request, pk)

    @view()
    def widget_attrs(self, request, pk):
        editor = FieldEditor(self, request, pk)
        return editor.get_configuration()

    @view()
    def widget_refresh(self, request, pk):
        editor = FieldEditor(self, request, pk)
        return editor.refresh()

    @view()
    def widget_code(self, request, pk):
        editor = FieldEditor(self, request, pk)
        return editor.get_code()

    @view()
    def widget_display(self, request, pk):
        editor = FieldEditor(self, request, pk)
        return editor.render()

    @button()
    def test(self, request, pk):
        ctx = self.get_common_context(request, pk)
        try:
            fld = ctx["original"]
            instance = fld.get_instance()
            ctx["debug_info"] = {
                # "widget": getattr(instance, "widget", None),
                "field_kwargs": fld.get_field_kwargs(),
                # "options": getattr(instance, "options", None),
                # "choices": getattr(instance, "choices", None),
                # "widget_attrs": instance.widget_attrs(instance.widget),
            }
            form_class_attrs = {
                "sample": instance,
            }
            form_class = type(forms.Form)("TestForm", (forms.Form,), form_class_attrs)

            if request.method == "POST":
                form = form_class(request.POST)

                if form.is_valid():
                    ctx["debug_info"]["cleaned_data"] = form.cleaned_data
                    self.message_user(
                        request, f"Form validation success. You have selected: {form.cleaned_data['sample']}"
                    )
            else:
                form = form_class()
            ctx["form"] = form
            ctx["instance"] = instance
        except Exception as e:
            logger.exception(e)
            ctx["error"] = e
            raise

        return render(request, "admin/core/flexformfield/test.html", ctx)


class FlexFormFieldInline(LoadDumpMixin, OrderableAdmin, TabularInline):
    template = "admin/core/flexformfield/tabular.html"
    model = FlexFormField
    form = FlexFormFieldFormInline
    fields = ("ordering", "label", "name", "required", "enabled", "field_type")
    show_change_link = True
    extra = 0
    ordering_field = "ordering"
    ordering_field_hide_input = True

    def formfield_for_choice_field(self, db_field, request, **kwargs):
        # if db_field.name == "field_type":
        #     kwargs["widget"] = Select2Widget()
        #     return db_field.formfield(**kwargs)
        return super().formfield_for_choice_field(db_field, request, **kwargs)


class SyncConfigForm(forms.Form):
    APPS = ("core", "registration")
    apps = forms.MultipleChoiceField(choices=zip(APPS, APPS), widget=forms.CheckboxSelectMultiple())


class SyncForm(SyncConfigForm):
    host = forms.CharField()
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)
    remember = forms.BooleanField(label="Remember me", required=False)


class ProjectFilter(AutoCompleteFilter):
    fk_name = "project__organization__exact"

    def __init__(self, field, request, params, model, model_admin, field_path):
        self.request = request
        super().__init__(field, request, params, model, model_admin, field_path)

    def has_output(self):
        return "project__organization__exact" in self.request.GET

    def get_url(self):
        url = reverse("%s:autocomplete" % self.admin_site.name)
        if self.fk_name in self.request.GET:
            oid = self.request.GET[self.fk_name]
            return f"{url}?oid={oid}"
        return url


class UsedByRegistration(BaseAutoCompleteFilter):
    def has_output(self):
        return "project__exact" in self.request.GET

    def queryset(self, request, queryset):
        # {'registration__exact': '30'}
        if not self.used_parameters:
            return queryset
        try:
            value = self.used_parameters["registration__exact"]
            return queryset.filter(Q(registration__exact=value) | Q(formset__parent__registration=value))
        except (ValueError, ValidationError) as e:
            # Fields may raise a ValueError or ValidationError when converting
            # the parameters to the correct type.
            raise IncorrectLookupParameters(e)


class UsedInRFormset(BaseAutoCompleteFilter):
    def has_output(self):
        return "project__exact" in self.request.GET


@register(FlexForm)
class FlexFormAdmin(SyncMixin, ConcurrencyVersionAdmin, SmartModelAdmin):
    SYNC_COOKIE = "sync"
    inlines = [
        FlexFormFieldInline,
        FormSetInline,
    ]
    list_display = (
        "name",
        # "validator",
        "project",
        "is_main",
    )
    list_filter = (
        QueryStringFilter,
        ("project__organization", AutoCompleteFilter),
        ("project", ProjectFilter),
        ("registration", UsedByRegistration),
        ("formset", UsedInRFormset),
        ("formset__parent", UsedInRFormset),
    )
    search_fields = ("name",)
    readonly_fields = ("version", "last_update_date")
    autocomplete_fields = ("validator", "project")
    ordering = ("name",)
    save_as = True

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .prefetch_related("registration_set")
            .select_related(
                "project",
            )
        )

    def is_main(self, obj):
        return obj.registration_set.exists()

    is_main.boolean = True

    @button(html_attrs={"class": "aeb-danger"})
    def invalidate_cache(self, request):
        from .cache import cache

        cache.clear()

    @button(label="invalidate cache", html_attrs={"class": "aeb-warn"})
    def invalidate_cache_single(self, request, pk):
        obj = self.get_object(request, pk)
        obj.save()

    @button(label="Fields")
    def _fields(self, request, pk):
        url = reverse("admin:core_flexformfield_changelist")
        url = f"{url}?flex_form__exact={pk}"
        return HttpResponseRedirect(url)

    @button()
    def test(self, request, pk):
        ctx = self.get_common_context(request, pk)
        form_class = self.object.get_form_class()
        if request.method == "POST":
            form = form_class(request.POST, initial=self.object.get_initial())
            if form.is_valid():
                ctx["cleaned_data"] = form.cleaned_data
                self.message_user(request, "Form is valid")
        else:
            form = form_class(initial=self.object.get_initial())
        ctx["form"] = form
        return render(request, "admin/core/flexform/test.html", ctx)

    # @view(http_basic_auth=True, permission=lambda request, obj: request.user.is_superuser)
    # def export(self, request):
    #     try:
    #         frm = SyncConfigForm(request.GET)
    #         if frm.is_valid():
    #             apps = frm.cleaned_data["apps"]
    #             buf = io.StringIO()
    #             call_command(
    #                 "dumpdata",
    #                 *apps,
    #                 stdout=buf,
    #                 exclude=["registration.Record"],
    #                 use_natural_foreign_keys=True,
    #                 use_natural_primary_keys=True,
    #             )
    #             return JsonResponse(json.loads(buf.getvalue()), safe=False)
    #         else:
    #             return JsonResponse(frm.errors, status=400)
    #     except Exception as e:
    #         logger.exception(e)
    #         return JsonResponse({}, status=400)

    # def _get_signed_cookie(self, request, form):
    #     signer = Signer(request.user.password)
    #     return signer.sign_object(form.cleaned_data)
    #
    # def _get_saved_credentials(self, request):
    #     try:
    #         signer = Signer(request.user.password)
    #         obj: dict = signer.unsign_object(request.COOKIES.get(self.SYNC_COOKIE, {}))
    #         return obj
    #     except BadSignature:
    #         return {}

    # @button(label="Import")
    # def _import(self, request):
    #     ctx = self.get_common_context(request, title="Import")
    #     cookies = {}
    #     if request.method == "POST":
    #         form = SyncForm(request.POST)
    #         if form.is_valid():
    #             try:
    #                 auth = HTTPBasicAuth(form.cleaned_data["username"], form.cleaned_data["password"])
    #                 if form.cleaned_data["remember"]:
    #                     cookies = {self.SYNC_COOKIE: self._get_signed_cookie(request, form)}
    #                 else:
    #                     cookies = {self.SYNC_COOKIE: ""}
    #                 url = f"{form.cleaned_data['host']}core/flexform/export/?"
    #                 for app in form.cleaned_data["apps"]:
    #                     url += f"apps={app}&"
    #                 if not url.startswith("http"):
    #                     url = f"https://{url}"
    #
    #                 workdir = Path(".").absolute()
    #                 out = io.StringIO()
    #                 with requests.get(url, stream=True, auth=auth) as res:
    #                     if res.status_code != 200:
    #                         raise Exception(str(res))
    #                     ctx["url"] = url
    #                     with tempfile.NamedTemporaryFile(
    #                         dir=workdir, prefix="~SYNC", suffix=".json", delete=not settings.DEBUG
    #                     ) as fdst:
    #                         fdst.write(res.content)
    #                         with disable_concurrency():
    #                             fixture = (workdir / fdst.name).absolute()
    #                             call_command("loaddata", fixture, stdout=out, verbosity=3)
    #
    #                         message = out.getvalue()
    #                         self.message_user(request, message)
    #                 ctx["res"] = res
    #             except (Exception, JSONDecodeError) as e:
    #                 logger.exception(e)
    #                 self.message_error_to_user(request, e)
    #     else:
    #         form = SyncForm(initial=self._get_saved_credentials(request))
    #     ctx["form"] = form
    #     return render(request, "admin/core/flexform/import.html", ctx, cookies=cookies)


@register(OptionSet)
class OptionSetAdmin(LoadDumpMixin, SyncMixin, ConcurrencyVersionAdmin, SmartModelAdmin):
    list_display = (
        "name",
        "id",
        "separator",
        "comment",
        "pk_col",
    )
    search_fields = ("name",)
    list_filter = (("data", ValueFilter.factory(lookup_name="icontains")),)
    save_as = True
    readonly_fields = ("version", "last_update_date")
    object_history_template = "reversion-compare/object_history.html"

    @button()
    def display_data(self, request, pk):
        ctx = self.get_common_context(request, pk, title="Data")
        obj: OptionSet = ctx["original"]
        data = []
        for line in obj.data.split("\r\n"):
            data.append(line.split(obj.separator))
        ctx["data"] = data
        return render(request, "admin/core/optionset/table.html", ctx)

    @link(change_form=True, change_list=False, html_attrs={"target": "_new"})
    def view_json(self, button):
        original = button.context["original"]
        if original:
            try:
                button.href = original.get_api_url()
            except NoReverseMatch:
                button.href = "#"
                button.label = "Error reversing url"

    def change_view(self, request, object_id, form_url="", extra_context=None):
        if request.method == "POST" and "_saveasnew" in request.POST:
            object_id = None

        return super().change_view(request, object_id)


@register(CustomFieldType)
class CustomFieldTypeAdmin(SmartModelAdmin):
    list_display = (
        "name",
        "base_type",
        "attrs",
    )
    search_fields = ("name",)
    formfield_overrides = {
        JSONField: {"widget": JSONEditor},
    }

    @button()
    def test(self, request, pk):
        ctx = self.get_common_context(request, pk)
        fld = ctx["original"]
        field_type = fld.base_type
        kwargs = fld.attrs.copy()
        field = field_type(**kwargs)
        form_class_attrs = {
            "sample": field,
        }
        formClass = type(forms.Form)("TestForm", (forms.Form,), form_class_attrs)

        if request.method == "POST":
            form = formClass(request.POST)
            if form.is_valid():
                self.message_user(
                    request, f"Form validation success. " f"You have selected: {form.cleaned_data['sample']}"
                )
        else:
            form = formClass()
        ctx["form"] = form
        return render(request, "admin/core/customfieldtype/test.html", ctx)
