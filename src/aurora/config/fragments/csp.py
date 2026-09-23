# Content-Security-Policy (django-csp).
#
# django-csp >= 4.0 uses the CONTENT_SECURITY_POLICY dict format.
# The legacy CSP_* top-level settings are no longer honored and only emit
# a warning via the csp.E001 system check.
#
# `'unsafe-inline'` / `'unsafe-eval'` are still required by the bundled
# admin/editor/charting assets. Migrating away from them (nonces / hashes,
# strict CSP) must be done incrementally; start with CONTENT_SECURITY_POLICY
# in "report-only" mode and monitor before enforcing a stricter policy, see
# https://cheatsheetseries.owasp.org/cheatsheets/Content_Security_Policy_Cheat_Sheet.html
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

FRAME_ANCESTORS = ("'self'",)

CONTENT_SECURITY_POLICY = {
    "DIRECTIVES": {
        "default-src": SOURCES,
        "frame-ancestors": FRAME_ANCESTORS,
        "frame-src": ["'self'"],
        "object-src": ["'none'"],
        "base-uri": ["'self'"],
    },
}
