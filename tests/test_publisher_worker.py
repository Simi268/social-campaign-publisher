import uuid

import pytest

from app.core.database import SessionLocal
from app.models.campaign import Campaign
from app.models.social_post import SocialPost
from app.workers.publisher import PublisherWorker
from datetime import datetime, timedelta, timezone



class FakeCredentialService:
    def get_token(self, db, platform):
        return "fake-access-token"


def create_post(platform: str, status: str = "READY"):
    db = SessionLocal()

    campaign = Campaign(
        title=f"Worker Test Campaign {uuid.uuid4()}",
    )

    db.add(campaign)
    db.commit()
    db.refresh(campaign)

    post = SocialPost(
        campaign_id=campaign.id,
        platform=platform,
        caption="Worker test post",
        image_path="test.jpg",
        status=status,
        idempotency_key=f"worker-test-{uuid.uuid4()}",
    )

    db.add(post)
    db.commit()
    db.refresh(post)

    return db, post


def test_publish_instagram_post():
    db, post = create_post("instagram")

    try:
        worker = PublisherWorker(
            credential_service=FakeCredentialService()
        )

        result = worker.publish_post(
            db,
            post,
        )

        assert result.external_post_id
        assert post.external_post_id == result.external_post_id
        assert post.status == result.status.upper()

    finally:
        db.close()


def test_already_published_post_is_rejected():
    db, post = create_post("instagram", "PUBLISHED")

    try:
        post.external_post_id = "existing-post-123"
        db.commit()

        worker = PublisherWorker(
            credential_service=FakeCredentialService()
        )

        with pytest.raises(
            ValueError,
            match="already been published",
        ):
            worker.publish_post(
                db,
                post,
            )

    finally:
        db.close()


def test_unsupported_platform_is_rejected():
    db, post = create_post("linkedin")

    try:
        worker = PublisherWorker(
            credential_service=FakeCredentialService()
        )

        with pytest.raises(
            ValueError,
            match="Unsupported platform",
        ):
            worker.publish_post(
                db,
                post,
            )

    finally:
        db.close()

def test_get_due_posts():
    db, post = create_post("instagram")

    try:
        post.scheduled_at = datetime.now(timezone.utc) - timedelta(minutes=5)
        db.commit()

        worker = PublisherWorker(
            credential_service=FakeCredentialService()
        )

        due_posts = worker.get_due_posts(
    db,
    campaign_id=post.campaign_id,
)

        assert post.id in [item.id for item in due_posts]

    finally:
        db.close()


def test_future_post_is_not_due():
    db, post = create_post("instagram")

    try:
        post.scheduled_at = datetime.now(timezone.utc) + timedelta(hours=1)
        db.commit()

        worker = PublisherWorker(
            credential_service=FakeCredentialService()
        )

        due_posts = worker.get_due_posts(db)

        assert post.id not in [item.id for item in due_posts]

    finally:
        db.close()


def test_draft_post_is_not_due():
    db, post = create_post("instagram", "DRAFT")

    try:
        post.scheduled_at = datetime.now(timezone.utc) - timedelta(minutes=5)
        db.commit()

        worker = PublisherWorker(
            credential_service=FakeCredentialService()
        )

        due_posts = worker.get_due_posts(db)

        assert post.id not in [item.id for item in due_posts]

    finally:
        db.close()


def test_already_published_post_is_not_due():
    db, post = create_post("instagram", "PUBLISHED")

    try:
        post.scheduled_at = datetime.now(timezone.utc) - timedelta(minutes=5)
        post.external_post_id = "already-published-123"
        db.commit()

        worker = PublisherWorker(
            credential_service=FakeCredentialService()
        )

        due_posts = worker.get_due_posts(db)

        assert post.id not in [item.id for item in due_posts]

    finally:
        db.close()


def test_publish_due_posts():
    db, post = create_post("instagram")

    try:
        post.scheduled_at = (
            datetime.now(timezone.utc)
            - timedelta(minutes=5)
        )
        db.commit()

        worker = PublisherWorker(
            credential_service=FakeCredentialService()
        )

        results = worker.publish_due_posts(
    db,
    campaign_id=post.campaign_id,
)

        assert len(results) >= 1

        db.refresh(post)

        assert post.external_post_id is not None
        assert post.status == "QUEUED"

    finally:
        db.close()

def test_publish_failure_marks_post_failed():
    from app.workers.publisher import PUBLISHERS

    db, post = create_post("instagram")

    try:
        worker = PublisherWorker(
            credential_service=FakeCredentialService()
        )

        class FailingPublisher:
            def __init__(self, access_token):
                pass

            def publish(self, request):
                raise RuntimeError(
                    "Fake platform unavailable"
                )

        original_publisher = PUBLISHERS["instagram"]

        PUBLISHERS["instagram"] = FailingPublisher

        try:
            with pytest.raises(
                RuntimeError,
                match="Fake platform unavailable",
            ):
                worker.publish_post(
                    db,
                    post,
                )

            db.refresh(post)

            assert post.status == "FAILED"
            assert (
                post.error_message
                == "Fake platform unavailable"
            )
            assert post.external_post_id is None

        finally:
            PUBLISHERS["instagram"] = original_publisher

    finally:
        db.close()

def test_recover_stale_publishing_post():
    db, post = create_post(
        "instagram",
        "PUBLISHING",
    )

    try:
        post.scheduled_at = (
            datetime.now(timezone.utc)
            - timedelta(minutes=30)
        )

        post.updated_at = (
            datetime.now(timezone.utc)
            - timedelta(minutes=30)
        )

        db.commit()

        worker = PublisherWorker(
            credential_service=FakeCredentialService()
        )

        recovered = worker.recover_stale_publishing(
            db,
            timeout_minutes=15,
        )

        db.refresh(post)

        assert post.id in [
            item.id for item in recovered
        ]

        assert post.status == "READY"
        assert post.error_message is None
        assert post.external_post_id is None

    finally:
        db.close()


def test_fresh_publishing_post_is_not_recovered():
    db, post = create_post(
        "instagram",
        "PUBLISHING",
    )

    try:
        post.updated_at = (
            datetime.now(timezone.utc)
            - timedelta(minutes=5)
        )

        db.commit()

        worker = PublisherWorker(
            credential_service=FakeCredentialService()
        )

        recovered = worker.recover_stale_publishing(
            db,
            timeout_minutes=15,
        )

        db.refresh(post)

        assert post.id not in [
            item.id for item in recovered
        ]

        assert post.status == "PUBLISHING"

    finally:
        db.close()

def test_stale_post_is_recovered_and_published():
    db, post = create_post(
        "instagram",
        "PUBLISHING",
    )

    try:
        post.scheduled_at = (
            datetime.now(timezone.utc)
            - timedelta(minutes=30)
        )
        post.updated_at = (
            datetime.now(timezone.utc)
            - timedelta(minutes=30)
        )
        db.commit()

        worker = PublisherWorker(
            credential_service=FakeCredentialService()
        )

        results = worker.publish_due_posts(db)

        db.refresh(post)

        assert len(results) >= 1
        assert post.status == "QUEUED"
        assert post.external_post_id is not None
        assert post.error_message is None

    finally:
        db.close()

def test_429_retry_honors_retry_after(monkeypatch):
    from app.adapters.instagram import FakeInstagramPublisher
    from app.adapters.base import PublishRequest

    class FakeResponse:
        def __init__(self, status_code, headers=None, data=None):
            self.status_code = status_code
            self.headers = headers or {}
            self._data = data

        def raise_for_status(self):
            if self.status_code >= 400:
                raise RuntimeError(
                    f"HTTP {self.status_code}"
                )

        def json(self):
            return self._data

    responses = [
        FakeResponse(
            429,
            headers={"Retry-After": "1"},
        ),
        FakeResponse(
            200,
            data={
                "external_post_id": "instagram-retry-success",
                "status": "queued",
            },
        ),
    ]

    sleep_calls = []

    def fake_post(*args, **kwargs):
        return responses.pop(0)

    def fake_sleep(seconds):
        sleep_calls.append(seconds)

    monkeypatch.setattr(
        "app.adapters.fake_base.httpx.post",
        fake_post,
    )

    monkeypatch.setattr(
        "app.adapters.fake_base.time.sleep",
        fake_sleep,
    )

    publisher = FakeInstagramPublisher(
    access_token="fake-access-token",
    max_retries=3,
)

    result = publisher.publish(
        PublishRequest(
            caption="Retry test",
            image_path="test.jpg",
            idempotency_key="retry-test-001",
        )
    )

    assert result.external_post_id == "instagram-retry-success"
    assert result.status == "queued"
    assert sleep_calls == [1]