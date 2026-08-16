import hashlib
import hmac
import json
import os
import uuid

from fastapi.testclient import TestClient

from app.main import app
from app.core.database import SessionLocal
from app.models.campaign import Campaign
from app.models.social_post import SocialPost


client = TestClient(app)

WEBHOOK_SECRET = os.getenv(
    "FAKE_WEBHOOK_SECRET",
    "local-webhook-secret",
)


def sign_payload(payload: dict) -> str:
    body = json.dumps(
        payload,
        separators=(",", ":"),
    ).encode()

    return hmac.new(
        WEBHOOK_SECRET.encode(),
        body,
        hashlib.sha256,
    ).hexdigest()


def create_test_post(external_post_id: str) -> int:
    db = SessionLocal()

    campaign = Campaign(
        title="Webhook Test Campaign",
    )

    db.add(campaign)
    db.commit()
    db.refresh(campaign)

    post = SocialPost(
        campaign_id=campaign.id,
        platform="instagram",
        caption="Webhook test",
        image_path="test.jpg",
        status="QUEUED",
        external_post_id=external_post_id,
        idempotency_key=f"webhook-test-{uuid.uuid4()}",
    )

    db.add(post)
    db.commit()
    db.refresh(post)

    post_id = post.id

    db.close()

    return post_id


def get_post(post_id: int) -> SocialPost:
    db = SessionLocal()

    post = db.get(SocialPost, post_id)

    db.expunge(post)
    db.close()

    return post


def test_valid_webhook_marks_post_published():
    external_id = f"webhook-valid-{uuid.uuid4()}"

    post_id = create_test_post(external_id)

    payload = {
        "external_post_id": external_id,
    }

    body = json.dumps(
        payload,
        separators=(",", ":"),
    ).encode()

    signature = sign_payload(payload)

    response = client.post(
        "/webhook/social-delivery",
        content=body,
        headers={
            "Content-Type": "application/json",
            "X-Webhook-Signature": signature,
        },
    )

    assert response.status_code == 200

    post = get_post(post_id)

    assert post.status == "PUBLISHED"
    assert post.published_at is not None


def test_invalid_webhook_does_not_publish_post():
    external_id = f"webhook-invalid-{uuid.uuid4()}"

    post_id = create_test_post(external_id)

    payload = {
        "external_post_id": external_id,
    }

    body = json.dumps(
        payload,
        separators=(",", ":"),
    ).encode()

    response = client.post(
        "/webhook/social-delivery",
        content=body,
        headers={
            "Content-Type": "application/json",
            "X-Webhook-Signature": "forged-signature",
        },
    )

    assert response.status_code == 400

    post = get_post(post_id)

    assert post.status == "QUEUED"
    assert post.published_at is None