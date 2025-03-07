from .. import env

CORS_ALLOWED_ORIGINS = [
    "https://excubo.unicef.io",
    "http://localhost:8000",
    "https://browser.sentry-cdn.com",
    "https://cdnjs.cloudflare.com",
    "https://login.microsoftonline.com",
] + env("CORS_ALLOWED_ORIGINS")

CORS_ORIGIN_ALLOW_ALL = True
CORS_ALLOW_CREDENTIALS = True
