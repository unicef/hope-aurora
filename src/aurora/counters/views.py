from datetime import datetime

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views import View

from aurora.core.utils import get_session_id, last_day_of_month, render
from aurora.counters.models import Counter
from aurora.registration.models import Registration


@login_required()
def index(request):
    regs = Registration.objects.filter(roles__user=request.user, roles__role__permissions__codename="view_counter")
    context = {"registrations": regs}
    return render(request, "counters/index.html", context)


class ChartView(UserPassesTestMixin, View):
    permission_denied_message = "----"
    login_url = "/login/"

    def test_func(self):
        return self.request.user.is_authenticated

    def get_registration(self, request, pk) -> Registration:
        reg = get_object_or_404(Registration, id=pk)
        if not request.user.has_perm("view_counter", reg):
            raise PermissionDenied("----")
        return reg

    def handle_no_permission(self):
        return HttpResponseRedirect("/")


class MonthlyDataView(ChartView):
    def get(self, request, registration_id):
        registration = self.get_registration(request, registration_id)
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
            labels = [d.strftime("%-d, %a") for d in values.keys()]
        period = date.strftime("%B %Y")
        data = {
            "datapoints": qs.all().count(),
            "label": f"{registration} {period}",
            "day": date.strftime("%Y-%m-%d"),
            "total": total,
            "labels": labels,
            "data": list(values.values()),
        }
        response = JsonResponse(data)
        # response["Cache-Control"] = "max-age=315360000"
        # response["Last-Modified"] = "max-age=315360000"
        # response["ETag"] = etag
        return response


def daily_data(request, registration, record):
    pass


class MonthlyChartView(ChartView):
    def get(self, request, registration):
        reg: Registration = self.get_registration(request, registration)
        first: [Counter] = reg.counters.first()
        latest: [Counter] = reg.counters.last()
        if not latest:
            latest = timezone.now()
        context = {
            "registration": reg,
            "first": first,
            "latest": latest,
            "token": get_session_id(),
            # "years": range(first.day.year, latest.day.year)
        }
        return render(request, "counters/chart_month.html", context)
