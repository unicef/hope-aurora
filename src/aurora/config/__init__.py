import uuid
from urllib.parse import urlencode, urlparse

from environ import Env
from smart_env import SmartEnv

from aurora.core.flags import parse_bool


def parse_bookmarks(value):
    return "".join(value.split(r"\n"))


def parse_emails(value):
    admins = value.split(",")
    return [(a.split("@")[0].strip(), a.strip()) for a in admins]


OPTIONS = {
    "ADMINS": (parse_emails, ""),
    "ADMIN_SYNC_CONFIG": (str, "admin_sync.conf.DjangoConstance"),
    "ADMIN_SYNC_LOCAL_ADMIN_URL": (str, ""),
    "ADMIN_SYNC_REMOTE_ADMIN_URL": (str, ""),
    "ADMIN_SYNC_REMOTE_SERVER": (str, ""),
    "ALLOWED_HOSTS": (list, ["*"]),
    "AUTHENTICATION_BACKENDS": (list, []),
    "AZURE_AUTHORITY_HOST": (str, ""),
    "AZURE_CLIENT_ID": (str, ""),
    "AZURE_CLIENT_KEY": (str, ""),
    "AZURE_CLIENT_SECRET": (str, ""),
    "AZURE_POLICY_NAME": (str, ""),
    "AZURE_TENANT_ID": (str, ""),
    "AZURE_TENANT_KEY": (str, ""),
    "AZURE_TRANSLATOR_KEY": (str, ""),
    "AZURE_TRANSLATOR_LOCATION": (str, ""),
    "CACHE_DEFAULT": (str, "locmemcache://", "", True),
    "CAPTCHA_TEST_MODE": (bool, "false"),
    "CHANNEL_LAYER": (str, "locmemcache://", True),
    "CONSTANCE_DATABASE_CACHE_BACKEND": (str, ""),
    "CORS_ALLOWED_ORIGINS": (list, []),
    "CSP_REPORT_ONLY": (bool, False, True),
    "CSRF_COOKIE_NAME": (str, "aurora"),
    "CSRF_COOKIE_SECURE": (bool, True, False),
    "CSRF_TRUSTED_ORIGINS": (list, [], []),
    "DATABASE_URL": (str, "psql://postgres:@postgres:5432/aurora", True),
    "DEBUG": (bool, False),
    "DEBUG_PROPAGATE_EXCEPTIONS": (bool, False),
    "DEFAULT_FILE_STORAGE": (str, "django.core.files.storage.FileSystemStorage"),
    "DJANGO_ADMIN_URL": (str, f"{uuid.uuid4().hex}/", True),
    "EMAIL_BACKEND": (str, "anymail.backends.mailjet.EmailBackend"),
    "EMAIL_FROM_EMAIL": (str, ""),
    "EMAIL_HOST": (str, ""),
    "EMAIL_HOST_PASSWORD": (str, ""),
    "EMAIL_HOST_USER": (str, ""),
    "EMAIL_PORT": (int, 587),
    "EMAIL_SUBJECT_PREFIX": (str, "[Aurora]"),
    "EMAIL_TIMEOUT": (int, 30),
    "EMAIL_USE_LOCALTIME": (bool, False),
    "EMAIL_USE_SSL": (bool, False),
    "EMAIL_USE_TLS": (bool, True),
    "FERNET_KEY": (str, "", uuid.uuid4().hex, True),
    "FRONT_DOOR_ALLOWED_PATHS": (str, ".*"),
    "FRONT_DOOR_ENABLED": (bool, False),
    "FRONT_DOOR_LOG_LEVEL": (str, "ERROR"),
    "FRONT_DOOR_TOKEN": (str, uuid.uuid4()),
    "INTERNAL_IPS": (list, [], ["127.0.0.1", "localhost"]),
    "JWT_LEEWAY": (int, 0),
    "LANGUAGE_CODE": (str, "en-us"),
    "LOG_LEVEL": (str, "ERROR"),
    "MAILJET_API_KEY": (str, ""),
    "MAILJET_SECRET_KEY": (str, ""),
    "MATOMO_ID": (str, "", "", False),
    "MATOMO_SITE": (str, "https://unisitetracker.unicef.io/"),
    "MEDIA_ROOT": (str, "/tmp/media/"),  # noqa
    "MIGRATION_LOCK_KEY": (str, "django-migrations"),
    "PRODUCTION_SERVER": (str, ""),
    "PRODUCTION_TOKEN": (str, ""),
    "REDIS_CONNSTR": (str, ""),
    "ROOT_KEY": (str, ""),
    "ROOT_TOKEN": (str, ""),
    "SECRET_KEY": (str, "", "", True),
    "SENTRY_DSN": (str, ""),
    "SENTRY_ENVIRONMENT": (str, ""),
    "SENTRY_PROJECT": (str, ""),
    "SENTRY_SECURITY_TOKEN": (str, ""),
    "SENTRY_SECURITY_TOKEN_HEADER": (str, "X-Sentry-Token"),
    "SESSION_COOKIE_DOMAIN": (str, "", "", True),
    "SESSION_COOKIE_NAME": (str, "aurora_id"),
    "SESSION_COOKIE_SECURE": (bool, True, False, True),
    "SITE_ID": (int, 1),
    "SMART_ADMIN_BOOKMARKS": (parse_bookmarks, ""),
    "STATICFILES_STORAGE": (
        str,
        "aurora.web.storage.ForgivingManifestStaticFilesStorage",
    ),
    "STATIC_ROOT": (str, "/tmp/static/"),  # noqa
    "STATIC_URL": (str, "static/"),
    "TRANSLATOR_SERVICE": (str, ""),
    "USE_HTTPS": (bool, False),
    "USE_X_FORWARDED_HOST": (bool, "false"),
}


class SmartEnv2(SmartEnv):
    def cache_url(self, var=Env.DEFAULT_CACHE_ENV, default=Env.NOTSET, backend=None):
        v = self.str(var, default)
        if v.startswith("redisraw://"):
            scheme, string = v.split("redisraw://")
            host, *options = string.split(",")
            config = dict([v.split("=", 1) for v in options])
            if parse_bool(config.get("ssl", "false")):
                scheme = "rediss"
            else:
                scheme = "redis"
            auth = ""
            credentials = [config.pop("user", ""), config.pop("password", "")]
            if credentials[0] or credentials[1]:
                auth = f"{':'.join(credentials)}@"
            new_url = f"{scheme}://{auth}{host}/?{urlencode(config)}"
            return self.cache_url_config(urlparse(new_url), backend=backend)
        return super().cache_url(var, default, backend)


env = SmartEnv2(**OPTIONS)
