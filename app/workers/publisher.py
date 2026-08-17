from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.adapters.base import PublishRequest, PublishResult
from app.adapters.instagram import FakeInstagramPublisher
from app.adapters.x_platform import FakeXPublisher
from app.models.social_post import SocialPost
from app.services.credentials import CredentialService

from datetime import datetime, timedelta, timezone

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
        if post.external_post_id:
            raise ValueError(
                "Social post has already been published"
            )

        try:
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
            post.error_message = None

            db.commit()
            db.refresh(post)

            return result

        except Exception as exc:
            post.status = "FAILED"
            post.error_message = str(exc)

            db.commit()
            db.refresh(post)

            raise

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

    def claim_due_posts(
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
            .with_for_update(skip_locked=True)
        )

        posts = list(db.scalars(statement).all())

        # Mark claimed posts as PUBLISHING while the
        # row locks are still held.
        for post in posts:
            post.status = "PUBLISHING"

        db.commit()

        return posts

    def recover_stale_publishing(
        self,
        db: Session,
        timeout_minutes: int = 15,
    ) -> list[SocialPost]:
        cutoff = (
            datetime.now(timezone.utc)
            - timedelta(minutes=timeout_minutes)
        )

        statement = (
            select(SocialPost)
            .where(
                SocialPost.status == "PUBLISHING",
                SocialPost.updated_at < cutoff,
                SocialPost.external_post_id.is_(None),
            )
        )

        posts = list(db.scalars(statement).all())

        for post in posts:
            post.status = "READY"
            post.error_message = None

        if posts:
            db.commit()

            for post in posts:
                db.refresh(post)

        return posts

    def publish_due_posts(
        self,
        db: Session,
        campaign_id: int | None = None,
        limit: int = 10,
    ) -> list[PublishResult]:
        self.recover_stale_publishing(
            db,
        )

        posts = self.claim_due_posts(
            db,
            campaign_id=campaign_id,
            limit=limit,
        )

        results = []

        for post in posts:
            # publish_post expects a post that has not already
            # been published. PUBLISHING is intentionally allowed.
            result = self.publish_post(
                db,
                post,
            )

            results.append(result)

        return results