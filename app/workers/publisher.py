from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.adapters.base import PublishRequest, PublishResult
from app.adapters.instagram import FakeInstagramPublisher
from app.adapters.x_platform import FakeXPublisher
from app.models.social_post import SocialPost
from app.services.credentials import CredentialService


PUBLISHERS = {
    "instagram": FakeInstagramPublisher,
    "x": FakeXPublisher,
}


class PublisherWorker:
    def __init__(
        self,
        credential_service: CredentialService | None = None,
    ):
        self.credential_service = (
            credential_service or CredentialService()
        )

    def publish_post(
        self,
        db: Session,
        post: SocialPost,
    ) -> PublishResult:
        # Idempotency guard:
        # Never publish a post that already has an
        # external platform ID.
        if post.external_post_id:
            raise ValueError(
                "Social post has already been published"
            )

        platform = post.platform.lower()

        publisher_class = PUBLISHERS.get(platform)

        if publisher_class is None:
            raise ValueError(
                f"Unsupported platform: {post.platform}"
            )

        access_token = self.credential_service.get_token(
            db,
            platform,
        )

        publisher = publisher_class(
            access_token=access_token,
        )

        request = PublishRequest(
            caption=post.caption,
            image_path=post.image_path or "",
            idempotency_key=post.idempotency_key,
        )

        result = publisher.publish(request)

        post.external_post_id = result.external_post_id
        post.status = result.status.upper()

        db.commit()
        db.refresh(post)

        return result

    def get_due_posts(
        self,
        db: Session,
        campaign_id: int | None = None,
        limit: int = 10,
    ) -> list[SocialPost]:
        now = datetime.now(timezone.utc)

        conditions = [
            SocialPost.status == "READY",
            SocialPost.scheduled_at.is_not(None),
            SocialPost.scheduled_at <= now,
            SocialPost.external_post_id.is_(None),
        ]

        if campaign_id is not None:
            conditions.append(
                SocialPost.campaign_id == campaign_id
            )

        statement = (
            select(SocialPost)
            .where(*conditions)
            .order_by(SocialPost.scheduled_at.asc())
            .limit(limit)
        )

        return list(db.scalars(statement).all())

    def publish_due_posts(
        self,
        db: Session,
        campaign_id: int | None = None,
        limit: int = 10,
    ) -> list[PublishResult]:
        posts = self.get_due_posts(
            db,
            campaign_id=campaign_id,
            limit=limit,
        )

        results = []

        for post in posts:
            result = self.publish_post(
                db,
                post,
            )
            results.append(result)

        return results