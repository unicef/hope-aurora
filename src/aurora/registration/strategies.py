import base64
from django.db.transaction import atomic

from django.shortcuts import render
from django.urls import reverse
from strategy_field.registry import Registry

from aurora.core.crypto import Crypto
from aurora.core.utils import jsonfy, safe_json, total_size
from aurora.registration.storage import router
from aurora.state import state


class RegistrationStrategy:
    def __init__(self, registration):
        self.registration = registration

    def save(self, fields_data, **kwargs):
        raise NotImplementedError


class SaveToDB(RegistrationStrategy):
    verbose_name = "Save To DB"

    def save(self, fields_data, **kwargs):
        from aurora.registration.models import Record

        fields, files = router.decompress(fields_data)
        crypter = Crypto()
        if self.registration.public_key:
            kwargs = {
                # "storage": self.encrypt(fields_data),
                "files": self.registration.encrypt(files),
                "fields": base64.b64encode(self.registration.encrypt(fields)).decode(),
            }
        elif self.registration.encrypt_data:
            kwargs = {
                # "storage": Crypto().encrypt(fields_data).encode(),
                "files": crypter.encrypt(files).encode(),
                "fields": crypter.encrypt(fields),
            }
        else:
            kwargs = {
                # "storage": safe_json(fields_data).encode(),
                "files": safe_json(files).encode(),
                "fields": jsonfy(fields),
            }
        if self.registration.unique_field_path and not kwargs.get("unique_field", None):
            unique_value = self.registration.get_unique_value(fields)
            kwargs["unique_field"] = unique_value
        if state.request and state.request.user.is_authenticated:
            registrar = state.request.user
        else:
            registrar = None
        kwargs.update(
            {
                "registrar": registrar,
                "size": total_size(fields) + total_size(files),
                "counters": fields_data.get("counters", {}),
                "index1": fields_data.get("index1", None),
            }
        )

        return Record.objects.create(registration=self.registration, **kwargs)


class TransactionTestStrategy(SaveToDB):
    def save(self, fields_data, **kwargs):
        ctx = {
            "fields_data": fields_data,
            "record": None,
        }
        try:
            with atomic():
                ctx["record"] = super().save(fields_data, **kwargs)
                raise ArithmeticError
        except ArithmeticError:
            pass
        except Exception as e:
            ctx["exception"] = e

        return render(state.request, "registration/test_registration.html", ctx)


class SaveAndDisplayTestStrategy(SaveToDB):
    def save(self, fields_data, **kwargs):
        ctx = {
            "fields_data": fields_data,
            "record": None,
        }
        try:
            with atomic():
                record = super().save(fields_data, **kwargs)
                ctx["record"] = record
                ctx["admin_url"] = reverse("admin:registration_record_change", args=[record.pk])
        except Exception as e:
            ctx["exception"] = e

        return render(state.request, "registration/test_registration.html", ctx)


class DisplayTestStrategy(RegistrationStrategy):
    verbose_name = "Test"

    def save(self, fields_data, **kwargs):
        from aurora.registration.models import Record

        fields, files = router.decompress(fields_data)

        if state.request and state.request.user.is_authenticated:
            registrar = state.request.user
        else:
            registrar = None
        kwargs.update(
            {
                "registrar": registrar,
                "size": total_size(fields) + total_size(files),
                "counters": fields_data.get("counters", {}),
                "index1": fields_data.get("index1", None),
                "fields": fields,
                # "files": files,
            }
        )
        record = Record(registration=self.registration, **kwargs)
        return render(
            state.request, "registration/test_registration.html", {"record": record, "fields_data": fields_data}
        )


class Strategies(Registry):
    pass


strategies = Strategies(RegistrationStrategy, label_attribute="verbose_name")

strategies.register(SaveToDB)
strategies.register(SaveAndDisplayTestStrategy)
strategies.register(DisplayTestStrategy)
strategies.register(TransactionTestStrategy)
