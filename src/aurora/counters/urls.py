from django.urls import path

from .views import DayChartView, MonthlyChartView, MonthlyDataView, index, org_index, project_index

app_name = "charts"

urlpatterns = [
    path("", index, name="index"),
    path("<str:org>/", org_index, name="org-index"),
    path("<str:org>/<int:prj>/", project_index, name="project-index"),
    path("<str:org>/<int:prj>/<int:registration>/monthly/", MonthlyChartView.as_view(), name="monthly"),
    path("<str:org>/<int:prj>/<int:registration>/daily/", DayChartView.as_view(), name="daily"),
    path("<str:org>/<int:prj>/data/<int:registration_id>/monthly/", MonthlyDataView.as_view(), name="monthly_data"),
]
