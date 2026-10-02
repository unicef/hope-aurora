from django.urls import path
from unicef_security.views import UNICEFLogoutView

from .views import (
    HomeView,
    LoginRouter,
    PageView,
    ProbeView,
    QRCodeView,
    RegistrarLoginView,
    RegistrarLogoutView,
    offline,
)

urlpatterns = [
    path("", HomeView.as_view(), name="index"),
    path("login/", RegistrarLoginView.as_view(), name="login"),
    path("logout/", RegistrarLogoutView.as_view(), name="logout"),
    path("unicef-logout/", UNICEFLogoutView.as_view(), name="unicef-logout"),
    path("logged-in/", LoginRouter.as_view(), name="logged-in"),
    path("page/<str:page>/", PageView.as_view(), name="page"),
    path("probe/", ProbeView.as_view(), name="probe"),
    path("qrcode/", QRCodeView.as_view(), name="qrcode"),
    path("offline/", offline, name="offline"),
]
