from datetime import datetime

from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views import View

from aurora.core.models import Organization, Project
from aurora.core.utils import get_session_id, last_day_of_month, render
from aurora.counters.models import Counter
from aurora.registration.models import Registration

User = get_user_model()


@login_required()
def index(request):
    if not request.user.has_perm("counters.view_counter"):
        raise PermissionDenied("----")
    if request.user.is_superuser:
        filters = {}
    else:
        filters = {"members__user": request.user}
    context = {
        "organizations": Organization.objects.filter(**filters).order_by("name"),
    }
    return render(request, "counters/index.html", context)


@login_required()
def org_index(request, org):
    o: Organization = Organization.objects.get(slug=org)
    if not request.user.has_perm("counters.view_counter", o):
        raise PermissionDenied("----")
    if request.user.is_superuser:
        filters = {}
    else:
        filters = {"members__user": request.user}
    context = {
        "organization": o,
        "projects": o.projects.filter(**filters),
    }
    return render(request, "counters/org_index.html", context)


@login_required()
def project_index(request, org, prj):
    o: Organization = Organization.objects.get(slug=org)
    p: Project = Project.objects.get(organization=o, pk=prj)
    if not request.user.has_perm("counters.view_counter", p):
        raise PermissionDenied("----")
    context = {
        "organization": o,
        "project": p,
        "registrations": p.registrations.filter(members__user=request.user),
    }
    return render(request, "counters/project.html", context)


class ChartView(UserPassesTestMixin, View):
    permission_denied_message = "----"
    login_url = "/login/"

    def test_func(self):
        return self.request.user.is_authenticated

    def get_registration(self, request, org, prj, reg_pk) -> Registration:
        reg = get_object_or_404(Registration, project__organization__slug=org, project_id=prj, id=reg_pk)
        if not request.user.has_perm("counters.view_counter", reg):
            raise PermissionDenied("----")
        return reg

    def handle_no_permission(self):
        return HttpResponseRedirect("/")


class MonthlyDataView(ChartView):
    def get(self, request, org, prj, registration_id):
        registration = self.get_registration(request, org, prj, registration_id)
        qs = Counter.objects.filter(registration_id=registration_id).order_by("day")
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


class MonthlyChartView(ChartView):
    def get(self, request, org, prj, registration):
        reg: Registration = self.get_registration(request, org, prj, registration)
        first: [Counter] = reg.counters.first()
        latest: [Counter] = reg.counters.last()
        m = request.GET.get("m", None)
        if not m:
            month = timezone.now().month
            year = timezone.now().year
            date = timezone.now()
        else:
            year, month = m.split("-")
            date = datetime(int(year), int(month), 1).date()

        context = {
            "date": date,
            "month": month,
            "year": year,
            "project": reg.project,
            "organization": reg.organization,
            "registration": reg,
            "first": first,
            "latest": latest,
            "token": get_session_id(),
            # "years": range(first.day.year, latest.day.year)
        }
        return render(request, "counters/chart_month.html", context)


class DayChartView(ChartView):
    def get(self, request, org, prj, registration):
        reg: Registration = self.get_registration(request, org, prj, registration)
        day = request.GET.get("day", datetime.today().strftime("%Y-%m-%d"))
        date = datetime.strptime(day, "%Y-%m-%d")

        original: Counter = reg.counters.filter(day=day).first()
        context = {
            "project": reg.project,
            "organization": reg.organization,
            "date": date,
            "month": date.month,
            "day": day,
            "registration": reg,
            "original": original,
            "token": get_session_id(),
            # "years": range(first.day.year, latest.day.year)
        }
        return render(request, "counters/chart_day.html", context)
