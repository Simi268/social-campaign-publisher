from datetime import datetime, timezone

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_create_campaign():
    response = client.post(
        "/campaigns",
        json={
            "title": "Summer Product Launch",
            "source_url": "https://example.com/product",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["title"] == "Summer Product Launch"
    assert data["source_url"] == "https://example.com/product"
    assert data["status"] == "DRAFT"
    assert data["id"] > 0


def test_create_scheduled_campaign():
    scheduled_at = "2026-09-01T10:00:00Z"

    response = client.post(
        "/campaigns",
        json={
            "title": "Scheduled Campaign",
            "scheduled_at": scheduled_at,
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["title"] == "Scheduled Campaign"
    assert data["scheduled_at"] is not None
    assert data["status"] == "DRAFT"


def test_get_campaign():
    create_response = client.post(
        "/campaigns",
        json={
            "title": "Campaign To Retrieve",
        },
    )

    campaign_id = create_response.json()["id"]

    response = client.get(
        f"/campaigns/{campaign_id}"
    )

    assert response.status_code == 200
    assert response.json()["id"] == campaign_id
    assert response.json()["title"] == "Campaign To Retrieve"


def test_get_missing_campaign():
    response = client.get("/campaigns/99999999")

    assert response.status_code == 404