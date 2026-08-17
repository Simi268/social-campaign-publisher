import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.campaign import Campaign
from app.models.social_post import SocialPost
from app.platforms.specifications import (
    get_platform_specification,
)
from app.schemas.social_post import (
    SocialPostCreate,
    SocialPostResponse,
)


router = APIRouter(
    prefix="/campaigns",
    tags=["social-posts"],
)


@router.post(
    "/{campaign_id}/posts",
    response_model=SocialPostResponse,
    status_code=201,
)
def create_social_post(
    campaign_id: int,
    payload: SocialPostCreate,
    db: Session = Depends(get_db),
):
    campaign = db.get(Campaign, campaign_id)

    if campaign is None:
        raise HTTPException(
            status_code=404,
            detail="Campaign not found",
        )

    try:
        get_platform_specification(
            payload.platform
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    platform = payload.platform.lower()

    existing = (
        db.query(SocialPost)
        .filter(
            SocialPost.campaign_id == campaign_id,
            SocialPost.platform == platform,
        )
        .first()
    )

    if existing:
        raise HTTPException(
            status_code=409,
            detail=(
                f"A social post already exists for "
                f"{platform} on this campaign"
            ),
        )

    post = SocialPost(
        campaign_id=campaign_id,
        platform=platform,
        caption=payload.caption,
        image_path=payload.image_path,
        scheduled_at=payload.scheduled_at,
        status="DRAFT",
        idempotency_key=str(uuid.uuid4()),
    )

    db.add(post)
    db.commit()
    db.refresh(post)

    return post


@router.post(
    "/posts/{post_id}/ready",
    response_model=SocialPostResponse,
)
def mark_post_ready(
    post_id: int,
    db: Session = Depends(get_db),
):
    post = db.get(SocialPost, post_id)

    if post is None:
        raise HTTPException(
            status_code=404,
            detail="Social post not found",
        )

    if post.status != "DRAFT":
        raise HTTPException(
            status_code=409,
            detail=(
                f"Social post cannot be marked READY "
                f"from status {post.status}"
            ),
        )

    if post.scheduled_at is None:
        raise HTTPException(
            status_code=400,
            detail="Social post must have a scheduled_at time",
        )

    post.status = "READY"

    db.commit()
    db.refresh(post)

    return post