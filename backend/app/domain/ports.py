"""
Interfaces the application layer depends on. Infrastructure provides the
implementations (adapters). See PROJECT.md §10 (notifications) and §11 (AI).

Repository protocols are declared per-feature in each feature's service module
rather than centralized here — see app/application/<feature>/ports.py — so
each slice only depends on the query shapes it actually needs.
"""

from typing import Protocol

from app.domain.value_objects import DeliveryResult, Interpretation, SessionContext


class NotificationChannel(Protocol):
    async def send(self, to: str, subject: str, body: str) -> DeliveryResult: ...


class MessageInterpreter(Protocol):
    async def interpret(
        self, raw_message: str, context: SessionContext
    ) -> Interpretation: ...
