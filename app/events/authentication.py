import base64
import hashlib
import hmac

from django.conf import settings
from rest_framework import authentication, exceptions


class HMACAuthentication(authentication.BaseAuthentication):
    HMAC_HEADER = "X-HMAC-Signature"

    def authenticate(self, request):
        secret_key = getattr(settings, "HMAC_SECRET_KEY", None)
        if not secret_key:
            raise exceptions.AuthenticationFailed("HMAC key is not configured.")

        signature_header = request.META.get(f'HTTP_{self.HMAC_HEADER.upper().replace("-", "_")}')
        if not signature_header:
            return None

        try:
            request.body
        except Exception:
            return None

        expected_signature = self._calculate_hmac(request.body, secret_key.encode("utf-8"))

        if not hmac.compare_digest(signature_header.encode("utf-8"), expected_signature):
            raise exceptions.AuthenticationFailed("HMAC signature verification failed.")

        return (None, None)

    def authenticate_header(selfself, request):
        return "HMAC signature verification"

    @staticmethod
    def _calculate_hmac(data, key):
        hash_digest = hmac.new(key, data, hashlib.sha256).digest()
        return base64.b64encode(hash_digest)
