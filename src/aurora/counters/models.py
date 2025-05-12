from collections import defaultdict
from datetime import datetime, timedelta
from typing import TYPE_CHECKING

import pytz
from django.conf import settings
from django.db import models
from django.db.models import Count
from django.db.models.functions import ExtractHour, TruncDay
from django.utils import timezone
from django.utils.functional import cached_property

from aurora.registration.models import Record, Registration

if TYPE_CHECKING:
    from typing import Sequence

    from django.db.models import QuerySet

    from aurora.types.counters.models import CollectCounter, CollectResult


class CounterManager(models.Manager):
    def collect(
        self, *, registrations: "Sequence[Registration] | None" = None
    ) -> "tuple[list[QuerySet[Counter]], CollectResult]":
        result: "CollectResult" = {"registration": 0, "records": 0, "days": 0, "details": {}}
        tz = pytz.timezone(settings.TIME_ZONE)
        today = timezone.now()
        yesterday = datetime.combine(today - timedelta(days=1), datetime.max.time()).astimezone(tz)
        selection = Registration.objects.filter(archived=False)
        if registrations:
            selection = selection.filter(id__in=registrations)

        def annotate(qs: "QuerySet") -> "QuerySet":
            return (
                qs.annotate(hour=ExtractHour("timestamp"), day=TruncDay("timestamp"))
                .values("day", "hour")
                .annotate(c=Count("id"))
                .order_by("day", "hour")
            )

        querysets = []
        for registration in selection:
            result["registration"] += 1
            result["details"][registration.slug] = {"range": [], "days": 0}
            last_counter = Counter.objects.filter(registration=registration).order_by("-day").first()

            if last_counter:
                start_date = last_counter.day + timedelta(days=1)
                start_date = datetime.combine(start_date, datetime.min.time()).astimezone(tz)
            else:
                start_date = datetime(2000, 1, 1, tzinfo=tz)
            # Query historical data
            historical_qs = annotate(
                Record.objects.filter(registration=registration, timestamp__range=(start_date, yesterday))
            )
            # Query today's data
            today_start = today.replace(hour=0, minute=0, second=0, microsecond=0)
            today_qs = annotate(Record.objects.filter(registration=registration, timestamp__gte=today_start))
            querysets.append(historical_qs)

            # Process queries and update counters
            counter: defaultdict[str, CollectCounter] = defaultdict(lambda: {"records": 0, "extra": {}})
            # Process both historical and today's data
            for qs in [historical_qs, today_qs]:
                for match in qs.all():
                    day = match["day"]
                    hour = match["hour"]
                    count = match["c"]

                    counter[day]["records"] += count
                    counter[day]["extra"][hour] = count
                    result["days"] += 1

            # Update database with counter information
            for day, values in counter.items():
                records_count = values["records"]
                result["records"] += records_count
                result["details"][registration.slug]["days"] += 1

                defaults = {
                    "records": records_count,
                    "details": {"hours": values["extra"]},
                }

                # Different handling for today vs. historical data
                if today.date() == day.date():
                    Counter.objects.update_or_create(registration=registration, day=day, defaults=defaults)
                else:
                    Counter.objects.get_or_create(registration=registration, day=day, defaults=defaults)
        return querysets, result


class Counter(models.Model):
    registration = models.ForeignKey(Registration, on_delete=models.CASCADE, related_name="counters")
    day = models.DateField(blank=True, null=True, db_index=True)
    records = models.IntegerField(default=0, blank=True, null=True)
    details = models.JSONField(default=dict, blank=True)

    objects = CounterManager()

    class Meta:
        unique_together = ("registration", "day")
        get_latest_by = "day"
        ordering = ("-day",)

    def __str__(self) -> str:
        try:
            return f"{self.registration} {self.day}"
        except Exception:  # noqa: BLE001
            return f"Counter #{self.pk}"

    @cached_property
    def hourly(self) -> list[str]:
        return [self.details["hours"].get(str(x), 0) for x in range(23)]
