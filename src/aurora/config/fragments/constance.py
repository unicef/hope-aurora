from collections import OrderedDict

from .. import env

CONSTANCE_ADDITIONAL_FIELDS = {
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
        "GRAPH_API_ENABLED": (True, "", bool),
        "LOG_POST_ERRORS": (False, "", bool),
        "MINIFY_IGNORE_PATH": (r"", "regex for ignored path", str),
        "BASE_TEMPLATE": ("base_lean.html", "Default base template", str),
        "HOME_TEMPLATE": ("home.html", "Default home.html", str),
        "QRCODE": (True, "Enable QRCode generation", bool),
        "SHOW_REGISTER_ANOTHER": (True, "Enable QRCode generation", bool),
        "MAINTENANCE_MODE": (False, "set maintenance mode On/Off", bool),
        "UBA_TOKEN_URL": ("", "UBA Token URL", str),
        "UBA_NAME_ENQUIRY_URL": ("", "UBA Name Enquiry Service URL", str),
        "UBA_USERNAME": ("", "UBA Username", str),
        "UBA_PASSWORD": ("", "UBA Password", "write_only_input"),
        "UBA_SECRET_KEY": ("", "UBA Secret Key", "write_only_input"),
        "UBA_APPL_CODE": ("", "UBA Application Code", str),
        "UBA_CLIENT_NO": ("", "UBA Client Number", str),
        "UBA_X_AUTH_CRED": ("", "UBA X Auth Credential", "write_only_input"),
        "UBA_CONSUMER_KEY": ("", "UBA Service Token", str),
        "UBA_CONSUMER_SECRET": ("", "UBA Service Token", "write_only_input"),
    }
)
