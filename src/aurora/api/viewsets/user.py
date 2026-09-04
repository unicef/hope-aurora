from typing import TYPE_CHECKING

from django.urls import reverse
from django.utils.translation import get_language
from rest_framework import serializers
from rest_framework.authentication import SessionAuthentication
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response

from ...security.models import User
from .base import SmartViewSet, StaffOnlyPermission

if TYPE_CHECKING:
    from rest_framework.permissions import _SupportsHasPermission


class UserSerializer(serializers.ModelSerializer):
    permissions = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ("pk", "is_staff", "permissions")

    def get_permissions(self, obj: User) -> set[str]:
        return obj.get_all_permissions()


class UserViewSet(SmartViewSet):
    """Viewset automatically provides `list` and `retrieve` actions.

    Only staff/root users may list or retrieve other users. Regular users can only
    access the ``me`` endpoint which returns their own information.
    """

    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get_permissions(self) -> "list[_SupportsHasPermission]":
        if self.action in ("list", "retrieve"):
            return [StaffOnlyPermission()]
        return [permission() for permission in self.permission_classes]

    @action(
        detail=False,
        permission_classes=[AllowAny],
        authentication_classes=[SessionAuthentication],
    )
    def me(self, request: Request) -> Response:
        response = {
            "perms": [],
            "staff": False,
            "canTranslate": False,
            "languageCode": get_language(),
            "editUrl": "",
            "adminUrl": "",
            "authenticated": request.user.is_authenticated,
        }
        if request.user.is_authenticated:
            response.update(
                {
                    "perms": request.user.get_all_permissions(),
                    "staff": request.user.is_staff,
                    "canTranslate": request.user.is_staff,
                    "editUrl": reverse("admin:i18n_message_get_or_create"),
                    "adminUrl": reverse("admin:index"),
                    "authenticated": request.user.is_authenticated,
                }
            )
        return Response(response)
