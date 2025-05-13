from aurora.core.templatetags.matomo import matomo_id, matomo_site


def test_matomo_site(settings):
    settings.MATOMO_SITE = "abc"
    assert matomo_site()


def test_matomo_id(settings):
    assert matomo_id() == ""
    settings.MATOMO_ID = "MATOMO_ID"
    assert matomo_id() == "MATOMO_ID"
