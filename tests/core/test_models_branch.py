from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from django import forms
from django.core.exceptions import ValidationError

from aurora.core.models import (
    CustomFieldType,
    FlexFormField,
    OptionSet,
    Organization,
    Project,
    Validator,
    clean_choices,
    get_validators,
)
from aurora.exceptions import JSEngineError


@pytest.mark.django_db
def test_organization_save_sets_slug_only_when_adding_without_slug():
    org = Organization(name="Org No Slug")
    org.save()
    assert org.slug == "org-no-slug"

    org_with_slug = Organization(name="Org With Slug", slug="custom-slug")
    org_with_slug.save()
    assert org_with_slug.slug == "custom-slug"


@pytest.mark.django_db
def test_project_save_sets_slug_only_when_missing():
    org = Organization.objects.create(name="Org #1", slug="org-1")

    project = Project(name="My Project", organization=org)
    project.save()
    assert project.slug == "my-project"

    project_with_slug = Project(name="Another Project", organization=org, slug="keep-me")
    project_with_slug.save()
    assert project_with_slug.slug == "keep-me"


def test_validator_js_type_and_get_validators():
    assert Validator.js_type({"a": 1}) == {"a": 1}
    assert isinstance(Validator.js_type("abc"), str)

    no_validator_field = SimpleNamespace(validator=None)
    assert get_validators(no_validator_field) == []

    validator = Mock()
    field = SimpleNamespace(validator=validator)
    wrapped = get_validators(field)
    assert len(wrapped) == 1
    wrapped[0]("payload")
    validator.validate.assert_called_once_with("payload")


@pytest.mark.django_db
def test_validator_monitor_handles_error_shapes(monkeypatch):
    v = Validator.objects.create(label="validator", name="validator", code="true", target=Validator.FIELD, active=True)
    monkeypatch.setattr("aurora.core.models.state.request", SimpleNamespace(user=SimpleNamespace(pk=7)))
    cache_set = Mock()
    monkeypatch.setattr("aurora.core.models.cache.set", cache_set)

    v.monitor(v.STATUS_SUCCESS, {"x": 1})
    assert cache_set.call_count == 3

    cache_set.reset_mock()
    v.monitor(v.STATUS_ERROR, {"x": 1}, exc=ValidationError({"field": ["bad"]}))
    assert cache_set.call_count == 3
    assert any("-error" in call.args[0] and call.args[1] is not None for call in cache_set.call_args_list)

    cache_set.reset_mock()
    v.monitor(v.STATUS_EXCEPTION, {"x": 1}, exc=ValidationError("bad"))
    assert any("-error" in call.args[0] and call.args[1] is not None for call in cache_set.call_args_list)

    cache_set.reset_mock()
    v.monitor(v.STATUS_EXCEPTION, {"x": 1}, exc=RuntimeError("boom"))
    assert any("-error" in call.args[0] and call.args[1] is not None for call in cache_set.call_args_list)


@pytest.mark.django_db
def test_validator_validate_skips_and_runs_based_on_flags(monkeypatch):
    v = Validator.objects.create(
        label="validator",
        name="validator",
        code="true",
        target=Validator.FIELD,
        active=False,
        draft=False,
    )
    engine = Mock()
    monkeypatch.setattr("aurora.core.models.DukPYValidator", lambda *_args, **_kwargs: engine)
    monkeypatch.setattr("aurora.core.models.state.request", SimpleNamespace(user=SimpleNamespace(is_staff=False)))

    # inactive + non-draft should skip
    v.validate({"a": 1})
    engine.validate.assert_not_called()

    # active runs
    v.active = True
    v.validate({"a": 1})
    engine.validate.assert_called_once_with({"a": 1})

    # draft staff runs even if inactive
    engine.validate.reset_mock()
    v.active = False
    v.draft = True
    monkeypatch.setattr("aurora.core.models.state.request", SimpleNamespace(user=SimpleNamespace(is_staff=True)))
    v.validate({"a": 1})
    engine.validate.assert_called_once_with({"a": 1})


@pytest.mark.django_db
def test_validator_validate_wraps_js_engine_error(monkeypatch):
    v = Validator.objects.create(
        label="validator label",
        name="validator_name",
        code="broken",
        target=Validator.FIELD,
        active=True,
    )

    class _Engine:
        @staticmethod
        def validate(_value):
            raise JSEngineError("engine boom")

    monkeypatch.setattr("aurora.core.models.DukPYValidator", lambda *_args, **_kwargs: _Engine())
    monkeypatch.setattr("aurora.core.models.state.request", SimpleNamespace(user=SimpleNamespace(is_staff=False)))

    with pytest.raises(JSEngineError, match="engine boom"):
        v.validate({"a": 1})


@pytest.mark.django_db
def test_flex_field_branches_and_instance_behavior(monkeypatch):
    from testutils.factories import FormFactory

    form = FormFactory(name="Form for fields")
    fld = form.fields.create(
        label="My Field",
        name="my_field",
        field_type=forms.ChoiceField,
        required=True,
        regex=r"^\\d+$",
        advanced={
            "smart": {"visible": False, "datasource": "ds-1"},
            "widget_kwargs": {"class": "input-class"},
        },
        choices="One,Two",
    )
    kwargs = fld.get_field_kwargs()
    assert kwargs["required"] is True
    assert kwargs["datasource"] == "ds-1"
    assert kwargs["widget_kwargs"]["class"] == "input-class"
    assert kwargs["smart_attrs"]["data-visibility"] == "hidden"
    assert kwargs["choices"] == [("one", "One"), ("two", "Two")]
    assert kwargs["validators"]

    # get_instance returns None when field_type is missing
    fld.field_type = None
    assert fld.get_instance() is None

    # clean wraps get_instance failures
    fld.field_type = forms.CharField
    monkeypatch.setattr(fld, "get_instance", lambda: (_ for _ in ()).throw(RuntimeError("boom")))
    with pytest.raises(ValidationError, match="Unable to create valid FlexField"):
        fld.clean()


@pytest.mark.django_db
def test_flex_field_save_autonames_blank_name():
    from testutils.factories import FormFactory

    form = FormFactory(name="Form for save")
    fld = FlexFormField(
        flex_form=form,
        label="Auto Named",
        name="   ",
        field_type=forms.CharField,
    )
    fld.save()
    assert fld.name.startswith("auto_named")


@pytest.mark.django_db
def test_optionset_and_clean_choices_branches(caplog):
    obj = OptionSet(
        name="options-branch",
        data="1:Rome\r\n2:Milan",
        separator=":",
        locale="en-us",
        languages="-,en-us",
    )
    # missing requested language falls back to default locale path
    data = obj.get_data("it-it")
    assert data[0]["label"] == "Rome"

    obj.locale = "fr-fr"
    with pytest.raises(ValidationError, match="Default locale must be in the languages list"):
        obj.clean()

    assert clean_choices(["One", "Two"]) == [("one", "One"), ("two", "Two")]
    with pytest.raises(ValueError, match="choices must be list or tuple"):
        clean_choices("invalid")


@pytest.mark.django_db
def test_custom_fieldtype_clean_and_build_branches():
    custom = CustomFieldType(name="BranchCustom", base_type=forms.CharField, attrs={"choices": [("a", "A")]})
    custom.save()
    built = CustomFieldType.build("BuiltCustom", {"base_type": forms.CharField, "attrs": {"choices": [("x", "X")]}})
    assert built.name == "BuiltCustom"

    custom.base_type = None  # type: ignore[assignment]
    with pytest.raises(ValidationError, match="base_type is mandatory"):
        custom.clean()

    custom.base_type = forms.CharField
    custom.attrs = {"invalid_kwarg": object()}
    with pytest.raises(ValidationError, match="Error instantiating"):
        custom.clean()
