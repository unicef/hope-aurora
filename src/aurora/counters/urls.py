from django.urls import path

from .views import ChartIndex, DayChartView, MonthlyChartView, MonthlyDataView, OrganizationIndex, ProjectIndex

app_name = "charts"

urlpatterns = [
    path("", ChartIndex.as_view(), name="index"),
    path("<str:org>/", OrganizationIndex.as_view(), name="org-index"),
    path("<str:org>/<int:prj>/", ProjectIndex.as_view(), name="project-index"),
    path("<str:org>/<int:prj>/<int:registration>/monthly/", MonthlyChartView.as_view(), name="monthly"),
    path("<str:org>/<int:prj>/<int:registration>/daily/", DayChartView.as_view(), name="daily"),
    path("<str:org>/<int:prj>/data/<int:registration_id>/monthly/", MonthlyDataView.as_view(), name="monthly_data"),
]
