import io
import tempfile
from pathlib import Path

import pytest
from django.core.management import call_command


@pytest.fixture()
def registration(simple_form):
    from aurora.registration.models import Registration

    reg, __ = Registration.objects.get_or_create(
        locale="en-us",
        name="registration #1",
        defaults={"flex_form": simple_form, "intro": "intro", "footer": "footer", "active": True},
    )
    priv, pub = reg.setup_encryption_keys()
    reg._private_pem = priv
    return reg


def test_sync(db):
    buf = io.StringIO()
    workdir = Path(".").absolute()

    with tempfile.NamedTemporaryFile("w", dir=workdir, prefix="~SYNC", suffix=".json", delete=False) as fdst:
        call_command("dumpdata", "core", stdout=buf, use_natural_foreign_keys=True, use_natural_primary_keys=True)
        fdst.write(buf.getvalue())
    call_command("loaddata", (workdir / fdst.name).absolute())


def test_protocol_registration(db, registration):
    from aurora.registration.admin.protocol import AuroraSyncRegistrationProtocol

    c = AuroraSyncRegistrationProtocol()
    data = c.collect([registration])
    assert registration in data
    assert registration.flex_form in data


def test_protocol_registration_marhalling(db, registration):
    from aurora.registration.admin.protocol import AuroraSyncRegistrationProtocol

    c = AuroraSyncRegistrationProtocol()
    assert c.deserialize(c.serialize([registration]))


def test_protocol_organization(db):
    from testutils.factories import OrganizationFactory

    from aurora.core.admin.protocols import AuroraSyncOrganizationProtocol

    organization = OrganizationFactory()

    c = AuroraSyncOrganizationProtocol()
    data = c.collect([organization])
    assert organization in data


def test_protocol_organization_marhalling(db):
    from testutils.factories import OrganizationFactory

    from aurora.core.admin.protocols import AuroraSyncOrganizationProtocol

    organization = OrganizationFactory()
    c = AuroraSyncOrganizationProtocol()
    assert c.deserialize(c.serialize([organization]))


def test_protocol_project(db):
    from testutils.factories import ProjectFactory

    from aurora.core.admin.protocols import AuroraSyncProjectProtocol

    organization = ProjectFactory()

    c = AuroraSyncProjectProtocol()
    data = c.collect([organization])
    assert organization in data


def test_protocol_project_marhalling(db):
    from testutils.factories import ProjectFactory

    from aurora.core.admin.protocols import AuroraSyncProjectProtocol

    organization = ProjectFactory()
    c = AuroraSyncProjectProtocol()
    assert c.deserialize(c.serialize([organization]))
