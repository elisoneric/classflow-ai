import pytest

from app.domain.enums import ContactMethod
from app.domain.exceptions import UnsupportedContactMethodError
from app.infrastructure.notifications.router import NotificationRouter
from tests.unit.fakes import FakeNotificationChannel


def test_resolves_registered_channel():
    email_channel = FakeNotificationChannel()
    router = NotificationRouter({ContactMethod.EMAIL: email_channel})
    assert router.resolve(ContactMethod.EMAIL) is email_channel


def test_whatsapp_is_unsupported_in_v1():
    router = NotificationRouter({ContactMethod.EMAIL: FakeNotificationChannel()})
    with pytest.raises(UnsupportedContactMethodError):
        router.resolve(ContactMethod.WHATSAPP)
