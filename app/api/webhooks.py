import hashlib
import hmac
import os
from datetime import datetime, timezone

from fastapi import APIRouter, Header, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.social_post import SocialPost


router = APIRouter(
    prefix="/webhook",
    tags=["webhooks"],
)


WEBHOOK_SECRET = os.getenv(
    "FAKE_WEBHOOK_SECRET",
    "local-webhook-secret",
)


def verify_signature(body: bytes, signature: str) -> bool:
    expected = hmac.new(
        WEBHOOK_SECRET.encode(),
        body,
        hashlib.sha256,
    ).hexdigest()

    return hmac.compare_digest(
        expected,
        signature,
    )


@router.post("/social-delivery")
async def social_delivery_webhook(
    request: Request,
    x_webhook_signature: str | None = Header(
        default=None,
        alias="X-Webhook-Signature",
    ),
):
    if not x_webhook_signature:
        raise HTTPException(
            status_code=400,
            detail="Missing webhook signature",
        )

    body = await request.body()

    if not verify_signature(
        body,
        x_webhook_signature,
    ):
        raise HTTPException(
            status_code=400,
            detail="Invalid webhook signature",
        )

    payload = await request.json()

    external_post_id = payload.get("external_post_id")

    if not external_post_id:
        raise HTTPException(
            status_code=400,
            detail="Missing external_post_id",
        )

    db: Session = SessionLocal()

    try:
        post = (
            db.query(SocialPost)
            .filter(
                SocialPost.external_post_id
                == external_post_id
            )
            .first()
        )

        if post is None:
            raise HTTPException(
                status_code=404,
                detail="Social post not found",
            )

        post.status = "PUBLISHED"
        post.published_at = datetime.now(timezone.utc)

        db.commit()

        return {
            "status": "accepted",
            "external_post_id": external_post_id,
        }

    finally:
        db.close()