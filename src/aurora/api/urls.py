from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import viewsets

app_name = "api"

router = DefaultRouter()
router.register(r"counter", viewsets.CounterViewSet)
router.register(r"field", viewsets.FlexFormFieldViewSet)
router.register(r"flatpage", viewsets.FlatPageViewSet)
router.register(r"form", viewsets.FlexFormViewSet)
router.register(r"formset", viewsets.FormSetViewSet)
router.register(r"registration", viewsets.RegistrationViewSet)
router.register(r"template", viewsets.TemplateViewSet)
router.register(r"template", viewsets.TemplateViewSet)
router.register(r"user", viewsets.UserViewSet)
router.register(r"validator", viewsets.ValidatorViewSet)
router.register(r"project", viewsets.ProjectViewSet)
router.register(r"record", viewsets.RecordViewSet)
router.register(r"organization", viewsets.OrganizationViewSet)
router.register(r"validator", viewsets.ValidatorViewSet)

urlpatterns = [
    path("", include(router.urls)),
    path("sys/", viewsets.system_info),
]
