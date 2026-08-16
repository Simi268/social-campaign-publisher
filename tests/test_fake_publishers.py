from app.adapters.base import PublishRequest
from app.adapters.instagram import FakeInstagramPublisher
from app.adapters.x_platform import FakeXPublisher


def test_instagram_publisher():
    publisher = FakeInstagramPublisher(
        access_token="fake-access-token"
    )

    request = PublishRequest(
        caption="Instagram test",
        image_path="instagram.jpg",
        idempotency_key="test-adapter-instagram-001",
    )

    result = publisher.publish(request)

    assert result.external_post_id.startswith("instagram-")
    assert result.status == "queued"


def test_x_publisher():
    publisher = FakeXPublisher(
        access_token="fake-access-token"
    )

    request = PublishRequest(
        caption="X test",
        image_path="x.jpg",
        idempotency_key="test-adapter-x-001",
    )

    result = publisher.publish(request)

    assert result.external_post_id.startswith("x-")
    assert result.status == "queued"


def test_idempotent_publish():
    publisher = FakeInstagramPublisher(
        access_token="fake-access-token"
    )

    request = PublishRequest(
        caption="Duplicate test",
        image_path="instagram.jpg",
        idempotency_key="test-idempotency-001",
    )

    first = publisher.publish(request)
    second = publisher.publish(request)

    assert first.external_post_id == second.external_post_id