from django.http import HttpResponseForbidden
from rest_framework.routers import DefaultRouter, APIRootView


class AuroraAPIRootView(APIRootView):
    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return super().get(request, *args, **kwargs)
        else:
            return HttpResponseForbidden()


class AuroraRouter(DefaultRouter):
    APIRootView = AuroraAPIRootView
