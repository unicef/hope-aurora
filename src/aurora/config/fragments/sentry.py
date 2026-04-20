import logging

import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.logging import LoggingIntegration


from .. import env

SENTRY_DSN = env("SENTRY_DSN")
sentry_logging = LoggingIntegration(
    level=logging.INFO,  # Capture info and above as breadcrumbs
    event_level=logging.ERROR,  # Send errors as events
)
if SENTRY_DSN:
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        environment=env("SENTRY_ENVIRONMENT"),
        integrations=[
            DjangoIntegration(transaction_style="url"),
            sentry_logging,
        ],
        send_default_pii=True,
    )
