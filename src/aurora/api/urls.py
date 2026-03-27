from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from . import viewsets
from .router import AuroraRouter

app_name = "api"

router = AuroraRouter()
router.register(r"counter", viewsets.CounterViewSet)
router.register(r"field", viewsets.FlexFormFieldViewSet)
router.register(r"flatpage", viewsets.FlatPageViewSet)
router.register(r"form", viewsets.FlexFormViewSet)
router.register(r"formset", viewsets.FormSetViewSet)
router.register(r"organization", viewsets.OrganizationViewSet)
router.register(r"project", viewsets.ProjectViewSet)
router.register(r"record", viewsets.RecordViewSet)
router.register(r"registration", viewsets.RegistrationViewSet)
router.register(r"template", viewsets.TemplateViewSet)
router.register(r"user", viewsets.UserViewSet)
router.register(r"validator", viewsets.ValidatorViewSet)

urlpatterns = [
    path("", include(router.urls)),
    path("sys/", viewsets.system_info),
    path("schema/", SpectacularAPIView.as_view(), name="schema"),
    path("rest/swagger/", SpectacularSwaggerView.as_view(url_name="api:schema"), name="swagger-ui"),
]
