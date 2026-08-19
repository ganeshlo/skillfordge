import hashlib
import hmac
import time
from fastapi import HTTPException, Request, status

MAX_CLOCK_SKEW_SECONDS = 60


async def verify_request(request: Request, secret: str):
    if not secret:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Controller signing secret is not configured")
    timestamp = request.headers.get("X-LearnOS-Timestamp", "")
    supplied = request.headers.get("X-LearnOS-Signature", "")
    try:
        timestamp_number = int(timestamp)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid request signature")
    if abs(int(time.time()) - timestamp_number) > MAX_CLOCK_SKEW_SECONDS:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Expired request signature")
    body = (await request.body()).decode()
    message = f"{timestamp}.{request.method.upper()}.{request.url.path}.{body}".encode()
    expected = hmac.new(secret.encode(), message, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, supplied):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid request signature")

