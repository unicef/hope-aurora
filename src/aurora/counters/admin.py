import logging

from admin_extra_buttons.decorators import button
from adminfilters.autocomplete import AutoCompleteFilter
from django.contrib.admin import register
from django.db.transaction import atomic
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from smart_admin.modeladmin import SmartModelAdmin

from ..core.utils import is_root
from ..registration.admin.paginator import LargeTablePaginator
from .forms import ChartForm
from .models import Counter

logger = logging.getLogger(__name__)


def get_token(request):
    return str(request.user.last_login.utcnow().timestamp())


@register(Counter)
class CounterAdmin(SmartModelAdmin):
    list_display = ("registration", "day", "records")
    list_filter = (("registration", AutoCompleteFilter), "day")
    date_hierarchy = "day"
    autocomplete_fields = ("registration",)
    change_form_template = None
    paginator = LargeTablePaginator
    show_full_result_count = False

    def get_exclude(self, request, obj=None):
        return ("details",)

    def get_readonly_fields(self, request, obj=None):
        if is_root(request):
            return []
        return ("registration", "day", "records")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return is_root(request)

    @button()
    def chart(self, request):
        ctx = self.get_common_context(request)
        if request.method == "POST":
            form = ChartForm(request.POST)
            if form.is_valid():
                registration = form.cleaned_data["registration"]
                return HttpResponseRedirect(reverse("charts:registration", args=[registration.pk]))
        else:
            form = ChartForm()
        ctx["form"] = form
        return render(request, "admin/counters/counter/chart.html", ctx)

    @button()
    def collect(self, request):
        try:
            with atomic():
                querysets, result = Counter.objects.collect()
                self.message_user(request, str(result))
        except Exception as e:
            logger.exception(e)
            self.message_error_to_user(request, e)
