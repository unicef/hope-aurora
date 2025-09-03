from unittest import mock

import pytest
from django.urls import NoReverseMatch

from aurora.i18n.hreflang.functions import reverse


def test_reverse(db):
    assert reverse("index") == "/"

    assert reverse("registrations") == "/en-us/registrations/"
    assert reverse("registrations", "it-it") == "/it-it/registrations/"
    assert reverse("registrations", "it-it", use_lang_prefix=False) == "/registrations/"
    with mock.patch("aurora.i18n.hreflang.functions.lang_implied_reverse", side_effect="/registrations/"):
        with pytest.raises(NoReverseMatch):
            assert reverse("registrations", "it-it", use_lang_prefix=False) == "/"
