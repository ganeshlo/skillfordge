import hashlib
import hmac
import json
import time

from django.conf import settings


def signed_headers(*, method, path, body=None):
    timestamp = str(int(time.time()))
    serialized = json.dumps(body, separators=(",", ":"), sort_keys=True) if body is not None else ""
    message = f"{timestamp}.{method.upper()}.{path}.{serialized}".encode()
    signature = hmac.new(settings.EXECUTION_CONTROLLER_SECRET.encode(), message, hashlib.sha256).hexdigest()
    return {
        "X-LearnOS-Timestamp": timestamp,
        "X-LearnOS-Signature": signature,
        "Content-Type": "application/json",
    }, serialized

