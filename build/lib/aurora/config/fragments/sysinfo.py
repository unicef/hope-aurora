def masker(key, value, config, request):
    from django_sysinfo.utils import cleanse_setting

    from aurora.core.utils import is_root

    if is_root(request):
        return value
    return cleanse_setting(key, value, config, request)


SYSINFO = {
    "host": True,
    "os": True,
    "python": True,
    "modules": True,
    "masker": "aurora.config.settings.masker",
    "masked_environment": "API|TOKEN|KEY|SECRET|PASS|SIGNATURE|AUTH|_ID|SID|DATABASE_URL",
}
