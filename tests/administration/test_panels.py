import base64
from unittest import mock

import pytest
from django.urls import reverse


@pytest.fixture
def app(django_app_factory):
    return django_app_factory(csrf_checks=False)


@pytest.mark.django_db
@pytest.mark.parametrize("is_root", [True, False])
def test_panel_sql(app, admin_user, is_root):
    app.set_user(admin_user)
    url = reverse("admin:console-panel_sql")
    stmt = "select * from security_user"
    # this is performed in javascript due to WAF
    encoded = base64.b64encode(stmt.encode("utf-8")).decode("ascii")
    with mock.patch("aurora.administration.panels.is_root", return_value=is_root):
        res = app.get(url)
        res.forms["sqlForm"]["command"] = encoded
        res.forms["sqlForm"].submit()


@pytest.mark.django_db(transaction=True)
def test_panel_sql_result(app, admin_user):
    app.set_user(admin_user)
    url = reverse("admin:console-panel_sql")
    stmt = "select * from security_user"
    # this is performed in javascript due to WAF
    encoded = base64.b64encode(stmt.encode("utf-8")).decode("ascii")
    res = app.get(url)
    res.forms["sqlForm"]["command"] = encoded
    res.forms["sqlForm"].submit()


@pytest.mark.django_db
def test_panel_sql_multiple(app, admin_user):
    app.set_user(admin_user)
    url = reverse("admin:console-panel_sql")
    stmt = "select * from security_user; select * from security_user; "
    # this is performed in javascript due to WAF
    encoded = base64.b64encode(stmt.encode("utf-8")).decode("ascii")
    with mock.patch("aurora.administration.panels.is_root", return_value=True):
        res = app.get(url)
        res.forms["sqlForm"]["command"] = encoded
        res.forms["sqlForm"].submit()


@pytest.mark.django_db
def test_panel_sql_exception(app, admin_user):
    app.set_user(admin_user)
    url = reverse("admin:console-panel_sql")
    with mock.patch("aurora.administration.panels.is_root", return_value=True):
        with mock.patch("aurora.administration.forms.sqlparse.split", side_effect=Exception):
            res = app.get(url)
            res.forms["sqlForm"]["command"] = ""
            res.forms["sqlForm"].submit()


@pytest.mark.django_db
def test_panel_sql_no_result(app, admin_user):
    app.set_user(admin_user)
    url = reverse("admin:console-panel_sql")
    stmt = "insert into auth_group (\"name\") VALUES ('ccc')"
    # this is performed in javascript due to WAF
    encoded = base64.b64encode(stmt.encode("utf-8")).decode("ascii")
    with mock.patch("aurora.administration.panels.is_root", return_value=True):
        res = app.get(url)
        res.forms["sqlForm"]["command"] = encoded
        res.forms["sqlForm"].submit()


@pytest.mark.django_db
def test_panel_sql_invalid(app, admin_user):
    app.set_user(admin_user)
    url = reverse("admin:console-panel_sql")
    res = app.get(url)
    res.forms["sqlForm"]["command"] = ""
    res.forms["sqlForm"].submit()


@pytest.mark.django_db
def test_panel_sql_save(app, admin_user):
    app.set_user(admin_user)
    url = reverse("admin:console-panel_sql")
    stmt = "select * from security_user;"
    # this is performed in javascript due to WAF
    encoded = base64.b64encode(stmt.encode("utf-8")).decode("ascii")

    res = app.post(f"{url}?op=save", {"name": "test", "command": encoded})
    assert res.json == {"message": "Saved"}


@pytest.mark.django_db
def test_panel_sql_save_invalid(app, admin_user):
    app.set_user(admin_user)
    url = reverse("admin:console-panel_sql")
    stmt = "select * from security_user;select * from security_user;"
    # this is performed in javascript due to WAF
    encoded = base64.b64encode(stmt.encode("utf-8")).decode("ascii")

    res = app.post(f"{url}?op=save", {"name": "test", "command": encoded})
    assert res.json == {"error": {"command": ["Only one statement is allowed"]}}


@pytest.mark.django_db
def test_panel_sql_save_max(app, admin_user):
    admin_user.profile.custom_fields = {"sql_stm": ["", "", "", "", ""]}
    admin_user.profile.save()
    app.set_user(admin_user)
    url = reverse("admin:console-panel_sql")
    stmt = "select * from security_user;"
    # this is performed in javascript due to WAF
    encoded = base64.b64encode(stmt.encode("utf-8")).decode("ascii")

    res = app.post(f"{url}?op=save", {"name": "test", "command": encoded})
    assert res.json == {"message": "Saved"}
    admin_user.profile.refresh_from_db()
    assert admin_user.profile.custom_fields["sql_stm"][4] == ["test", "select * from security_user;"]


@pytest.mark.django_db
@pytest.mark.parametrize("is_root", [True, False])
def test_panel_sql_403(app, staff_user, is_root):
    app.set_user(staff_user)
    url = reverse("admin:console-panel_sql")
    with mock.patch("aurora.administration.panels.is_root", return_value=is_root):
        res = app.get(url, expect_errors=True)
        assert res.status_code == 403


@pytest.mark.django_db
@pytest.mark.parametrize("is_root", [True, False])
def test_panel_sql_302(app, user, is_root):
    app.set_user(user)
    url = reverse("admin:console-panel_sql")
    with mock.patch("aurora.administration.panels.is_root", return_value=is_root):
        res = app.get(url, expect_errors=True)
        assert res.status_code == 302
