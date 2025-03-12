from django.http import HttpResponseForbidden
from rest_framework.routers import APIRootView, DefaultRouter


class AuroraAPIRootView(APIRootView):
    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return super().get(request, *args, **kwargs)
        return HttpResponseForbidden()


class AuroraRouter(DefaultRouter):
    APIRootView = AuroraAPIRootView
