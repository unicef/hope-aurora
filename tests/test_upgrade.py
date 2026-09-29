from types import SimpleNamespace

import pytest
from click.testing import CliRunner
from redis.exceptions import LockError

from aurora.management.commands import upgrade as upgrade_module


@pytest.fixture
def unavailable_lock(monkeypatch, tmp_path):
    """Run `upgrade` with a contended migration lock, recording the commands it manages to run."""
    commands: list[str] = []

    def fail_to_lock(*args, **kwargs):
        raise LockError("Unable to acquire lock within the time specified")

    monkeypatch.setenv("STATIC_ROOT", str(tmp_path))
    monkeypatch.setattr(upgrade_module, "call_command", lambda name, *a, **kw: commands.append(name))
    monkeypatch.setattr(upgrade_module, "cache", SimpleNamespace(lock=fail_to_lock))
    return commands


def test_upgrade_collects_static_outside_the_lock(unavailable_lock):
    CliRunner().invoke(upgrade_module.upgrade, ["--no-input"])

    assert unavailable_lock == ["collectstatic"]


def test_upgrade_fails_when_the_lock_cannot_be_acquired(unavailable_lock):
    result = CliRunner().invoke(upgrade_module.upgrade, ["--no-input"])

    assert result.exit_code == 1
    assert "django-migrations" in result.stderr
