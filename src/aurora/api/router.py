from django.http import HttpResponse, HttpResponseForbidden
from rest_framework.request import Request
from rest_framework.routers import APIRootView, DefaultRouter


class AuroraAPIRootView(APIRootView):
    def get(self, request: Request, *args, **kwargs) -> HttpResponse:
        if request.user.is_authenticated:
            return super().get(request, *args, **kwargs)
        return HttpResponseForbidden()


class AuroraRouter(DefaultRouter):
    APIRootView = AuroraAPIRootView
