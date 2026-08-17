from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from app.core.database import SessionLocal
from app.main import app
from app.models.social_post import SocialPost
from app.services.credentials import CredentialService


client = TestClient(app)


def create_campaign(title: str):
    response = client.post(
        "/campaigns",
        json={"title": title},
    )

    assert response.status_code == 201

    return response.json()["id"]


def create_post(
    campaign_id: int,
    platform: str = "instagram",
):
    response = client.post(
        f"/campaigns/{campaign_id}/posts",
        json={
            "platform": platform,
            "caption": "Campaign publish test",
            "image_path": "images/test.jpg",
        },
    )

    assert response.status_code == 201

    return response.json()["id"]


def create_test_credential(
    platform: str = "instagram",
):
    db = SessionLocal()

    try:
        service = CredentialService()

        service.save_token(
            db,
            platform,
            "fake-access-token",
        )

    finally:
        db.close()


def make_post_ready(post_id: int):
    db = SessionLocal()

    try:
        post = db.get(
            SocialPost,
            post_id,
        )

        assert post is not None

        post.status = "READY"
        post.scheduled_at = (
            datetime.now(timezone.utc)
            - timedelta(minutes=5)
        )

        db.commit()

    finally:
        db.close()


def test_publish_campaign_publishes_due_post():
    campaign_id = create_campaign(
        "Publish Campaign"
    )

    post_id = create_post(
        campaign_id,
    )

    make_post_ready(post_id)

    create_test_credential(
        "instagram",
    )

    response = client.post(
        f"/campaigns/{campaign_id}/publish"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["campaign_id"] == campaign_id
    assert data["status"] == "PUBLISHED"
    assert data["published_count"] == 1
    assert len(data["posts"]) == 1
    assert data["posts"][0]["external_post_id"]
    assert data["posts"][0]["status"] == "queued"


def test_publish_campaign_does_not_publish_other_campaign():
    campaign_one = create_campaign(
        "Campaign One"
    )

    campaign_two = create_campaign(
        "Campaign Two"
    )

    post_one = create_post(
        campaign_one,
    )

    post_two = create_post(
        campaign_two,
    )

    make_post_ready(post_one)
    make_post_ready(post_two)

    create_test_credential(
        "instagram",
    )

    response = client.post(
        f"/campaigns/{campaign_one}/publish"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["campaign_id"] == campaign_one
    assert data["published_count"] == 1

    db = SessionLocal()

    try:
        other_post = db.get(
            SocialPost,
            post_two,
        )

        assert other_post is not None
        assert other_post.external_post_id is None
        assert other_post.status == "READY"

    finally:
        db.close()


def test_publish_missing_campaign():
    response = client.post(
        "/campaigns/99999999/publish"
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Campaign not found"


def test_publish_campaign_with_no_due_posts():
    campaign_id = create_campaign(
        "Future Campaign"
    )

    post_id = create_post(
        campaign_id,
    )

    db = SessionLocal()

    try:
        post = db.get(
            SocialPost,
            post_id,
        )

        assert post is not None

        post.status = "READY"
        post.scheduled_at = (
            datetime.now(timezone.utc)
            + timedelta(hours=1)
        )

        db.commit()

    finally:
        db.close()

    response = client.post(
        f"/campaigns/{campaign_id}/publish"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["campaign_id"] == campaign_id
    assert data["status"] == "SCHEDULED"
    assert data["published_count"] == 0
    assert data["posts"] == []