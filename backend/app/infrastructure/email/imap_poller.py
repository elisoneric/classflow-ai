"""IMAP polling for inbound lecturer replies. See PROJECT.md §9/ADR-2.

Uses BODY.PEEK[] rather than a plain FETCH so messages aren't marked \\Seen
until the caller has successfully processed and persisted them — a poll that
crashes mid-batch won't silently lose a lecturer's reply. Reconnects on every
call rather than holding a persistent IMAP connection; at ~75s polling
intervals and a handful of messages a day this is a deliberate simplicity
trade-off, not an oversight.
"""

import asyncio
import email
import imaplib
from dataclasses import dataclass
from datetime import UTC, datetime
from email.message import Message
from email.utils import parseaddr

from app.core.config import get_settings


@dataclass(frozen=True, slots=True)
class InboundEmailMessage:
    uid: bytes
    message_id: str
    in_reply_to: str | None
    from_address: str
    body: str
    received_at: datetime


def _extract_plain_body(message: Message) -> str:
    if message.is_multipart():
        for part in message.walk():
            content_disposition = str(part.get("Content-Disposition", ""))
            if part.get_content_type() == "text/plain" and "attachment" not in content_disposition:
                payload = part.get_payload(decode=True)
                if payload is None:
                    continue
                charset = part.get_content_charset() or "utf-8"
                return payload.decode(charset, errors="replace")
        return ""
    payload = message.get_payload(decode=True)
    if payload is None:
        return message.get_payload() or ""
    charset = message.get_content_charset() or "utf-8"
    return payload.decode(charset, errors="replace")


def _in_reply_to(message: Message) -> str | None:
    in_reply_to = message.get("In-Reply-To")
    if in_reply_to:
        return in_reply_to.strip()
    references = message.get("References")
    if references:
        return references.split()[-1].strip()
    return None


class ImapEmailPoller:
    def __init__(self):
        self._settings = get_settings()

    def _connect(self) -> imaplib.IMAP4:
        settings = self._settings
        conn: imaplib.IMAP4
        if settings.imap_use_ssl:
            conn = imaplib.IMAP4_SSL(settings.imap_host, settings.imap_port)
        else:
            conn = imaplib.IMAP4(settings.imap_host, settings.imap_port)
        conn.login(settings.imap_username, settings.imap_password)
        conn.select(settings.imap_mailbox)
        return conn

    @staticmethod
    def _disconnect(conn: imaplib.IMAP4) -> None:
        try:
            conn.close()
        except Exception:
            pass
        conn.logout()

    def _fetch_unseen_sync(self) -> list[InboundEmailMessage]:
        conn = self._connect()
        try:
            status, data = conn.search(None, "UNSEEN")
            if status != "OK" or not data or not data[0]:
                return []
            results: list[InboundEmailMessage] = []
            for uid in data[0].split():
                status, msg_data = conn.fetch(uid, "(BODY.PEEK[])")
                if status != "OK" or not msg_data or msg_data[0] is None:
                    continue
                raw = msg_data[0][1]
                message = email.message_from_bytes(raw)
                results.append(
                    InboundEmailMessage(
                        uid=uid,
                        message_id=(message.get("Message-ID") or "").strip(),
                        in_reply_to=_in_reply_to(message),
                        from_address=parseaddr(message.get("From", ""))[1],
                        body=_extract_plain_body(message),
                        received_at=datetime.now(UTC),
                    )
                )
            return results
        finally:
            self._disconnect(conn)

    def _mark_seen_sync(self, uid: bytes) -> None:
        conn = self._connect()
        try:
            conn.store(uid, "+FLAGS", "\\Seen")
        finally:
            self._disconnect(conn)

    async def fetch_unseen(self) -> list[InboundEmailMessage]:
        return await asyncio.to_thread(self._fetch_unseen_sync)

    async def mark_seen(self, uid: bytes) -> None:
        await asyncio.to_thread(self._mark_seen_sync, uid)
