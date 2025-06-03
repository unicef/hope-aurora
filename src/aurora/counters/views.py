from datetime import datetime
from typing import Any

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.forms import Media
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.utils import timezone
from django.utils.functional import cached_property
from django.views.generic import TemplateView

from aurora.core.models import Organization, Project
from aurora.core.utils import get_session_id, last_day_of_month, render
from aurora.core.version_media import VersionMedia
from aurora.counters.models import Counter
from aurora.registration.models import Registration
from aurora.web.views.mixins import MediaMixin

User = get_user_model()


class ChartBase(MediaMixin, LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    def has_permission(self) -> bool:
        return self.request.user.has_perm("counters.view_counter")

    @cached_property
    def registration(self) -> "Registration":
        return Registration.objects.select_related().get(
            project__organization__slug=self.kwargs["org"],
            project_id=self.kwargs["prj"],
            id=self.kwargs["registration"],
        )


class ChartIndex(ChartBase):
    template_name = "counters/index.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        if self.request.user.is_superuser:
            filters = {}
        else:
            filters = {"members__user": self.request.user}
        organizations = Organization.objects.filter(**filters).order_by("name")

        return super().get_context_data(organizations=organizations, title="Offices", **kwargs)


class OrganizationIndex(ChartBase):
    template_name = "counters/org_index.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        o: Organization = Organization.objects.get(slug=self.kwargs["org"])
        if self.request.user.is_superuser:
            filters = {}
        else:
            filters = {"members__user": self.request.user}
        context = {
            "organization": o,
            "projects": o.projects.filter(**filters),
            "title": "Programmes",
        }

        return super().get_context_data(**context, **kwargs)


class ProjectIndex(ChartBase):
    template_name = "counters/project_index.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        o: Organization = Organization.objects.get(slug=self.kwargs["org"])
        p: Project = Project.objects.get(organization=o, pk=self.kwargs["prj"])
        context = {
            "organization": o,
            "project": p,
            "registrations": p.registrations.filter(members__user=self.request.user),
            "title": "Registrations",
        }

        return super().get_context_data(**context, **kwargs)


class MonthlyDataView(ChartBase):
    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        registration = Registration.objects.select_related().get(
            project__organization__slug=self.kwargs["org"],
            project_id=self.kwargs["prj"],
            id=self.kwargs["registration_id"],
        )
        qs = Counter.objects.filter(registration_id=self.kwargs["registration_id"]).order_by("day")
        param_month = request.GET.get("m", None)
        total = 0
        if param_month:
            date = datetime.strptime(param_month, "%Y-%m-%d")
        else:
            date = timezone.now()

        qs = qs.filter(day__month=date.month)
        last_day = last_day_of_month(date)
        days = list(range(1, 1 + last_day.day))
        labels = [last_day.replace(day=d).strftime("%-d, %a") for d in days]
        values = {}
        for d in range(1, last_day.day + 1):
            dt = date.replace(day=d).date()
            values[dt] = {"total": 0, "pk": 0}

        for record in qs.all():
            values[record.day] = {"total": record.records, "pk": record.pk}
            total += record.records

        if not labels:
            labels = [d.strftime("%-d, %a") for d in values]
        period = date.strftime("%B %Y")
        data = {
            "datapoints": qs.all().count(),
            "label": f"{registration} {period}",
            "day": date.strftime("%Y-%m-%d"),
            "total": total,
            "labels": labels,
            "data": list(values.values()),
        }
        return JsonResponse(data)


class MonthlyChartView(ChartBase):
    template_name = "counters/project_chart_month.html"

    @property
    def media(self) -> Media:
        extra = "" if settings.DEBUG else ".min"
        media = super().media

        js_files = [
            "admin/js/vendor/jquery/jquery%s.js" % extra,
            "admin/js/jquery.init.js",
            "jquery.compat%s.js" % extra,
            "https://cdnjs.cloudflare.com/ajax/libs/moment.js/2.29.1/moment.min.js",
            "https://cdn.jsdelivr.net/npm/chart.js",
            "https://cdnjs.cloudflare.com/ajax/libs/chartjs-plugin-datalabels/2.0.0/chartjs-plugin-datalabels.min.js",
            "https://cdnjs.cloudflare.com/ajax/libs/chartjs-plugin-annotation/1.4.0/chartjs-plugin-annotation.min.js",
        ]

        mine = VersionMedia(js=js_files)

        return media + mine

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        reg = Registration.objects.select_related().get(
            project__organization__slug=self.kwargs["org"],
            project_id=self.kwargs["prj"],
            id=self.kwargs["registration"],
        )
        first: Counter = reg.counters.first()
        latest: Counter = reg.counters.last()

        m = self.request.GET.get("m", None)
        if not m:
            month = timezone.now().month
            year = timezone.now().year
            date = timezone.now().date()
        else:
            year, month = map(int, m.split("-"))
            date = datetime(year, month, 1).date()
        context = {
            "title": reg,
            "date": date,
            "month": month,
            "year": year,
            "project": reg.project,
            "organization": reg.organization,
            "registration": reg,
            "first": first,
            "latest": latest,
            "token": get_session_id(),
        }

        return super().get_context_data(**context)


class DayChartView(ChartBase):
    @property
    def media(self) -> Media:
        extra = "" if settings.DEBUG else ".min"
        media = super().media

        js_files = [
            "admin/js/vendor/jquery/jquery%s.js" % extra,
            "admin/js/jquery.init.js",
            "jquery.compat%s.js" % extra,
            "https://cdnjs.cloudflare.com/ajax/libs/moment.js/2.29.1/moment.min.js",
            "https://cdn.jsdelivr.net/npm/chart.js",
            "https://cdnjs.cloudflare.com/ajax/libs/chartjs-plugin-datalabels/2.0.0/chartjs-plugin-datalabels.min.js",
            "https://cdnjs.cloudflare.com/ajax/libs/chartjs-plugin-annotation/1.4.0/chartjs-plugin-annotation.min.js",
        ]

        mine = VersionMedia(js=js_files)

        return media + mine

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        reg = self.registration
        day = request.GET.get("day", datetime.today().strftime("%Y-%m-%d"))
        date = datetime.strptime(day, "%Y-%m-%d")

        self.original: Counter = reg.counters.filter(day=day).first()
        context = {
            "project": reg.project,
            "organization": reg.organization,
            "date": date,
            "month": date.month,
            "day": day,
            "media": self.media,
            "registration": reg,
            "original": self.original,
            "token": get_session_id(),
            # "years": range(first.day.year, latest.day.year)
        }
        return render(request, "counters/project_chart_day.html", context)
