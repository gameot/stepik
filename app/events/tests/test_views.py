import ast
import json
from unittest.mock import patch

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.exceptions import AuthenticationFailed

from events.models import Event


@pytest.mark.django_db
class TestEventCreateAPIView:
    @staticmethod
    def _get_path():
        return reverse("events:event-create")

    def test_create_event_success_and_db_record(self, client, valid_payload):
        signature = "some_signature"

        initial_count = Event.objects.count()

        with patch(
            "app.events.views.HMACAuthentication.authenticate",
            return_value=(None, None),
        ) as auth_mock:
            response = client.post(
                self._get_path(),
                data=valid_payload,
                content_type="application/json",
                HTTP_X_HMAC_SIGNATURE=signature,
            )

        assert auth_mock.call_count == 1
        assert response.status_code == status.HTTP_200_OK

        assert Event.objects.count() == initial_count + 1

        decoded_data = json.loads(valid_payload.decode("utf-8"))

        event = Event.objects.get(provider_event_id=decoded_data["event_id"])
        assert event.status == Event.STATUS_NEW

    def test_create_event_fails_if_hmac_is_incorrect(self, client, valid_payload):
        incorrect_signature = "incorrect_signature"
        initial_count = Event.objects.count()

        with patch(
            "app.events.views.HMACAuthentication.authenticate",
            side_effect=AuthenticationFailed(),
        ) as auth_mock:
            response = client.post(
                self._get_path(),
                data=valid_payload,
                content_type="application/json",
                HTTP_X_HMAC_SIGNATURE=incorrect_signature,
            )

        assert auth_mock.call_count == 1
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert Event.objects.count() == initial_count

    def test_create_event_fails_if_data_is_invalid(self, client, valid_payload):
        signature = "some_signature"

        invalid_data = {
            "event_id": "test-123",
            "event_type": "order_created",
            "date": "2020-12-01 01:02:03",
            "data": {"note": "some data"},
        }
        del invalid_data["event_id"]

        initial_count = Event.objects.count()

        with patch(
            "app.events.views.HMACAuthentication.authenticate",
            return_value=(None, None),
        ) as auth_mock:
            response = client.post(self._get_path(), data=invalid_data, HTTP_X_HMAC_SIGNATURE=signature)

        assert auth_mock.call_count == 1
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "event_id" in response.json()

        assert Event.objects.count() == initial_count
