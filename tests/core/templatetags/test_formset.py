import pytest
from testutils.factories import FormSetFactory

from aurora.core.models import FormSet
from aurora.core.templatetags.formset import formset_config, markdown, md


@pytest.fixture
def formset(db) -> FormSet:
    return FormSetFactory()


def test_formset_config(formset: FormSet):
    assert formset_config(formset.get_formset()(prefix="prefix")) == {
        "addContainerClass": "formset-0-add",
        "addCssClass": "formset-add-button",
        "addText": "Add Another",
        "deleteContainerClass": "formset-0-delete",
        "deleteCssClass": "formset-delete-button",
        "deleteText": "Remove",
        "formCssClass": "form-container-prefix",
        "keepFieldValues": False,
        "namespace": "prefix",
        "onAdd": None,
        "onRemove": None,
        "original": {
            "addText": "Add Another",
            "counterPrefix": "",
            "deleteText": "Remove",
        },
        "prefix": "prefix",
        "counterPrefix": "",
    }


def test_markdown():
    assert markdown("# abc") == "<h1>abc</h1>"


def test__md():
    assert md("# abc") == "<h1>abc</h1>"
