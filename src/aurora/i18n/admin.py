import csv
import logging
from hashlib import md5
from io import TextIOWrapper
from typing import TYPE_CHECKING
from unittest.mock import Mock
from urllib.parse import unquote

from admin_extra_buttons.decorators import button, view
from adminfilters.combo import ChoicesFieldComboFilter
from adminfilters.querystring import QueryStringFilter
from dateutil.utils import today
from django.conf import settings
from django.contrib import messages
from django.contrib.admin import register
from django.core.cache import caches
from django.db.models import Model, QuerySet
from django.db.transaction import atomic
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.template import loader
from django.urls import reverse
from django.utils import translation
from django.utils.translation import get_language
from smart_admin.modeladmin import SmartModelAdmin

from ..core.admin_sync import SyncMixin
from ..core.forms import CSVOptionsForm
from ..core.models import FlexForm
from ..state import state
from .engine import translator
from .forms import ImportLanguageForm, LanguageForm
from .models import Message

if TYPE_CHECKING:
    from django.utils.datastructures import _ListOrTuple

logger = logging.getLogger(__name__)

cache = caches["default"]


@register(Message)
class MessageAdmin(SyncMixin, SmartModelAdmin):
    search_fields = ("msgid__icontains", "md5")
    list_display = ("md5", "__str__", "locale", "draft", "used")
    list_editable = ("draft",)
    readonly_fields = ("md5", "msgcode")
    list_filter = (
        "draft",
        "used",
        ("locale", ChoicesFieldComboFilter),
        QueryStringFilter,
        "last_hit",
    )
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "msgid",
                    "msgstr",
                    "locale",
                )
            },
        ),
        (
            None,
            {"fields": (("draft", "auto", "used"),)},
        ),
        (
            None,
            {"fields": (("md5", "msgcode"),)},
        ),
    )
    actions = ("approve", "rehash", "publish_action")
    object: Message

    def approve(self, request: HttpRequest, queryset: QuerySet[Message]) -> None:
        num = queryset.update(draft=False)
        self.message_user(request, f"{num} Messages have been approved")

    def get_queryset(self, request: HttpRequest) -> QuerySet:
        return (
            super()
            .get_queryset(request)
            .defer(
                "msgcode",
            )
        )

    @button()  # type: ignore[arg-type]
    def import_translations(self, request: HttpRequest) -> HttpResponse:  # noqa: C901, PLR0912, PLR0915
        ctx = self.get_common_context(request, media=self.media, title="Import Translations File", pre={}, post={})
        ctx["rows"] = []
        if request.method == "POST":
            key = "_".join(
                [
                    "translation",
                    str(request.user.pk),
                    str(state.timestamp),
                    str(md5(request.session.session_key.encode()).hexdigest()),  # noqa: S324
                ]
            )
            if "save" in request.POST:
                data = cache.get(key, version=1)
                selection = request.POST.getlist("selection")
                lang = data["language_code"]
                processed = selected = updated = created = 0
                ids = []
                with atomic():
                    for row in data["messages"]:
                        processed += 1
                        info = row[1]
                        if info["msgid"] in selection:
                            selected += 1
                            __, c = Message.objects.update_or_create(
                                msgid=info["msgid"],
                                locale=lang,
                                defaults={"msgstr": info["msgstr"]},
                            )
                            ids.append(str(__.pk))
                            if c:
                                created += 1
                            else:
                                updated += 1
                    self.message_user(
                        request,
                        f"Messages processed: "
                        f"Processed: {processed}, "
                        f"Selected: {selected}, "
                        f"Created: {created}, "
                        f"Updated: {updated}",
                    )
                    base_url = reverse("admin:i18n_message_changelist")
                    return HttpResponseRedirect(f"{base_url}?locale__exact={lang}&qs=id__in={','.join(ids)}")
            else:  # if "import" in request.POST:
                form = ImportLanguageForm(request.POST, request.FILES)
                opts_form = CSVOptionsForm(request.POST, prefix="csv")
                if form.is_valid() and opts_form.is_valid():
                    csv_file = form.cleaned_data["csv_file"]
                    if csv_file.multiple_chunks():
                        self.message_user(
                            request,
                            "Uploaded file is too big (%.2f MB)" % (csv_file.size / 1000),
                        )
                    else:
                        ctx["language_code"] = form.cleaned_data["locale"]
                        ctx["language"] = dict(form.fields["locale"].choices)[ctx["language_code"]]  # type: ignore[attr-defined]
                        rows = TextIOWrapper(csv_file, encoding="utf-8")
                        rows.seek(0)
                        config = {**opts_form.cleaned_data}
                        has_header = config.pop("header", False)
                        reader = csv.reader(rows, **config)
                        try:
                            for line_count, row in enumerate(reader, 1):
                                if has_header and line_count == 1:
                                    continue
                                found = Message.objects.filter(msgid=row[0]).first()
                                ctx["rows"].append(
                                    [
                                        line_count,
                                        {
                                            "msgid": row[0],
                                            "msgstr": row[1],
                                            "found": bool(found),
                                            "match": found and found.msgstr == row[1],
                                        },
                                    ]
                                )
                            data = {
                                "header": has_header,
                                "language": ctx["language"],
                                "language_code": ctx["language_code"],
                                "messages": ctx["rows"],
                            }
                            cache.set(key, data, timeout=86400, version=1)
                            self.message_user(
                                request,
                                "Uploaded file succeeded (%.2f MB)" % (csv_file.size / 1000),
                            )
                        except IndexError:
                            self.message_user(
                                request, "Error on line %d. Check import configuration" % line_count, messages.ERROR
                            )
        else:
            form = ImportLanguageForm()
            opts_form = CSVOptionsForm(prefix="csv", initial=CSVOptionsForm.defaults)
        ctx["form"] = form
        ctx["opts_form"] = opts_form
        return render(request, "admin/i18n/message/import_trans.html", ctx)

    @button()  # type: ignore[arg-type]
    def check_orphans(self, request: HttpRequest) -> HttpResponse | None:
        ctx = self.get_common_context(request, media=self.media, title="Check Orphans", pre={}, post={})
        if request.method == "POST":
            form = LanguageForm(request.POST)
            locale = get_language()
            if form.is_valid():
                lang = form.cleaned_data["locale"]
                translator.activate(lang)
                translation.activate(lang)
                translator[lang].reset()
                ctx["pre"]["total_messages"] = Message.objects.all().count()
                ctx["pre"]["used"] = Message.objects.filter(used=True).count()
                ctx["pre"]["unused"] = Message.objects.filter(used=False).count()
                Message.objects.update(last_hit=None, used=False)
                try:
                    state.collect_messages = True
                    state.hit_messages = True
                    for flex_form in FlexForm.objects.all():
                        frm_cls = flex_form.get_form_class()
                        for frm in [frm_cls(), frm_cls({})]:
                            loader.render_to_string(
                                "smart/_form.html",
                                {
                                    "form": frm,
                                    "formsets": flex_form.get_formsets({}),
                                    "request": Mock(selected_language=lang),
                                },
                            )
                except Exception as e:
                    logger.exception(e)
                finally:
                    ctx["post"]["total_messages"] = Message.objects.all().count()
                    ctx["post"]["used"] = Message.objects.filter(used=True).count()
                    ctx["post"]["unused"] = Message.objects.filter(used=False).count()
                    translator.activate(locale)
                    translation.activate(locale)
                    state.collect_messages = False
                    state.hit_messages = False
        else:
            form = LanguageForm()
            ctx["form"] = form
        return render(request, "admin/i18n/message/check_orphans.html", ctx)

    @view()  # type: ignore[arg-type]
    def get_or_create(self, request: HttpRequest) -> HttpResponse:
        if request.method == "POST":
            msgid = unquote(request.POST["msgid"])
            lang = request.POST["lang"]
            queryset = self.get_queryset(request)
            try:
                obj = queryset.get(msgid=msgid, locale=lang)
                self.message_user(request, "Found")
            except Message.DoesNotExist:
                obj = Message(msgid=msgid, locale=lang)
                obj.save()
                self.message_user(request, "Created", messages.WARNING)
            cl = reverse("admin:i18n_message_change", args=[obj.pk])
        else:
            cl = reverse("admin:i18n_message_changelist")

        return HttpResponseRedirect(cl)

    def rehash(self, request: HttpRequest, queryset: QuerySet) -> None:
        num = 0
        for m in queryset.all():
            m.save()
            num += 1
        self.message_user(request, f"{num} Messages have been rehashed")

    @button()  # type: ignore[arg-type]
    def siblings(self, request: HttpRequest, pk: str) -> HttpResponse:
        obj: Message = self.get_object(request, pk)  # type: ignore[assignment]
        cl = reverse("admin:i18n_message_changelist")
        return HttpResponseRedirect(f"{cl}?msgcode__exact={obj.msgcode}")

    @button(label="Create Translation")  # type: ignore[arg-type]
    def create_translation_single(self, request: HttpRequest, pk: str) -> HttpResponse:
        ctx = self.get_common_context(
            request,
            pk,
            media=self.media,
            title="Generate Translation",
        )
        if request.method == "POST":
            form = LanguageForm(request.POST)
            if form.is_valid():
                locale = form.cleaned_data["locale"]
                original: Message = ctx["original"]
                try:
                    msg, created = original.update_or_create_translation(original.msgid, locale=locale, draft=True)
                    if created:
                        self.message_user(request, "Message created.")
                    else:
                        self.message_user(request, "Message found.", messages.WARNING)
                    return HttpResponseRedirect(reverse("admin:i18n_message_change", args=[msg.pk]))
                except Exception as e:
                    logger.exception(e)
                    self.message_error_to_user(request, e)
                    return HttpResponseRedirect(".")
            ctx["form"] = form
        else:
            form = LanguageForm()
            ctx["form"] = form
        return render(request, "admin/i18n/message/translation.html", ctx)

    @button()  # type: ignore[arg-type]
    def create_translations(self, request: HttpRequest) -> HttpResponse:
        ctx = self.get_common_context(
            request,
            media=self.media,
            title="Generate Translation",
        )
        if request.method == "POST":
            form = LanguageForm(request.POST)
            if form.is_valid():
                locale = form.cleaned_data["locale"]
                existing = Message.objects.filter(locale=locale).count()
                try:
                    for msg in Message.objects.filter(locale=settings.LANGUAGE_CODE).order_by("msgid").distinct():
                        Message.objects.get_or_create(
                            msgid=msg.msgid,
                            locale=locale,
                            defaults={
                                "md5": Message.get_md5(locale, msg.msgid),
                                "draft": True,
                            },
                        )
                except Exception as e:
                    logger.exception(e)
                    self.message_error_to_user(request, e)

                updated = Message.objects.filter(locale=locale).count()
                added = Message.objects.filter(locale=locale, draft=True, timestamp__date=today())
                self.message_user(
                    request,
                    f"{updated - existing} messages created. {updated} available",
                )
                ctx["locale"] = locale
                ctx["added"] = added
            else:
                ctx["form"] = form
        else:
            form = LanguageForm()
            ctx["form"] = form
        return render(request, "admin/i18n/message/translation.html", ctx)

    def get_readonly_fields(self, request: HttpRequest, obj: Model | None = None) -> "_ListOrTuple[str]":
        if obj:
            return ("msgid",) + self.readonly_fields
        return self.readonly_fields
