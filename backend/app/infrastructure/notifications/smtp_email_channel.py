from email.message import EmailMessage
from email.utils import make_msgid

import aiosmtplib

from app.core.config import get_settings
from app.domain.value_objects import DeliveryResult


class SmtpEmailChannel:
    """NotificationChannel adapter over SMTP. See PROJECT.md §10."""

    def __init__(self):
        self._settings = get_settings()

    async def send(self, to: str, subject: str, body: str) -> DeliveryResult:
        message = EmailMessage()
        message["From"] = self._settings.smtp_from_email
        message["To"] = to
        message["Subject"] = subject
        message_id = make_msgid()
        message["Message-ID"] = message_id
        message.set_content(body)

        try:
            await aiosmtplib.send(
                message,
                hostname=self._settings.smtp_host,
                port=self._settings.smtp_port,
                username=self._settings.smtp_username or None,
                password=self._settings.smtp_password or None,
                start_tls=self._settings.smtp_use_tls,
            )
        except Exception as exc:
            return DeliveryResult(success=False, error=str(exc))
        return DeliveryResult(success=True, provider_message_id=message_id)
