from app.domain.enums import ContactMethod
from app.domain.exceptions import UnsupportedContactMethodError
from app.domain.ports import NotificationChannel


class NotificationRouter:
    """Resolves a NotificationChannel adapter for a ContactMethod. See PROJECT.md §10.

    V1 registers only EMAIL. Adding WhatsApp later (ADR-1) means registering
    another adapter here — callers never change.
    """

    def __init__(self, channels: dict[ContactMethod, NotificationChannel]):
        self._channels = channels

    def resolve(self, method: ContactMethod) -> NotificationChannel:
        channel = self._channels.get(method)
        if channel is None:
            raise UnsupportedContactMethodError(method.value)
        return channel
