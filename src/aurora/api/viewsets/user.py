from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils.translation import get_language
from rest_framework import serializers
from rest_framework.authentication import SessionAuthentication
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .base import SmartViewSet

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    permissions = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ("pk", "is_staff", "permissions")

    def get_permissions(self, obj):
        return obj.get_all_permissions()


class UserViewSet(SmartViewSet):
    """
    This viewset automatically provides `list` and `retrieve` actions.
    """

    queryset = User.objects.all()
    serializer_class = UserSerializer

    @action(detail=False, permission_classes=[AllowAny], authentication_classes=[SessionAuthentication])
    def me(self, request):
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
