import io
from unittest.mock import Mock

import pytest
from PIL import Image
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import UploadedFile
from django.urls import reverse
from pyquery import PyQuery
from webtest import Upload

from aurora.core.fields import ImageField


@pytest.fixture
def image_registration(db):
    from testutils.factories import FormFactory, RegistrationFactory

    frm = FormFactory(name="Form1")
    frm.fields.get_or_create(
        label="Image",
        defaults={
            "field_type": ImageField,
            "advanced": {"field_kwargs": {"max_size": 1}, "smart": {"description": ""}},
        },
    )
    return RegistrationFactory(flex_form=frm)


@pytest.fixture(autouse=True)
def mock_state():
    from django.contrib.auth.models import AnonymousUser

    from aurora.state import state

    state.request = Mock(user=AnonymousUser())


@pytest.fixture
def image():
    img = Image.new("RGB", (100, 100), (255, 255, 255))
    imgc = img.convert("RGB")
    data = io.BytesIO()
    imgc.save(data, format="PNG")
    return ContentFile(data.getvalue(), name="aaaa.png")


def test_image_type():
    fld = ImageField()
    with pytest.raises(ValidationError, match="No file was submitted. Check the encoding type on the form."):
        assert fld.clean(22)


def test_image_valid(db, image):
    fld = ImageField()
    assert fld.clean(UploadedFile(image, name="aaaa.png", size=image.size))


def test_image_too_big(db, image):
    fld = ImageField(max_size=1)
    with pytest.raises(ValidationError, match="Image too big."):
        assert fld.clean(UploadedFile(image, name="aaaa.png", size=image.size))


def test_create_form(django_app, image_registration, image):
    url = reverse("register", kwargs={"slug": image_registration.slug})
    res = django_app.get(url)
    res.forms["registrationForm"]["image"] = Upload(image.name, image.read())
    res = res.forms["registrationForm"].submit()
    assert res.status_code == 200
    pq = PyQuery(res.body)
    assert pq("#id_image_error").text() == "Image too big."
