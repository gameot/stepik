import json

import pytest
from django.conf import settings
from rest_framework.test import APIRequestFactory

from events.models import Event


@pytest.fixture(autouse=True)
def setup_settings():
    settings.HMAC_SECRET_KEY = "test_secret_key_12345"


@pytest.fixture
def factory():
    return APIRequestFactory()


@pytest.fixture
def valid_payload():
    data = {
        "event_id": "test-123",
        "event_type": "order_created",
        "order_id": "provider-123",
        "date": "2020-12-01 01:02:03",
        "data": {"note": "some data"},
    }
    return json.dumps(data).encode("utf-8")


@pytest.fixture
def create_event(db):
    def _create_event(provider_event_id="test-event-1", order_id="100", status=Event.STATUS_NEW):
        return Event.objects.create(
            provider_event_id=provider_event_id,
            order_id=order_id,
            data="{}",
            status=status,
        )

    return _create_event
