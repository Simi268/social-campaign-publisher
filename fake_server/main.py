import hashlib
import hmac
import os
import uuid
from datetime import datetime, timezone

from fastapi import FastAPI, Header, HTTPException, Request
from pydantic import BaseModel


app = FastAPI(
    title="Fake Social Platform Server",
    version="1.0.0",
)


WEBHOOK_SECRET = os.getenv(
    "FAKE_WEBHOOK_SECRET",
    "local-webhook-secret",
)

ACCESS_TOKEN = "fake-access-token"

# In-memory state intentionally keeps the fake server simple.
posts_by_idempotency_key: dict[str, dict] = {}

# Set this to True through the test endpoint to simulate a 429.
rate_limit_enabled = False


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class PublishRequest(BaseModel):
    platform: str
    caption: str
    image_path: str | None = None


@app.get("/")
def root():
    return {
        "name": "Fake Social Platform Server",
        "status": "ok",
    }


@app.post("/auth/token", response_model=TokenResponse)
def issue_token():
    return TokenResponse(
        access_token=ACCESS_TOKEN,
    )


@app.post("/test/rate-limit")
def enable_rate_limit():
    global rate_limit_enabled

    rate_limit_enabled = True

    return {
        "rate_limit_enabled": True,
    }


@app.post("/test/reset")
def reset_fake_server():
    global rate_limit_enabled

    posts_by_idempotency_key.clear()
    rate_limit_enabled = False

    return {
        "status": "reset",
    }


@app.post("/publish")
def publish(
    payload: PublishRequest,
    authorization: str | None = Header(default=None),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
):
    global rate_limit_enabled

    if authorization != f"Bearer {ACCESS_TOKEN}":
        raise HTTPException(
            status_code=401,
            detail="Invalid access token",
        )

    if not idempotency_key:
        raise HTTPException(
            status_code=400,
            detail="Idempotency-Key header is required",
        )

    # Simulate rate limiting.
    if rate_limit_enabled:
        rate_limit_enabled = False

        from fastapi.responses import JSONResponse

        return JSONResponse(
            status_code=429,
            content={
                "error": "rate_limited",
            },
            headers={
                "Retry-After": "1",
            },
        )

    # Idempotency:
    # the same key returns the original result instead
    # of creating another post.
    if idempotency_key in posts_by_idempotency_key:
        return posts_by_idempotency_key[idempotency_key]

    post_id = f"{payload.platform}-{uuid.uuid4().hex[:12]}"

    result = {
        "external_post_id": post_id,
        "platform": payload.platform,
        "status": "queued",
        "caption": payload.caption,
        "image_path": payload.image_path,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    posts_by_idempotency_key[idempotency_key] = result

    return result


@app.post("/webhook/deliver")
async def deliver_webhook(
    request: Request,
):
    body = await request.body()

    signature = request.headers.get(
        "X-Webhook-Signature",
    )

    if not signature:
        raise HTTPException(
            status_code=400,
            detail="Missing webhook signature",
        )

    expected_signature = hmac.new(
        WEBHOOK_SECRET.encode(),
        body,
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(
        signature,
        expected_signature,
    ):
        raise HTTPException(
            status_code=400,
            detail="Invalid webhook signature",
        )

    return {
        "status": "accepted",
    }


@app.post("/test/signature")
async def generate_signature(request: Request):
    body = await request.body()

    signature = hmac.new(
        WEBHOOK_SECRET.encode(),
        body,
        hashlib.sha256,
    ).hexdigest()

    return {
        "signature": signature,
    }