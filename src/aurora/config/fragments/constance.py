from collections import OrderedDict

from .. import env

CONSTANCE_ADDITIONAL_FIELDS = {
    "html_minify_select": [
        "bitfield.forms.BitFormField",
        {
            "initial": 0,
            "required": False,
            "choices": (("html", "HTML"), ("line", "NEWLINE"), ("space", "SPACES")),
        },
    ],
    "write_only_input": [
        "django.forms.fields.CharField",
        {
            "required": False,
            "widget": "aurora.core.constance.WriteOnlyInput",
        },
    ],
}
CONSTANCE_BACKEND = "constance.backends.database.DatabaseBackend"
CONSTANCE_DATABASE_CACHE_BACKEND = env("CONSTANCE_DATABASE_CACHE_BACKEND")
CONSTANCE_CONFIG = OrderedDict(
    {
        "CACHE_FORMS": (False, "", bool),
        "CACHE_VERSION": (1, "", int),
        "HOME_PAGE_REGISTRATIONS": ("", "", str),
        "SMART_ADMIN_BOOKMARKS": (
            "",
            "",
            str,
        ),
        "LOGIN_LOCAL": (True, "Enable local accounts login", bool),
        "LOGIN_SSO": (True, "Enable SSO logon", bool),
        "ADMIN_SYNC_REMOTE_SERVER": ("", "production server url", str),
        "ADMIN_SYNC_REMOTE_ADMIN_URL": ("/admin/", "", str),
        "ADMIN_SYNC_LOCAL_ADMIN_URL": ("/admin/", "", str),
        "LOG_POST_ERRORS": (False, "", bool),
        "MINIFY_RESPONSE": (0, "select yes or no", "html_minify_select"),
        "MINIFY_IGNORE_PATH": (r"", "regex for ignored path", str),
        "BASE_TEMPLATE": ("base_lean.html", "Default base template", str),
        "HOME_TEMPLATE": ("home.html", "Default home.html", str),
        "QRCODE": (True, "Enable QRCode generation", bool),
        "SHOW_REGISTER_ANOTHER": (True, "Enable QRCode generation", bool),
        "MAINTENANCE_MODE": (False, "set maintenance mode On/Off", bool),
        "WAF_REGISTRATION_ALLOWED_HOSTNAMES": (
            ".*",
            "public website hostname (regex)",
            str,
        ),
        "WAF_ADMIN_ALLOWED_HOSTNAMES": ("", "admin website hostname (regex)", str),
        "IMTO_NAME_ENQUIRY_URL": ("", "IMTO Name Enquiry Service URL", str),
        "IMTO_TOKEN": ("", "IMTO Service Token", "write_only_input"),
    }
)
