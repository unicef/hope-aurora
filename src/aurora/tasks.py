import logging

import dramatiq
from django.db.transaction import atomic
from dramatiq_crontab import interval
from sentry_sdk.crons import monitor

from aurora.counters.models import Counter

logger = logging.getLogger(__name__)


@monitor(monitor_slug="collect-numbers")
@interval(seconds=30)
@dramatiq.actor
def collect() -> None:
    try:
        with atomic():
            Counter.objects.collect()
    except Exception as e:
        logger.exception(e)
        raise


@dramatiq.actor
def remove_records(pk: str) -> None:
    from aurora.registration.models import Record

    Record.objects.filter(registration__idp=pk, registration__archived=True, registration__active=False).delete()
