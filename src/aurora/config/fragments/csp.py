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
# CSP_SCRIPT_SRC = SOURCES
# CSP_STYLE_SRC = (
#     "'self'",
#     "'data'",
#     "'unsafe-inline'",
#     "https://unpkg.com",
#     "http://localhost:8000",
#     "https://cdnjs.cloudflare.com",
#     "http://cdnjs.cloudflare.com",
#
# )
# CSP_OBJECT_SRC = ("self",)
# CSP_BASE_URI = ("self", "http://localhost:8000",)
# CSP_CONNECT_SRC = ("self",)
# CSP_FONT_SRC = ("self",)
# CSP_FRAME_SRC = ("self",)
# CSP_IMG_SRC = ("self", "data")
# CSP_MANIFEST_SRC = ("self",)
# CSP_MEDIA_SRC = ("self",)
# CSP_REPORT_URI = ("https://624948b721ea44ac2a6b4de4.endpoint.csper.io/?v=0;",)
# CSP_WORKER_SRC = ("self",)
# """default-src 'self';
# script-src 'report-sample' 'self';
# style-src 'report-sample' 'self';
# object-src 'none';
#
# base-uri 'self';
# connect-src 'self';
# font-src 'self';
# frame-src 'self';
# img-src 'self';
# manifest-src 'self';
# media-src 'self';
# report-uri https://624948b721ea44ac2a6b4de4.endpoint.csper.io/?v=0;
# worker-src 'none';
# """

# CSP_INCLUDE_NONCE_IN = env("CSP_INCLUDE_NONCE_IN")
# CSP_REPORT_ONLY = env("CSP_REPORT_ONLY")
# CSP_DEFAULT_SRC = env("CSP_DEFAULT_SRC")
# CSP_SCRIPT_SRC = env("CSP_SCRIPT_SRC")
