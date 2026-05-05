from types import SimpleNamespace

import pytest
from django.utils import timezone

from aurora.registration.models import Record


@pytest.mark.django_db
def test_registration_save_defaults_and_all_locales():
    from testutils.factories import RegistrationFactory

    reg = RegistrationFactory(name="Reg Save", slug="", title="", locales=["it-it"])
    reg.save()
    assert reg.slug == "reg-save"
    assert reg.title == "Reg Save"
    assert "wizard" in reg.advanced["smart"]
    assert reg.all_locales == {"en-us", "it-it"}


@pytest.mark.django_db
def test_registration_is_running_and_welcome_url():
    from testutils.factories import RegistrationFactory

    reg = RegistrationFactory(start=timezone.now().date(), end=None)
    assert reg.is_running() is True
    assert reg.get_welcome_url() == reg.get_absolute_url()

    reg.end = timezone.now().date() - timezone.timedelta(days=2)
    assert reg.is_running() is False


@pytest.mark.django_db
def test_registration_add_record_and_unique_value(monkeypatch):
    from testutils.factories import RegistrationFactory

    reg = RegistrationFactory(unique_field_path="x.y")

    # default strategy path (handler is None)
    monkeypatch.setattr(
        "aurora.registration.models.SaveToDB",
        lambda _reg: SimpleNamespace(save=lambda data: {"saved": data}),
    )
    assert reg.add_record({"x": 1}) == {"saved": {"x": 1}}

    # unique field happy path
    assert reg.get_unique_value({"x": {"y": "ID1"}}) == "ID1"

    # unique field exception path
    monkeypatch.setattr(
        "aurora.registration.models.jmespath.search",
        lambda *_a, **_k: (_ for _ in ()).throw(Exception("boom")),
    )
    assert reg.get_unique_value({"x": {"y": "ID2"}}) is None


@pytest.mark.django_db
def test_record_data_branches(monkeypatch):
    from testutils.factories import RecordFactory, RegistrationFactory

    reg = RegistrationFactory(public_key="pubkey", encrypt_data=False)
    record = RecordFactory(registration=reg, fields={"a": 1}, files=None)
    assert record.data == {"Forbidden": "Cannot access encrypted data"}

    reg.public_key = ""
    reg.encrypt_data = True
    monkeypatch.setattr(record, "decrypt", lambda **_k: {"ok": 1})
    assert record.data == {"ok": 1}

    reg.encrypt_data = False
    record.files = None
    record.fields = {"a": 1}
    assert record.data == {"a": 1}


@pytest.mark.django_db
def test_record_fields_data_and_merge_conflict():
    from aurora.registration.models import merge

    rec = Record(fields={"a": "b"}, is_offline=False)
    assert rec.fields_data == {"a": "b"}

    rec.is_offline = True
    rec.fields = "x" * 13000
    assert rec.fields_data == "String too long to display..."

    with pytest.raises(Exception, match="Conflict"):
        merge({"a": 1}, {"a": 2}, update=False)
