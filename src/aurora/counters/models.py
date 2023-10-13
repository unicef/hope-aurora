from collections import defaultdict
from datetime import datetime, timedelta

from django.db import models
from django.db.models import Count
from django.db.models.functions import ExtractHour, TruncDay
from django.utils.functional import cached_property

from aurora.registration.models import Record, Registration


class CounterManager(models.Manager):
    def collect(self, *, registrations=None):
        result = {"registration": 0, "records": 0, "days": 0, "details": {}}
        today = datetime.today()
        yesterday = datetime.combine(today - timedelta(days=1), datetime.max.time())
        selection = Registration.objects.filter(archived=False)

        def annotate(qs):
            return (
                qs.annotate(hour=ExtractHour("timestamp"), day=TruncDay("timestamp"))
                .values("day", "hour")
                .annotate(c=Count("id"))
                .order_by("day", "hour")
            )

        if registrations:
            selection = selection.filter(id__in=registrations)
        querysets = []
        for registration in selection:
            result["registration"] += 1
            result["details"][registration.slug] = {"range": [], "days": 0}
            latest = Counter.objects.filter(registration=registration).order_by("-day").first()
            if latest:
                latest = latest.day + timedelta(days=1)
            else:
                latest = datetime.min
            qs = annotate(Record.objects.filter(registration=registration, timestamp__range=(latest, yesterday)))
            today_data = annotate(Record.objects.filter(registration=registration, timestamp__date=today))
            querysets.append(qs)
            counter = defaultdict(lambda: {"records": 0, "extra": {}})
            for q in [qs, today_data]:
                for match in q.all():
                    counter[match["day"]]["records"] += match["c"]
                    counter[match["day"]]["extra"][match["hour"]] = match["c"]
                    result["days"] += 1
            for day, values in counter.items():
                result["records"] += values["records"]
                result["details"][registration.slug]["days"] += 1
                if today.date() == day.date():
                    Counter.objects.update_or_create(
                        registration=registration,
                        day=day,
                        defaults={
                            "records": values["records"],
                            "details": {"hours": values["extra"]},
                        },
                    )
                else:
                    Counter.objects.get_or_create(
                        registration=registration,
                        day=day,
                        defaults={
                            "records": values["records"],
                            "details": {"hours": values["extra"]},
                        },
                    )
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

    def __str__(self):
        try:
            return f"{self.registration} {self.day}"
        except Exception:
            return f"Counter #{self.pk}"

    @cached_property
    def hourly(self):
        return [self.details["hours"].get(str(x), 0) for x in range(23)]
