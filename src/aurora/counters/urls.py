from django.urls import path

from .views import MonthlyChartView, MonthlyDataView, index, project_index

app_name = "charts"

urlpatterns = [
    path("<str:org>/", index, name="index"),
    path("<str:org>/<int:prj>/", project_index, name="project-index"),
    path("<str:org>/<int:prj>/<int:registration>/monthly/", MonthlyChartView.as_view(), name="registration"),
    path("<str:org>/<int:prj>/data/<int:registration_id>/monthly/", MonthlyDataView.as_view(), name="monthly_data"),
]
