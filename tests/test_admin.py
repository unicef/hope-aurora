from typing import TYPE_CHECKING, List
from unittest.mock import Mock

import pytest
from _pytest.python import Metafunc
from admin_extra_buttons.handlers import ChoiceHandler
from django.contrib.admin.sites import site
from django.contrib.admin.templatetags.admin_urls import admin_urlname
from django.urls import reverse
from django_regex.utils import RegexList as _RegexList

if TYPE_CHECKING:
    from _pytest.mark import Mark
    from django.db.models.options import Options


class RegexList(_RegexList):
    def extend(self, __iterable) -> None:
        for e in __iterable:
            self.append(e)


GLOBAL_EXCLUDED_MODELS = RegexList(
    [
        r"reversion.",
        # r"security.",
        # r"core.FormSet",
        # r"core.FlexFormField",
    ]
)

GLOBAL_EXCLUDED_BUTTONS = RegexList(
    [
        r".*:publish",
        r".*:_recoverlist_view",
        r".*:check_remote_version",
        r"core.ValidatorAdmin:test",
        r"registration.RecordAdmin:preview",
        r"registration.RecordAdmin:inspect",
        r"registration.RecordAdmin:decrypt",
        "security.UserAdmin:hijack",
    ]
)

KWARGS = {}
pytestmark = pytest.mark.admin


def pytest_generate_tests(metafunc: Metafunc):  # noqa
    import django

    markers: List[Mark] = metafunc.definition.own_markers
    excluded_models = RegexList(GLOBAL_EXCLUDED_MODELS)
    excluded_buttons = RegexList(GLOBAL_EXCLUDED_BUTTONS)
    if "skip_models" in [m.name for m in markers]:
        skip_rule = list(filter(lambda m: m.name == "skip_models", markers))[0]
        excluded_models.extend(skip_rule.args)
    if "skip_buttons" in [m.name for m in markers]:
        skip_rule = list(filter(lambda m: m.name == "skip_buttons", markers))[0]
        excluded_buttons.extend(skip_rule.args)
    django.setup()
    if "button_handler" in metafunc.fixturenames:
        m = []
        ids = []
        for model, admin in site._registry.items():
            if hasattr(admin, "get_changelist_buttons"):
                name = model._meta.object_name
                assert admin.urls  # we need to force this call
                buttons = admin.extra_button_handlers.values()
                full_name = f"{model._meta.app_label}.{name}"
                admin_name = f"{model._meta.app_label}.{admin.__class__.__name__}"
                if full_name not in excluded_models:
                    for btn in buttons:
                        tid = f"{admin_name}:{btn.name}"
                        if tid not in excluded_buttons:
                            m.append([admin, btn])
                            ids.append(tid)
        metafunc.parametrize("modeladmin,button_handler", m, ids=ids)
    elif "modeladmin" in metafunc.fixturenames:
        m = []
        ids = []
        for model, admin in site._registry.items():
            name = model._meta.object_name
            full_name = f"{model._meta.app_label}.{name}"
            if full_name not in excluded_models:
                m.append(admin)
                ids.append(f"{admin.__class__.__name__}:{full_name}")
        metafunc.parametrize("modeladmin", m, ids=ids)


@pytest.fixture
def record(db, request):
    from testutils.factories import get_factory_for_model

    # TIPS: database access is forbidden in pytest_generate_tests
    modeladmin = request.getfixturevalue("modeladmin")
    instance = modeladmin.model.objects.first()
    if not instance:
        full_name = f"{modeladmin.model._meta.app_label}.{modeladmin.model._meta.object_name}"
        factory = get_factory_for_model(modeladmin.model)
        try:
            instance = factory(**KWARGS.get(full_name, {}))
        except Exception as e:
            raise Exception(f"Error creating fixture for {modeladmin.model}") from e
    return instance


@pytest.fixture
def app(django_app_factory):
    from testutils.factories import SuperUserFactory

    admin_user = SuperUserFactory(username="superuser")
    django_app = django_app_factory(csrf_checks=False)
    django_app.set_user(admin_user)
    django_app._user = admin_user
    return django_app


@pytest.mark.django_db
def test_index(app):
    url = reverse("admin:index")

    res = app.get(url)
    assert res.status_code == 200
    assert "Smart Index" in res.body.decode()

    app.set_cookie("smart", "1")
    res = app.get(reverse("admin:index"))
    assert "Standard Index" in res.body.decode()


@pytest.mark.django_db
def test_applist(app):
    url = reverse("admin:index")

    res = app.get(url)
    assert "Smart Index" in res.body.decode()

    app.set_cookie("smart", "1")
    res = app.get(url)
    assert "Standard Index" in res.body.decode()


@pytest.mark.django_db
def test_group_list(app):
    url = reverse("admin:group_list", args=["Security"])

    res = app.get(url)
    assert res.status_code == 200, res.location


@pytest.mark.django_db
@pytest.mark.skip_models("constance.Config", "registration.Record")
def test_changelist(app, modeladmin, record):
    url = reverse(admin_urlname(modeladmin.model._meta, "changelist"))
    opts: Options = modeladmin.model._meta
    res = app.get(url)
    assert res.status_code == 200, res.location
    assert str(opts.app_config.verbose_name) in str(res.content)
    assert f"/{record.pk}/change/" in res.body.decode()


def show_error(res):
    errors = []
    for k, v in dict(res.context["adminform"].form.errors).items():
        errors.append(f"{k}: {''.join(v)}")
    return ("Form submitting failed: {}: {}".format(res.status_code, errors),)


@pytest.mark.django_db
@pytest.mark.skip_models("constance.Config", "registration.Record")
def test_changeform(app, modeladmin, record):
    opts: Options = modeladmin.model._meta
    url = reverse(admin_urlname(opts, "change"), args=[record.pk])

    res = app.get(url)
    assert str(opts.app_config.verbose_name) in res.body.decode()
    if modeladmin.has_change_permission(Mock(user=app._user)):
        res = res.forms[1].submit()
        assert res.status_code in [302, 200]


@pytest.mark.django_db
@pytest.mark.skip_models("constance.Config", "registration.Record")
def test_add(
    app,
    modeladmin,
):
    url = reverse(admin_urlname(modeladmin.model._meta, "add"))
    if modeladmin.has_add_permission(Mock(user=app._user)):
        res = app.get(url)
        res.forms[1].submit()
        assert res.status_code in [200, 302]
    else:
        pytest.skip("No 'add' permission")


@pytest.mark.django_db
@pytest.mark.skip_models("constance.Config", "registration.Record")
def test_delete(app, modeladmin, record, monkeypatch):
    url = reverse(admin_urlname(modeladmin.model._meta, "delete"), args=[record.pk])
    if modeladmin.has_delete_permission(Mock(user=app._user)):
        res = app.get(url)
        res.forms[1].submit()
        assert res.status_code in [200, 302]
    else:
        pytest.skip("No 'delete' permission")


@pytest.mark.django_db
@pytest.mark.skip_buttons(
    "i18n.MessageAdmin.publish",
)
def test_buttons(app, modeladmin, button_handler, record, monkeypatch):
    from admin_extra_buttons.handlers import LinkHandler

    if isinstance(button_handler, ChoiceHandler):
        pass
    elif isinstance(button_handler, LinkHandler):
        btn = button_handler.get_button({"original": record})
        button_handler.func(None, btn)
    else:
        if len(button_handler.sig.parameters) == 2:
            url = reverse(f"admin:{button_handler.url_name}")
        else:
            url = reverse(f"admin:{button_handler.url_name}", args=[record.pk])

        res = app.get(url)
        assert res.status_code in [200, 302]
