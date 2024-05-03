import logging
import mimetypes
import os
from pathlib import Path

from . import env

BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

PWA_SERVICE_WORKER_PATH = os.path.join(BASE_DIR, "static/js", "serviceworker.js")

mimetypes.add_type("image/svg+xml", ".svg", True)
mimetypes.add_type("image/svg+xml", ".svgz", True)

PACKAGE_DIR = Path(__file__).resolve().parent.parent
SRC_DIR = PACKAGE_DIR.parent
DEV_DIR = SRC_DIR.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env("SECRET_KEY")
FERNET_KEY = env("FERNET_KEY")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env("DEBUG")
DEBUG_PROPAGATE_EXCEPTIONS = env("DEBUG_PROPAGATE_EXCEPTIONS")

ALLOWED_HOSTS = env.list("ALLOWED_HOSTS")
DJANGO_ADMIN_URL = env("DJANGO_ADMIN_URL")

# Application definition
SITE_ID = env("SITE_ID")
INSTALLED_APPS = [
    "daphne",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",
    "django.forms",
    # -- dev --
    "debug_toolbar",
    # ---
    "reversion",  # https://github.com/etianen/django-reversion
    "reversion_compare",  # https://github.com/jedie/django-reversion-compare
    "django_filters",
    # ---
    "smart_admin.apps.SmartLogsConfig",
    "smart_admin.apps.SmartTemplateConfig",
    "smart_admin.apps.SmartAuthConfig",
    "smart_admin.apps.SmartConfig",
    "aurora.administration.apps.AuroraAdminConfig",
    "front_door.contrib",
    "hijack",
    "rest_framework",
    "rest_framework.authtoken",
    "aurora.api",
    "admin_ordering",
    "django_sysinfo",
    "admin_extra_buttons",
    "adminfilters",
    "adminactions",
    "mptt",
    "tinymce",
    "mdeditor",
    "constance",
    "constance.backends.database",
    "flags",
    "jsoneditor",
    "captcha",
    "social_django",
    "corsheaders",
    "simplemathcaptcha",
    "dbtemplates",
    "admin_sync",
    "anymail",
    # ---
    "aurora.apps.Config",
    "aurora.flatpages.apps.Config",
    "aurora.i18n",
    "aurora.web",
    "aurora.security.apps.Config",
    "aurora.core",
    "aurora.registration",
    "aurora.counters",
]
FORM_RENDERER = "django.forms.renderers.TemplatesSetting"
MIDDLEWARE = [
    # "django.middleware.cache.UpdateCacheMiddleware",
    "aurora.web.middlewares.thread_local.ThreadLocalMiddleware",
    "aurora.web.middlewares.sentry.SentryMiddleware",
    "front_door.middleware.FrontDoorMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "aurora.web.middlewares.maintenance.MaintenanceMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "aurora.web.middlewares.i18n.I18NMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "aurora.web.middlewares.admin.AdminSiteMiddleware",
    # "aurora.web.middlewares.http2.HTTP2Middleware",
    "aurora.web.middlewares.minify.HtmlMinMiddleware",
    "django.middleware.gzip.GZipMiddleware",
    # "django.middleware.cache.FetchFromCacheMiddleware",
    "debug_toolbar.middleware.DebugToolbarMiddleware",
    "hijack.middleware.HijackUserMiddleware",
    "csp.middleware.CSPMiddleware",
]
X_FRAME_OPTIONS = "SAMEORIGIN"

ROOT_URLCONF = "aurora.config.urls"

TEMPLATE_LOADERS = (
    "dbtemplates.loader.Loader",
    "django.template.loaders.filesystem.Loader",
    "django.template.loaders.app_directories.Loader",
)

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            PACKAGE_DIR / "administration/templates",
            PACKAGE_DIR / "admin/ui/templates",
            PACKAGE_DIR / "api/templates",
            PACKAGE_DIR / "registration/templates",
            PACKAGE_DIR / "flatpages/templates",
            PACKAGE_DIR / "core/templates",
            PACKAGE_DIR / "web/templates",
        ],
        "APP_DIRS": False,
        "OPTIONS": {
            "loaders": TEMPLATE_LOADERS,
            # 'builtins': [
            #     'http2.templatetags',
            # ],
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "constance.context_processors.config",
                "aurora.i18n.context_processors.itrans",
                "aurora.web.context_processors.smart",
                "django.template.context_processors.i18n",
                # Social auth context_processors
                "social_django.context_processors.backends",
                "social_django.context_processors.login_redirect",
            ],
        },
    },
]

WSGI_APPLICATION = "aurora.config.wsgi.application"
ASGI_APPLICATION = "aurora.config.asgi.application"

# Database
# https://docs.djangoproject.com/en/3.1/ref/settings/#databases

main_conn = env.db("DATABASE_URL")
main_conn["CONN_MAX_AGE"] = 60
main_conn.update({"OPTIONS": {"options": "-c statement_timeout=10000"}})

ro_conn = main_conn.copy()
ro_conn.update(
    {
        "OPTIONS": {"options": "-c default_transaction_read_only=on"},
        "TEST": {
            "READ_ONLY": True,  # Do not manage this database during tests
        },
    }
)

DATABASES = {"default": main_conn, "read_only": ro_conn}

DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

# Password validation
# https://docs.djangoproject.com/en/3.1/ref/settings/#auth-password-validators

try:
    if REDIS_CONNSTR := env("REDIS_CONNSTR"):
        os.environ["CACHE_DEFAULT"] = f"redisraw://{REDIS_CONNSTR},client_class=django_redis.client.DefaultClient"
except Exception as e:  # pragma: no cover
    logging.exception(e)

CACHES = {
    "default": env.cache_url("CACHE_DEFAULT"),
}

if DEBUG:  # pragma: no cover
    AUTH_PASSWORD_VALIDATORS = []
else:  # pragma: no cover
    AUTH_PASSWORD_VALIDATORS = [
        {
            "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
        },
        {
            "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        },
        {
            "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
        },
        {
            "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
        },
    ]

# Internationalization
# https://docs.djangoproject.com/en/3.1/topics/i18n/

LANGUAGE_CODE = env("LANGUAGE_CODE")
LANGUAGE_COOKIE_NAME = "smart-register-language"

# As per http://www.lingoes.net/en/translator/langcode.htm
LANGUAGES = (
    ("en-us", "English | English"),
    ("ar-ae", " | عربي" + "Arabic"),
    ("cs-cz", "čeština | Czech"),
    ("de-de", "Deutsch | German"),
    ("es-es", "Español | Spanish"),
    ("fr-fr", "Français | French"),
    ("hu-hu", "Magyar | Hungarian"),
    ("it-it", "Italiano | Italian"),
    ("pl-pl", "Polskie | Polish"),
    ("pt-pt", "Português | Portuguese"),
    ("ro-ro", "Română | Romanian"),
    ("ru-ru", "Русский | Russian"),
    ("si-si", "සිංහල | Sinhala"),
    ("ta-ta", "தமிழ் | Tamil"),
    ("uk-ua", "український | Ukrainian"),
    ("hi-hi", "हिंदी | Hindi"),  # Hindi
)
LOCALE_PATHS = (str(PACKAGE_DIR / "LOCALE"),)

SESSION_COOKIE_AGE = 60 * 60 * 24 * 7  # 7 days
# SESSION_COOKIE_DOMAIN = env('SESSION_COOKIE_DOMAIN')
SESSION_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_SECURE = False
SESSION_COOKIE_NAME = env("SESSION_COOKIE_NAME")
SESSION_ENGINE = "django.contrib.sessions.backends.signed_cookies"
SESSION_COOKIE_HTTPONLY = True
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_COOKIE_HTTPONLY = False  # for offline forms

TIME_ZONE = "UTC"

USE_I18N = True

USE_L10N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.1/howto/static-files/
# STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")
# Ensure STATIC_ROOT exists.
# os.makedirs(STATIC_ROOT, exist_ok=True)

# STATIC_URL = f"/static/{os.environ.get('VERSION', '')}/"
STATIC_URL = env("STATIC_URL")
STATIC_ROOT = env("STATIC_ROOT") + STATIC_URL  # simplify nginx config

STORAGES = {
    "default": {
        "BACKEND": env("DEFAULT_FILE_STORAGE"),
    },
    "staticfiles": {
        "BACKEND": env("STATICFILES_STORAGE"),
    },
}

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "web/static"),
    os.path.join(BASE_DIR, "flatpages/static"),
]

# -------- Added Settings
ADMINS = env("ADMINS")
AUTHENTICATION_BACKENDS = [
    "aurora.security.backend.AuroraAuthBackend",
    # "aurora.security.backend.RegistrationAuthBackend",
    # "aurora.security.backend.OrganizationAuthBackend",
    # "django.contrib.auth.backends.ModelBackend",
    "social_core.backends.azuread_tenant.AzureADTenantOAuth2",
] + env("AUTHENTICATION_BACKENDS")

CSRF_COOKIE_NAME = env("CSRF_COOKIE_NAME")
CSRF_HEADER_NAME = "HTTP_X_CSRFTOKEN"
CSRF_COOKIE_SECURE = False
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
USE_X_FORWARDED_HOST = env("USE_X_FORWARDED_HOST")

EMAIL_BACKEND = env("EMAIL_BACKEND")
EMAIL_DEFAULT_FROM = env("EMAIL_FROM_EMAIL")
EMAIL_HOST = env("EMAIL_HOST")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD")
EMAIL_HOST_USER = env("EMAIL_HOST_USER")
EMAIL_PORT = env("EMAIL_PORT")
EMAIL_TIMEOUT = env("EMAIL_TIMEOUT")
EMAIL_USE_SSL = env("EMAIL_USE_SSL")
EMAIL_USE_TLS = env("EMAIL_USE_TLS")

# FORM_RENDERER = 'django.forms.renderers.TemplatesSetting'
LOGIN_REDIRECT_URL = "index"
LOGOUT_REDIRECT_URL = "index"
# LOGIN_URL = "/login"
# USER_LOGIN_URL = "/login"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    # "filters": {"require_debug_false": {"()": "django.utils.log.RequireDebugFalse"}},
    "formatters": {"verbose": {"format": "%(levelname)s %(asctime)s %(module)s: %(message)s"}},
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "verbose"},
        "null": {
            "class": "logging.NullHandler",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "ERROR",
    },
    "loggers": {
        "selector_events": {
            "handlers": ["console"],
            "level": "ERROR",
        },
        "flags": {
            "handlers": ["console"],
            "level": "ERROR",
        },
        "front_door": {
            "handlers": ["console"],
            "level": "ERROR",
        },
        "front_door.middleware": {
            "handlers": ["console"],
            "level": "CRITICAL",
        },
        "django": {
            "handlers": ["console"],
            "level": "ERROR",
        },
        "aurora": {
            "handlers": ["console"],
            "level": env("LOG_LEVEL"),
        },
    },
}

# ------ Custom App

DATE_INPUT_FORMATS = [
    "%Y-%m-%d",  # '2006-10-25'
    "%Y/%m/%d",  # '2006/10/25'
    "%m/%d/%Y",  # '10/25/2006'
    "%m/%d/%y",  # '10/25/06'
    "%b %d %Y",  # 'Oct 25 2006'
    "%b %d, %Y",  # 'Oct 25, 2006'
    "%d %b %Y",  # '25 Oct 2006'
    "%d %b, %Y",  # '25 Oct, 2006'
    "%B %d %Y",  # 'October 25 2006'
    "%B %d, %Y",  # 'October 25, 2006'
    "%d %B %Y",  # '25 October 2006'
    "%d %B, %Y",  # '25 October, 2006'
]

MAX_OBSERVED = 1


RATELIMIT = {
    "PERIODS": {
        "s": 1,
        "m": 60,
        "h": 60 * 60,
        "d": 24 * 60 * 60,
        "w": 7 * 60 * 60,
        "M": 30 * 24 * 60 * 60,
        "y": 365 * 24 * 60 * 60,
    }
}

AA_PERMISSION_HANDLER = 3  # AA_PERMISSION_CREATE_USE_APPCONFIG

INTERNAL_IPS = env.list("INTERNAL_IPS")


ROOT_TOKEN = env("ROOT_TOKEN")
CSRF_FAILURE_VIEW = "aurora.web.views.site.error_csrf"

# WARNING: Do NOT touch this line before it will reach out production
AUTH_USER_MODEL = "auth.User"
# AUTH_USER_MODEL = "security.AuroraUser"

# fix admin name
LOGIN_URL = "/login"
LOGIN_REDIRECT_URL = "/logged-in/"

# allow upload big file
DATA_UPLOAD_MAX_MEMORY_SIZE = 1024 * 1024 * 2  # 2M
FILE_UPLOAD_MAX_MEMORY_SIZE = DATA_UPLOAD_MAX_MEMORY_SIZE

HTTP2_PRELOAD_HEADERS = True
HTTP2_PRESEND_CACHED_HEADERS = True
HTTP2_SERVER_PUSH = False

SECURE_HSTS_SECONDS = 60
SECURE_HSTS_INCLUDE_SUBDOMAINS = True

SILENCED_SYSTEM_CHECKS = ["debug_toolbar.W006", "urls.W005", "admin_extra_buttons.PERM"]


MIGRATION_LOCK_KEY = env("MIGRATION_LOCK_KEY")

from .fragments import *  # noqa
