from django.contrib.admin import register

from ..models import Record, Registration
from .record import RecordAdmin
from .registration import RegistrationAdmin

register(Registration)(RegistrationAdmin)
register(Record)(RecordAdmin)
