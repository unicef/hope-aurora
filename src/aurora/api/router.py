from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.routers import APIRootView, DefaultRouter


class AuroraAPIRootView(APIRootView):
    def get(self, request: Request, *args, **kwargs) -> Response:
        if request.user.is_authenticated:
            return super().get(request, *args, **kwargs)
        return Response({}, status=status.HTTP_401_UNAUTHORIZED)


class AuroraRouter(DefaultRouter):
    APIRootView = AuroraAPIRootView
