from types import SimpleNamespace

import pytest
from django.forms import Media
from django.http import Http404

from aurora.registration.views.data import RegistrationDataView


@pytest.mark.django_db
def test_registration_property_resolves_by_slug_and_sets_tags(monkeypatch):
    from testutils.factories import RegistrationFactory

    reg = RegistrationFactory(name="Reg Data")
    view = RegistrationDataView()
    view.kwargs = {"slug": reg.slug}

    tags = {}
    monkeypatch.setattr(
        "aurora.registration.views.data.set_tag",
        lambda key, value: tags.setdefault(key, value),
    )

    resolved = view.registration
    assert resolved.pk == reg.pk
    assert tags["registration.organization"] == reg.project.organization.name
    assert tags["registration.project"] == reg.project.name
    assert tags["registration.slug"] == reg.name


@pytest.mark.django_db
def test_registration_property_resolves_by_pk(monkeypatch):
    from testutils.factories import RegistrationFactory

    reg = RegistrationFactory()
    view = RegistrationDataView()
    view.kwargs = {"pk": reg.pk}

    monkeypatch.setattr("aurora.registration.views.data.set_tag", lambda *_a, **_k: None)
    assert view.registration.pk == reg.pk


@pytest.mark.django_db
def test_registration_property_raises_404_when_missing_or_unknown(monkeypatch):
    view = RegistrationDataView()
    view.kwargs = {}
    with pytest.raises(Http404):
        _ = view.registration

    view = RegistrationDataView()
    view.kwargs = {"slug": "missing-slug"}
    monkeypatch.setattr("aurora.registration.views.data.set_tag", lambda *_a, **_k: None)
    with pytest.raises(Http404):
        _ = view.registration


def test_media_uses_debug_suffix(monkeypatch):
    from aurora.registration.views import data as data_view

    view = RegistrationDataView()

    monkeypatch.setattr(data_view.settings, "DEBUG", False)
    js_files = view.media._js
    assert "admin/js/vendor/jquery/jquery.min.js" in js_files
    assert "js/datatable.min.js" in js_files

    monkeypatch.setattr(data_view.settings, "DEBUG", True)
    js_files = view.media._js
    assert "admin/js/vendor/jquery/jquery.js" in js_files
    assert "js/datatable.js" in js_files


@pytest.mark.django_db
def test_get_context_data_includes_registration_media_and_page_size(monkeypatch):
    from testutils.factories import RegistrationFactory

    reg = RegistrationFactory()
    view = RegistrationDataView()
    view.kwargs = {"slug": reg.slug}
    view.__dict__["registration"] = reg
    view.request = SimpleNamespace()

    monkeypatch.setattr(
        "aurora.registration.views.data.settings.REST_FRAMEWORK",
        {"PAGE_SIZE": 77},
    )
    monkeypatch.setattr(
        RegistrationDataView,
        "media",
        property(lambda _self: Media(js=["x.js"])),
    )

    context = view.get_context_data(extra="value")
    assert context["registration"] == reg
    assert context["drf_page_size"] == 77
    assert isinstance(context["media"], Media)
    assert context["extra"] == "value"
