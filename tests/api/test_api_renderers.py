import importlib
from pathlib import Path

import pytest
from django.contrib.staticfiles import finders
from django.core.management import call_command

from aurora.config.fragments import rest_framework as fragment

BROWSABLE_API = "rest_framework.renderers.BrowsableAPIRenderer"


@pytest.fixture
def reload_fragment(monkeypatch):
    def _reload(debug: bool) -> dict:
        monkeypatch.setenv("DEBUG", str(int(debug)))
        return importlib.reload(fragment).REST_FRAMEWORK

    yield _reload
    monkeypatch.undo()
    importlib.reload(fragment)


def test_browsable_api_is_disabled_in_production(reload_fragment):
    renderers = reload_fragment(debug=False)["DEFAULT_RENDERER_CLASSES"]

    assert BROWSABLE_API not in renderers
    assert renderers[0] == "rest_framework.renderers.JSONRenderer"


def test_browsable_api_is_available_in_debug(reload_fragment):
    assert BROWSABLE_API in reload_fragment(debug=True)["DEFAULT_RENDERER_CLASSES"]


def test_drf_assets_are_not_collected(settings, tmp_path: Path):
    settings.STATIC_ROOT = tmp_path

    call_command("collectstatic", interactive=False, verbosity=0)

    assert (tmp_path / "admin").is_dir()
    assert not (tmp_path / "rest_framework").exists()


def test_drf_assets_are_still_served_in_development():
    assert finders.find("rest_framework/js/bootstrap.min.js")
