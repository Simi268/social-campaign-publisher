from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def create_campaign(title: str):
    response = client.post(
        "/campaigns",
        json={"title": title},
    )
    assert response.status_code == 201
    return response.json()["id"]


def test_create_instagram_post():
    campaign_id = create_campaign(
        "Instagram Campaign"
    )

    response = client.post(
        f"/campaigns/{campaign_id}/posts",
        json={
            "platform": "instagram",
            "caption": "Launch day!",
            "image_path": "images/launch.jpg",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["campaign_id"] == campaign_id
    assert data["platform"] == "instagram"
    assert data["status"] == "DRAFT"
    assert data["idempotency_key"]


def test_create_x_post():
    campaign_id = create_campaign(
        "X Campaign"
    )

    response = client.post(
        f"/campaigns/{campaign_id}/posts",
        json={
            "platform": "x",
            "caption": "Hello from our campaign!",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["platform"] == "x"
    assert data["status"] == "DRAFT"


def test_unsupported_platform():
    campaign_id = create_campaign(
        "Invalid Platform Campaign"
    )

    response = client.post(
        f"/campaigns/{campaign_id}/posts",
        json={
            "platform": "facebook",
            "caption": "This should fail",
        },
    )

    assert response.status_code == 400
    assert "Unsupported platform" in response.json()["detail"]


def test_duplicate_platform_post():
    campaign_id = create_campaign(
        "Duplicate Platform Campaign"
    )

    payload = {
        "platform": "instagram",
        "caption": "First post",
    }

    first = client.post(
        f"/campaigns/{campaign_id}/posts",
        json=payload,
    )

    assert first.status_code == 201

    second = client.post(
        f"/campaigns/{campaign_id}/posts",
        json=payload,
    )

    assert second.status_code == 409


def test_missing_campaign():
    response = client.post(
        "/campaigns/99999999/posts",
        json={
            "platform": "instagram",
            "caption": "Missing campaign",
        },
    )

    assert response.status_code == 404