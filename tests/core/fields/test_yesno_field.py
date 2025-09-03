import pytest

from aurora.core.fields import YesNoRadio


def test_yesno():
    fld = YesNoRadio()
    assert fld.choices == [("y", "Yes"), ("n", "No")]


def test_custom():
    fld = YesNoRadio(choices=[("y", "Si"), ("n", "No")])
    assert fld.choices == [("y", "Si"), ("n", "No")]


def test_error1():
    with pytest.raises(ValueError, match="Choice value must"):
        YesNoRadio(choices=["Si", "No"])


def test_error2():
    with pytest.raises(ValueError, match="accept only 2 choice label"):
        YesNoRadio(choices=["Yes", "No", "Maybe"])
