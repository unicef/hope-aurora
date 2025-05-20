import logging

from django.utils.translation import gettext as _
from django.db.models import TextChoices
import bitcaster_sdk

from aurora.config import env

logger = logging.getLogger(__name__)


class BitcasterEvents(TextChoices):
    USER_REGISTERED = "user_registered", _("User registered")
    GENERATE_PASSWORD = "generate_password", _("Generate password")


class BitcasterEventManager:
    """
    Manage and send events to Bitcaster:
    - define messages
    - create subject/body
    - send events
    """

    def __init__(
            self, project: str | None = env("BITCASTER_PRJ_SLUG"), application: str | None = env("BITCASTER_APP_SLUG")
    ) -> None:
        self.project = project
        self.application = application
        bitcaster_sdk.init()

    CONTEXT = {
        BitcasterEvents.USER_REGISTERED: {
            "required_context": ["user"],
        },
        BitcasterEvents.GENERATE_PASSWORD: {
            "required_context": ["user", "email", "pwd", "login_url"],
        },
    }

    @classmethod
    def check_context(cls, event: BitcasterEvents, context: dict) -> None:
        if event not in cls.CONTEXT:
            raise ValueError(f"Unknown event {event}, possible events: {list(cls.CONTEXT.keys())}")
        if not all(key in context.keys() for key in cls.CONTEXT[event]["required_context"]):
            raise ValueError(f"Missing context keys {cls.CONTEXT[event]['required_context']}")
        return

    def trigger(self, event: BitcasterEvents, context: dict, options: dict | None = None):
        """
        Trigger event.
        """
        self.check_context(event, context)
        event_slug = str(event.value)

        bitcaster_sdk.trigger(self.project, self.application, event_slug, context=context, options=options)
        logger.info(
            f"Bitcaster event '{event_slug}' triggered for project '{self.project}', application '{self.application}'"
        )
