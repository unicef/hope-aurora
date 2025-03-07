from unittest import mock

from aurora.web.storage import ForgivingManifestStaticFilesStorage


def test_storage():
    s = ForgivingManifestStaticFilesStorage()
    assert s.stored_name("aaa") == "aaa"
    assert s.hashed_name("aaa") == "aaa"


def test_storage_error():
    with mock.patch(
        "django.contrib.staticfiles.storage.ManifestStaticFilesStorage.stored_name", side_effect=ValueError
    ):
        s = ForgivingManifestStaticFilesStorage()
        assert s.stored_name("aaa") == "aaa"
        assert s.hashed_name("aaa") == "aaa"
