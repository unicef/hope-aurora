import json
import logging
import os
import time
from functools import wraps
from hashlib import md5
from json import JSONDecodeError
from typing import Dict, Type

import sentry_sdk
from constance import config
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.models import User
from django.core import signing
from django.core.exceptions import ValidationError
from django.forms import forms
from django.http import Http404, HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.utils import translation
from django.utils.cache import get_conditional_response
from django.utils.decorators import method_decorator
from django.utils.functional import cached_property
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView
from django.views.generic.edit import FormView
from sentry_sdk import set_tag

from aurora.core.utils import (
    get_etag,
    get_qrcode,
    has_token,
    never_ever_cache,
    total_size,
)
from aurora.i18n.gettext import gettext as _
from aurora.registration.models import Record, Registration
from aurora.state import state
from aurora.stubs import FormSet

logger = logging.getLogger(__name__)


class QRVerify(TemplateView):
    template_name = "registration/register_verify.html"

    def get_context_data(self, **kwargs):
        record = Record.objects.get(id=self.kwargs["pk"])
        valid = md5(record.storage).hexdigest() == self.kwargs["hash"]
        return super().get_context_data(valid=valid, record=record, **kwargs)


class RegisterCompleteView(TemplateView):
    template_name = "registration/register_done.html"

    def get_template_names(self):
        slug = self.registration.slug
        language = translation.get_language()
        return [f"registration/{language}/{slug}_done.html", f"registration/{slug}_done.html", self.template_name]

    @cached_property
    def registration(self):
        return self.record.registration

    @cached_property
    def record(self):
        try:
            return Record.objects.select_related("registration").get(
                registration__id=self.kwargs["reg"], id=self.kwargs["rec"]
            )
        except Record.DoesNotExist:
            if state.collect_messages:
                Record.objects.first()
            raise Http404

    def get_qrcode(self, record):
        h = md5(str(record.fields).encode()).hexdigest()
        url = self.request.build_absolute_uri(reverse("register-done", args=[record.registration.pk, record.pk]))
        hashed_url = f"{url}/{h}"
        return get_qrcode(hashed_url), url

    def get_context_data(self, **kwargs):
        if config.QRCODE:
            qrcode, url = self.get_qrcode(self.record)
        else:
            qrcode, url = None, None
        return super().get_context_data(qrcode=qrcode, url=url, record=self.record, **kwargs)


class BinaryFile:
    def __init__(self, content):
        self.content = content


@method_decorator(csrf_exempt, name="dispatch")
class RegisterRouter(FormView):
    def get_template_names(self):
        return []

    def get_form(self, form_class=None):
        return None

    def post(self, request, *args, **kwargs):
        r = Registration.objects.only("slug", "version", "locale").get(slug=request.POST["slug"])
        language = translation.get_language()
        if language not in r.all_locales:
            language = r.locale
        with translation.override(language):
            url = r.get_absolute_url()
        return HttpResponseRedirect(url)


class RegistrationMixin:
    @cached_property
    def registration(self):
        filters = {}
        if not self.request.user.is_staff and not state.collect_messages:
            filters["active"] = True

        base = Registration.objects.select_related("flex_form", "validator", "project", "project__organization")
        try:
            reg = base.get(slug=self.kwargs["slug"], **filters)
            set_tag("registration.organization", reg.project.organization.name)
            set_tag("registration.project", reg.project.name)
            set_tag("registration.slug", reg.name)
            return reg
        except Registration.DoesNotExist:  # pragma: no coalidateer
            raise Http404


def check_access(view_func):
    def wrapped_view(*args, **kwargs):
        view, request = args
        if view.registration.protected:
            login_url = "%s?next=%s" % (settings.USER_LOGIN_URL, request.path)
            if request.user.is_anonymous:
                return HttpResponseRedirect(login_url)
            if not request.user.has_perm("registration.register", view.registration):
                messages.add_message(request, messages.ERROR, _("Sorry you do not have access to requested Form"))
                return HttpResponseRedirect(login_url)
        return view_func(*args, **kwargs)

    wrapped_view.csrf_exempt = True
    return wraps(view_func)(wrapped_view)


@method_decorator(csrf_exempt, name="dispatch")
class RegisterView(RegistrationMixin, FormView):
    template_name = "registration/register.html"

    def get_template_names(self):
        slug = self.registration.slug
        language = translation.get_language()
        return [f"registration/{language}/{slug}.html", f"registration/{slug}.html", self.template_name]

    @check_access
    def get(self, request, *args, **kwargs):
        # if request.user.is_authenticated and not request.GET.get("s"):
        #     return HttpResponseRedirect(self.registration.get_absolute_url())

        if state.collect_messages:
            self.res_etag = get_etag(request, time.time())
        else:
            language = translation.get_language()
            if language not in self.registration.all_locales:
                with translation.override(self.registration.locale):
                    url = self.registration.get_absolute_url()
                    return HttpResponseRedirect(url)

            self.res_etag = get_etag(
                request,
                self.registration.active,
                str(self.registration.version),
                os.environ.get("BUILD_DATE", ""),
                translation.get_language(),
                {True: "staff", False: ""}[request.user.is_staff],
            )
        response = get_conditional_response(request, str(self.res_etag))
        if response is None:
            response = super().get(request, *args, **kwargs)
            response.headers.setdefault("ETag", self.res_etag)
        return response

    def get_form_class(self):
        return self.registration.flex_form.get_form_class()

    # @cache_formset
    def get_formsets_classes(self) -> Dict[str, Type[FormSet]]:
        #     return self.registration.flex_form.get_formsets_classes()
        formsets = {}
        # attrs = self.get_form_kwargs().copy()
        # attrs.pop("prefix")
        for fs in self.registration.flex_form.formsets.select_related("flex_form", "parent").filter(enabled=True):
            formsets[fs.name] = fs.get_formset()
        return formsets

    def get_initial(self):
        return self.registration.flex_form.get_initial()

    def get_formsets(self):
        formsets = {}
        attrs = self.get_form_kwargs().copy()
        attrs["initial"] = []
        attrs.pop("prefix")
        for name, fs in self.get_formsets_classes().items():
            attrs["initial"] = [fs.form.flex_form.get_initial()]
            formsets[name] = fs(prefix=f"{name}", **attrs)
        return formsets

    def get_context_data(self, **kwargs):
        if "formsets" not in kwargs:
            kwargs["formsets"] = self.get_formsets()
        kwargs["registration"] = self.registration
        kwargs["can_edit_inpage"] = self.request.user.is_staff
        kwargs["can_translate"] = self.request.user.is_staff

        ctx = super().get_context_data(**kwargs)
        m = forms.Media()
        m += ctx["form"].media
        for __, f in ctx["formsets"].items():
            m += f.media
        ctx["media"] = m
        return ctx

    def validate(self, cleaned_data):
        if self.registration.validator:
            try:
                self.registration.validator.validate(cleaned_data, registration=self)
            except ValidationError as e:
                self.errors.append(e)
                return False

        try:
            if unique_value := self.registration.get_unique_value(cleaned_data):
                r = Record(registration=self.registration, unique_field=unique_value)
                r.validate_unique()
                cleaned_data["unique_field"] = unique_value
        except ValidationError:
            self.errors.append(ValidationError(_(self.registration.unique_field_error)))
            return False
        return True

    @check_access
    def post(self, request, *args, **kwargs):
        slug = request.resolver_match.kwargs.get("slug")
        registration = Registration.objects.filter(slug=slug).first()
        if registration and registration.is_pwa_enabled:
            encrypted_data = request.POST.get("encryptedData")
            if encrypted_data:
                kwargs = {"fields": encrypted_data, "size": total_size(encrypted_data), "is_offline": True}

                Record.objects.create(registration=registration, **kwargs)
                return HttpResponse()

        form = self.get_form()
        formsets = self.get_formsets()
        self.errors = []
        is_valid = True
        all_cleaned_data = {}

        for fs in formsets.values():
            if fs.is_valid():
                all_cleaned_data[fs.fs.name] = fs.cleaned_data
            else:
                all_cleaned_data[fs.fs.name] = []
                is_valid = False
        form_valid = form.is_valid()
        all_cleaned_data.update(**form.cleaned_data)

        is_valid = self.validate(all_cleaned_data) and is_valid
        if form_valid and is_valid:
            return self.form_valid(form, formsets)
        else:
            return self.form_invalid(form, formsets)

    def form_valid(self, form, formsets):
        data = form.cleaned_data

        for name, fs in formsets.items():
            data[name] = []
            for f in fs:
                data[name].append(f.cleaned_data)

        data["counters"] = form.get_counters(data)
        if form.indexes["1"]:
            data["index1"] = data[form.indexes["1"]]
        if form.indexes["2"]:
            data["index2"] = data[form.indexes["2"]]
        if form.indexes["3"]:
            data["index3"] = data[form.indexes["3"]]
        record = self.registration.add_record(data)
        success_url = reverse("register-done", args=[self.registration.pk, record.pk])
        return HttpResponseRedirect(success_url)

    def form_invalid(self, form, formsets):
        """If the form is invalid, render the invalid form."""
        if config.LOG_POST_ERRORS:
            with sentry_sdk.push_scope() as scope:
                scope.set_extra("errors", self.errors)
                scope.set_extra("form.errors", form.errors)
                for n, f in formsets.items():
                    scope.set_extra(n, f.errors)
                scope.set_extra("target", self.target)
                logger.error("Validation Error")

        return self.render_to_response(
            self.get_context_data(form=form, invalid=True, errors=self.errors, formsets=formsets)
        )


class RegisterAuthView(RegistrationMixin, View):
    @method_decorator(never_ever_cache)
    def get(self, request, *args, **kwargs):
        project = {
            "build_date": os.environ.get("BUILD_DATE", ""),
            "version": os.environ.get("VERSION", ""),
            "debug": settings.DEBUG,
            "env": settings.SMART_ADMIN_HEADER,
            "sentry_dsn": settings.SENTRY_DSN,
            "cache": config.CACHE_VERSION,
            "has_token": has_token(request),
        }
        return JsonResponse(
            {
                "registration": {
                    "name": self.registration.name,
                    "locale": self.registration.locale,
                    "protected": self.registration.protected,
                },
                "project": project,
                "user": {
                    "username": request.user.username,
                    # "perms": request.user.get_all_permissions(self.registration),
                    # "authenticated": request.user.is_authenticated,
                    "anonymous": not request.user.is_authenticated,
                },
            }
        )


def registrations(request):
    # if request.user.is_authenticated:
    registration_objs = Registration.objects.filter(active=True)

    if request.method == "GET":
        return render(request, "registration/registrations.html", {"registrations": registration_objs})
    elif request.method == "POST":
        slug = request.POST["slug"]
        registration = get_object_or_404(Registration, slug=slug)
        registration.is_pwa_enabled = True
        registration.save(update_fields=["is_pwa_enabled"])

        Registration.objects.exclude(slug=slug).update(is_pwa_enabled=False)  # only one can be enabled at once

        return render(request, "registration/registrations.html", {"registrations": registration_objs})


def get_pwa_enabled(request):
    register_obj = Registration.objects.filter(is_pwa_enabled=True).first()
    return JsonResponse(
        {
            "slug": getattr(register_obj, "slug", None),
            "version": getattr(register_obj, "version", None),
            "publicKey": getattr(register_obj, "public_key", None),
            "optionsSets": getattr(register_obj, "option_set_links", None),
        }
    )


@csrf_exempt
def authorize_cookie(request):
    try:
        decoded_key = signing.loads(
            json.loads(request.body),
            max_age=settings.SESSION_COOKIE_AGE,
            salt="django.contrib.sessions.backends.signed_cookies",
        )
        if User.objects.filter(id=int(decoded_key.get("_auth_user_id"))).exists():
            return JsonResponse({"authorized": True})
        else:
            return JsonResponse({"authorized": False})
    except (signing.BadSignature, JSONDecodeError):
        logger.info("PWA Cookie was not authorized")
        return JsonResponse({"authorized": False})
