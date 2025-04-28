from django.urls import path

from .views import OptionsListVersion, OptionsListView

urlpatterns = [
    path("options/<str:name>/", OptionsListView.as_view(), name="optionset"),
    path("options/<str:name>/<int:version>/", OptionsListView.as_view(), name="optionset-versioned"),
    path("options/<str:name>/version/", OptionsListVersion.as_view(), name="optionset-version"),
    path("options/<str:name>/<str:parent>/", OptionsListView.as_view(), name="optionset"),
    path(
        "options/<str:name>/<int:pk>/<str:parent>/",
        OptionsListView.as_view(),
        name="optionset",
    ),
]
