SOURCES = (
    "'self'",
    "inline",
    "unsafe-inline",
    "data:",
    "blob:",
    "'unsafe-inline'",
    "localhost:8000",
    "unpkg.com",
    "browser.sentry-cdn.com",
    "cdnjs.cloudflare.com",
    "unisitetracker.unicef.io",
    "cdn.jsdelivr.net",
    "register.unicef.org",
    "uni-hope-ukr-sr.azurefd.net",
    "uni-hope-ukr-sr-dev.azurefd.net",
    "uni-hope-ukr-sr-dev.unitst.org",
)

CSP_DEFAULT_SRC = SOURCES
CSP_FRAME_ANCESTORS = ("'self'",)
