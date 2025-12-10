import base64
import hashlib
import hmac

import pytest
from django.conf import settings
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.reverse import reverse

from app.events.authentication import HMACAuthentication


def generate_hmac_signature(body: bytes, secret_key: str) -> str:
    key = secret_key.encode("utf-8")
    hash_digest = hmac.new(key, body, hashlib.sha256).digest()
    return base64.b64encode(hash_digest).decode("utf-8")


class TestHMACAuthentication:
    auth = HMACAuthentication()

    @staticmethod
    def _get_path():
        return reverse("events:event-create")

    def test_successful_authentication_with_valid_signature(self, factory, valid_payload):
        secret = settings.HMAC_SECRET_KEY
        signature = generate_hmac_signature(valid_payload, secret)
        request = factory.post(self._get_path(), data=valid_payload, content_type="application/json")
        request.META[f'HTTP_{self.auth.HMAC_HEADER.upper().replace("-", "_")}'] = signature
        result = self.auth.authenticate(request)
        assert result == (None, None)

    def test_failed_authentication_with_incorrect_signature(self, factory, valid_payload):
        incorrect_signature = generate_hmac_signature(b"corrupted body", settings.HMAC_SECRET_KEY)
        request = factory.post(self._get_path(), data=valid_payload, content_type="application/json")
        request.META[f'HTTP_{self.auth.HMAC_HEADER.upper().replace("-", "_")}'] = incorrect_signature

        with pytest.raises(AuthenticationFailed) as exc_info:
            self.auth.authenticate(request)

        assert "verification failed" in str(exc_info.value)

    def test_failed_authentication_with_modified_body(self, factory, valid_payload):
        secret = settings.HMAC_SECRET_KEY
        correct_signature = generate_hmac_signature(valid_payload, secret)
        corrupted_payload = b'{"event_id": "test-123", "data": "corrupted"}'
        request = factory.post(self._get_path(), data=corrupted_payload, content_type="application/json")
        request.META[f'HTTP_{self.auth.HMAC_HEADER.upper().replace("-", "_")}'] = correct_signature

        with pytest.raises(AuthenticationFailed) as exc_info:
            self.auth.authenticate(request)

        assert "verification failed" in str(exc_info.value)

    def test_no_authentication_when_header_is_missing(self, factory):
        request = factory.post(self._get_path(), data={})
        result = self.auth.authenticate(request)
        assert result is None

    @pytest.mark.parametrize(
        "data_str, key_str, expected_base64_signature",
        [
            (
                "test_body_data",
                "secret_key_123",
                "NNHJ4xVm7hVYYJCt1423/JOFM8wAS4Agb+aupHvmUrc=",  # Valid HMAC
            ),
            (
                "",
                "secret_key_123",
                "m2n3KQqYdgD7QrqDszcRddV0COjfY9Ys3kfGyCUhyXE=",
            ),
            (
                "test_body_data",
                "different_secret",
                "J50Of58Cl9A+bjzUPfSk3GxQ/A6kiF1l5fNAKU76zSU=",
            ),
            (
                '{"field": "value", "count": 100}',
                "super_secure_key",
                "gOgg3Nwl/M8yr4FOmEhUNhx5EIRyToqbspT+ewM4rK4=",
            ),
        ],
    )
    def test_calculate_hmac_returns_correct_base64_signature(self, data_str, key_str, expected_base64_signature):
        data_bytes = data_str.encode("utf-8")
        key_bytes = key_str.encode("utf-8")

        actual_signature_bytes = HMACAuthentication()._calculate_hmac(data_bytes, key_bytes)
        actual_signature_str = actual_signature_bytes.decode("utf-8")
        assert actual_signature_str == expected_base64_signature

    def test_calculate_hmac_matches_standard_python_library(self, valid_payload):
        test_key = b"A_SECRET_KEY"
        test_data = b"some_sample_data"

        expected_digest = hmac.new(test_key, test_data, hashlib.sha256).digest()
        expected_base64 = base64.b64encode(expected_digest)

        actual_base64 = HMACAuthentication()._calculate_hmac(test_data, test_key)

        assert actual_base64 == expected_base64
