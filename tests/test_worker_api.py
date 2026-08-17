from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_publish_due_worker_endpoint():
    response = client.post(
        "/worker/publish-due"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "completed"
    assert "published_count" in data
    assert "posts" in data
    assert isinstance(data["posts"], list)