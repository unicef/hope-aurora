from django.urls import path

from .views import (
    QRVerify,
    RegisterAuthView,
    RegisterCompleteView,
    RegisterRouter,
    RegisterView,
    RegistrationDataApi,
    RegistrationDataView,
    authorize_cookie,
    get_pwa_enabled,
    registrations,
)

urlpatterns = [
    path("route/", RegisterRouter.as_view(), name="registration-router"),
    path("register/complete/<int:reg>/<int:rec>/", RegisterCompleteView.as_view(), name="register-done"),
    path("register/qr/<int:pk>/<str:hash>/", QRVerify.as_view(), name="register-verify"),
    path("register/<slug:slug>/", RegisterView.as_view(), name="register"),
    # path("register/<int:pk>/data/", RegistrationDataView.as_view(), name="register-data"),
    path("register/<slug:slug>/data/", RegistrationDataView.as_view(), name="register-data"),
    path("register/<slug:slug>/auth/", RegisterAuthView.as_view(), name="register-auth"),
    path("register/<slug:slug>/<int:version>/", RegisterView.as_view(), name="register"),
    path("api/data/<int:pk>/<int:start>/<int:end>/", RegistrationDataApi.as_view(), name="api"),
    path("registrations/", registrations, name="registrations"),
    path("get_pwa_enabled/", get_pwa_enabled, name="get_pwa_enabled"),
    path("authorize_cookie/", authorize_cookie, name="authorize_cookie"),
]
