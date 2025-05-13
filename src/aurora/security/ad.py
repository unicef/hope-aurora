import logging
from collections import namedtuple
from typing import TYPE_CHECKING, Any

from admin_extra_buttons.decorators import button
from admin_extra_buttons.mixins import ExtraButtonsMixin
from constance import config
from django import forms
from django.contrib import admin, messages
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.forms.forms import Form
from django.http import Http404, HttpRequest, HttpResponse
from django.template.response import TemplateResponse
from requests import HTTPError

from aurora.core.models import Organization, Project
from aurora.registration.models import Registration
from aurora.security.microsoft_graph import MicrosoftGraphAPI, MicrosoftGraphAPIError
from aurora.security.models import AuroraRole, User

if TYPE_CHECKING:
    from aurora.types.http import AuthHttpRequest

logger = logging.getLogger(__name__)

# NOTE: add after UserModel migration "ad_uuid": "id",
DJANGO_USER_MAP = {
    "username": "mail",
    "email": "mail",
    "first_name": "givenName",
    "last_name": "surname",
}


class LoadUsersForm(forms.Form):
    emails = forms.CharField(widget=forms.Textarea, help_text="Emails must be space separated")
    role = forms.ModelChoiceField(queryset=Group.objects.all())
    organization = forms.ModelChoiceField(queryset=Organization.objects.all(), required=False)
    project = forms.ModelChoiceField(queryset=Project.objects.all(), required=False)
    registration = forms.ModelChoiceField(queryset=Registration.objects.all(), required=False)

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.request = kwargs.pop("request", None)
        super().__init__(*args, **kwargs)

    def clean_emails(self) -> dict:
        errors = []
        for e in self.cleaned_data["emails"].split():
            try:
                validate_email(e)
            except ValidationError:
                errors.append(e)
        if errors:
            raise ValidationError("Invalid emails {}".format(", ".join(errors)))
        return self.cleaned_data["emails"]

    def clean(self) -> None:
        found = [
            self.cleaned_data.get(x) for x in ["organization", "project", "registration"] if self.cleaned_data.get(x)
        ]
        if not found:
            raise ValidationError("You must set one scope")
        if len(found) > 1:
            raise ValidationError("You must set only one scope")


def build_arg_dict_from_dict(data_dict: dict, mapping_dict: dict) -> dict:
    return {key: data_dict.get(value) for key, value in mapping_dict.items()}


class ADUSerMixin(ExtraButtonsMixin, admin.ModelAdmin[User]):
    ad_form_class = LoadUsersForm
    Results = namedtuple("Results", "created,missing,updated,errors")

    def _get_ad_form(self, request: HttpRequest) -> Form:
        if request.method == "POST":
            return self.ad_form_class(request.POST, request=request)
        return self.ad_form_class(request=request)

    def _sync_ad_data(self, user: "User") -> None:
        ms_graph = MicrosoftGraphAPI()
        if user.profile and user.profile.ad_uuid:
            filters = [{"uuid": user.profile.ad_uuid}, {"email": user.email}]
        else:
            filters = [{"email": user.email}]

        for _filter in filters:
            try:
                user_data = ms_graph.get_user_data(**_filter)
                user_args = build_arg_dict_from_dict(user_data, DJANGO_USER_MAP)
                for field, value in user_args.items():
                    setattr(user, field, value or "")
                user.save()
                break
            except Http404:
                pass
        else:
            raise Http404

    @button(label="AD Sync", permission="account.can_sync_with_ad")  # type: ignore[arg-type]
    def sync_multi(self, request: HttpRequest) -> None:
        not_found = []
        try:
            for user in self.get_queryset(request):
                try:
                    self._sync_ad_data(user)  # type: ignore [arg-type]
                except Http404:
                    not_found.append(str(user))
            if not_found:
                self.message_user(
                    request,
                    f"These users were not found: {', '.join(not_found)}",
                    messages.WARNING,
                )
            else:
                self.message_user(
                    request,
                    "Active Directory data successfully fetched",
                    messages.SUCCESS,
                )
        except Exception as e:
            logger.exception(e)
            self.message_user(request, str(e), messages.ERROR)

    @button(label="Sync", permission="account.can_sync_with_ad")  # type: ignore[arg-type]
    def sync_single(self, request: HttpRequest, pk: str) -> HttpResponse:  # type: ignore[return]
        try:
            self._sync_ad_data(self.get_object(request, pk))  # type: ignore[arg-type]
            self.message_user(request, "Active Directory data successfully fetched", messages.SUCCESS)
        except Exception as e:
            logger.exception(e)
            self.message_user(request, str(e), messages.ERROR)

    @button(permission="account.can_load_from_ad")  # type: ignore[arg-type]
    def load_ad_users(self, request: "AuthHttpRequest") -> TemplateResponse:  # noqa: C901, PLR0912, PLR0915
        ctx = self.get_common_context(
            request,
            None,
            change=True,
            is_popup=False,
            save_as=False,
            has_delete_permission=False,
            has_add_permission=False,
            has_change_permission=True,
        )
        form = self._get_ad_form(request)
        if request.method == "POST" and form.is_valid():
            emails = set(form.cleaned_data["emails"].split())
            role = form.cleaned_data["role"]
            organization = form.cleaned_data.get("organization", None)
            project = form.cleaned_data.get("project", None)
            registration = form.cleaned_data.get("registration", None)
            users_to_bulk_create = []
            users_role_to_bulk_create = []
            existing = set(User.objects.filter(email__in=emails).values_list("email", flat=True))
            results = self.Results([], [], [], [])
            try:
                ms_graph = MicrosoftGraphAPI()
                for email in emails:
                    try:
                        if email in existing:
                            user = User.objects.get(email=email)
                            if config.GRAPH_API_ENABLED:
                                self._sync_ad_data(user)
                            results.updated.append(user)
                        elif config.GRAPH_API_ENABLED:
                            user_data = ms_graph.get_user_data(email=email)
                            user_args = build_arg_dict_from_dict(user_data, DJANGO_USER_MAP)
                            user = User(**user_args)
                            if user.first_name is None:
                                user.first_name = ""
                            if user.last_name is None:
                                user.last_name = ""
                        else:
                            user = User.objects.create(email=email, username=email)

                        user.set_unusable_password()
                        users_to_bulk_create.append(user)
                        results.created.append(user)

                        users_role_to_bulk_create.append(
                            AuroraRole(
                                role=role,
                                organization=organization,
                                registration=registration,
                                project=project,
                                user=user,
                            )
                        )
                    except HTTPError as e:
                        if e.response.status_code != 404:
                            raise
                        results.missing.append(email)
                    except Http404:
                        results.missing.append(email)
                User.objects.bulk_create(users_to_bulk_create)
                AuroraRole.objects.bulk_create(users_role_to_bulk_create, ignore_conflicts=True)
                ctx["results"] = results
                return TemplateResponse(request, "admin/aurorauser/load_users.html", ctx)
            except MicrosoftGraphAPIError as e:
                self.message_user(request, str(e), messages.ERROR)
            except Exception as e:
                logger.exception(e)
                raise
                self.message_user(request, "UnHandled Error", messages.ERROR)

        ctx["form"] = form
        return TemplateResponse(request, "admin/aurorauser/load_users.html", ctx)
