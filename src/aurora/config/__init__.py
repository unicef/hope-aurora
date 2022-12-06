import uuid
from urllib.parse import urlencode, urlparse

from environ import Env

from aurora.core.flags import parse_bool


def parse_bookmarks(value):
    return "".join(value.split(r"\n"))


def parse_emails(value):
    admins = value.split(",")
    v = [(a.split("@")[0].strip(), a.strip()) for a in admins]
    return v


DEFAULTS = {
    "ADMINS": (parse_emails, ""),
    "ALLOWED_HOSTS": (list, []),
    "AUTHENTICATION_BACKENDS": (list, []),
    "AZURE_CLIENT_ID": (str, None),
    "AZURE_CLIENT_SECRET": (str, None),
    "AZURE_TENANT_KEY": (str, None),
    "CACHE_DEFAULT": (str, "locmemcache://"),
    "CAPTCHA_TEST_MODE": (bool, False),
    "CONSTANCE_DATABASE_CACHE_BACKEND": (str, ""),
    "CORS_ALLOWED_ORIGINS": (list, []),
    "CSP_REPORT_ONLY": (bool, True),
    "DATABASE_URL": (str, "psql://postgres:@postgres:5432/aurora"),
    "DEBUG": (bool, False),
    "DEBUG_PROPAGATE_EXCEPTIONS": (bool, False),
    "DJANGO_ADMIN_TITLE": (str, "Aurora"),
    "DJANGO_ADMIN_URL": (str, f"{uuid.uuid4().hex}/"),
    "EMAIL_BACKEND": (str, "django.core.mail.backends.smtp.EmailBackend"),
    "EMAIL_FROM_EMAIL": (str, ""),
    "EMAIL_HOST": (str, ""),
    "EMAIL_HOST_PASSWORD": (str, ""),
    "EMAIL_HOST_USER": (str, ""),
    "EMAIL_PORT": (int, 587),
    "EMAIL_SUBJECT_PREFIX": (str, "[SmartRegister]"),
    "EMAIL_TIMEOUT": (int, 30),
    "EMAIL_USE_LOCALTIME": (bool, False),
    "EMAIL_USE_SSL": (bool, False),
    "EMAIL_USE_TLS": (bool, True),
    "FERNET_KEY": (str, "2jQklRvSAZUdsVOKH-521Wbf_p5t2nTDA0LgD9sgim4="),
    "INTERNAL_IPS": (list, ["127.0.0.1", "localhost"]),
    "LANGUAGE_CODE": (str, "en-us"),
    "LOG_LEVEL": (str, "ERROR"),
    "MEDIA_ROOT": (str, "/tmp/media/"),
    "MIGRATION_LOCK_KEY": (str, "django-migrations"),
    "PRODUCTION_SERVER": (str, ""),
    "PRODUCTION_TOKEN": (str, ""),
    "REDIS_CONNSTR": (str, ""),
    "ROOT_KEY": (str, uuid.uuid4().hex),
    "ROOT_TOKEN": (str, uuid.uuid4().hex),
    "SECRET_KEY": (str, ""),
    "SENTRY_DSN": (str, ""),
    "SENTRY_PROJECT": (str, ""),
    "SENTRY_SECURITY_TOKEN": (str, ""),
    "SENTRY_SECURITY_TOKEN_HEADER": (str, "X-Sentry-Token"),
    "SESSION_COOKIE_DOMAIN": (str, "localhost"),
    "SESSION_COOKIE_NAME": (str, "reg_id"),
    "SESSION_COOKIE_SECURE": (bool, "false"),
    "SMART_ADMIN_BOOKMARKS": (parse_bookmarks, ""),
    "STATICFILES_STORAGE": (str, "django.contrib.staticfiles.storage.ManifestStaticFilesStorage"),
    "USE_HTTPS": (bool, False),
    "USE_X_FORWARDED_HOST": (bool, "false"),
    "WHITENOISE": (bool, False),
    # "CSP_DEFAULT_SRC": (list, ),
    # "CSP_SCRIPT_SRC": (str, None),
    # "FERNET_KEY": (str, "Nl_puP2z0-OKVNKMtPXx4jEI-ox7sKLM7CgnGT-yAug="),
    # "STATICFILES_STORAGE": (str, "django.contrib.staticfiles.storage.StaticFilesStorage"),
    # "STATIC_ROOT": (str, "/tmp/static/"),
    # Sentry - see CONTRIBUTING.md
}


class SmartEnv(Env):
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


env = SmartEnv(**DEFAULTS)