import datetime
import logging
import secrets
import sys

from django import forms

import djclick as click
import pytz

from aurora.core import fields
from aurora.core.models import OptionSet
from aurora.registration.models import Record

logger = logging.getLogger(__name__)


class NotRunningInTTYError(Exception):
    pass


@click.command()  # noqa: C901
def demo(**kwargs):
    from aurora.core.models import FlexForm, Validator
    from aurora.registration.models import Registration

    vf1, __ = Validator.objects.update_or_create(
        name='name must start with "S"',
        defaults={"target": Validator.FORM, "code": "value.family_name.startsWith('S');"},
    )
    v1, __ = Validator.objects.get_or_create(
        name="max_length_25",
        defaults={
            "message": "String too long (max 25.chars)",
            "target": Validator.FIELD,
            "code": "value.length<25;",
        },
    )
    v2, __ = Validator.objects.get_or_create(
        name="date_after_3000",
        defaults={
            "message": "Date must be after 3000-12-01",
            "target": Validator.FIELD,
            "code": """var limit = Date.parse("3000-12-01");
var dt = Date.parse(value);
dt > limit;""",
        },
    )
    OptionSet.objects.get_or_create(
        name="italian_locations",
        defaults={
            "data": "1:Rome\n2:Milan",
            "separator": ":",
        },
    )

    hh, __ = FlexForm.objects.get_or_create(name="Demo Household", defaults={"validator": vf1})
    hh.fields.get_or_create(label="Family Name", field_type=forms.CharField, required=True)

    ind, __ = FlexForm.objects.get_or_create(name="Demo Individual")
    ind.fields.get_or_create(
        label="First Name",
        defaults={"field_type": forms.CharField, "required": True, "validator": v1},
    )
    ind.fields.get_or_create(label="Last Name", defaults={"field_type": forms.CharField, "validator": v1})
    ind.fields.get_or_create(label="Date Of Birth", defaults={"field_type": forms.DateField, "validator": v2})

    ind.fields.get_or_create(
        label="Options",
        defaults={"field_type": forms.ChoiceField, "choices": "opt 1, opt 2, opt 3"},
    )

    ind.fields.get_or_create(
        label="Location",
        defaults={"field_type": fields.SelectField, "choices": "italian_locations"},
    )

    hh.formsets.get_or_create(name="individuals", defaults={"flex_form": ind})

    reg, __ = Registration.objects.get_or_create(name="Demo Registration1", defaults={"flex_form": hh}, active=True)
    today = datetime.datetime.today()

    last_month = datetime.datetime.combine(today - datetime.timedelta(days=31), datetime.datetime.min.time())
    prev_month = datetime.datetime.combine(last_month.replace(day=1), datetime.time.max) - datetime.timedelta(days=1)

    Record.objects.all().delete()
    ranges = (
        (5, 20),
        (5, 30),
    )
    from faker import Faker
    from freezegun import freeze_time

    fake = Faker()
    for month in range(prev_month.month, last_month.month):
        sys.stdout.write(f"{month}: ")
        for day in range(1, 31):
            sys.stdout.write(f"{day},")
            sys.stdout.flush()
            for _ in range(secrets.choice(range(*ranges[0]))):
                hour = secrets.randbelow(24)
                for _ in range(secrets.choice(range(*ranges[1]))):
                    minute = secrets.randbelow(60)
                    ts = datetime.datetime(last_month.year, month, day, hour, minute, tzinfo=pytz.utc)
                    with freeze_time(ts):
                        Record.objects.create(registration=reg, remote_ip=fake.ipv4(), timestamp=ts)
        sys.stdout.write("\n")
    from aurora.counters.models import Counter

    Counter.objects.collect()
