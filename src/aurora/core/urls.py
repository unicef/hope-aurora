from django.urls import path

from .views import OptionsListView

urlpatterns = [
    path("options/<str:name>/", OptionsListView.as_view(), name="optionset"),
    path("options/<str:name>/<str:parent>/", OptionsListView.as_view(), name="optionset"),
    path(
        "options/<str:name>/<int:pk>/<str:parent>/",
        OptionsListView.as_view(),
        name="optionset",
    ),
]
