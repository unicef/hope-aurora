from django.urls import path
from django.views.decorators.csrf import csrf_exempt
from django.views.i18n import set_language

from .views import SmartJavascriptCatalog, editor_info

urlpatterns = [
    path("editor_info/", editor_info, name="editor_info"),
    path("setlang/", csrf_exempt(set_language), name="set_language"),
    path("<str:locale>/", SmartJavascriptCatalog.as_view(), name="javascript-catalog"),
]
