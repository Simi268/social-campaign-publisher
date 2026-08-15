import pytest

from app.adapters.base import (
    PublishRequest,
    PublishResult,
    SocialPublisher,
)


def test_publish_request():
    request = PublishRequest(
        caption="Hello world",
        image_path="images/test.png",
        idempotency_key="campaign-1-instagram",
    )

    assert request.caption == "Hello world"
    assert request.idempotency_key == "campaign-1-instagram"


def test_publish_result():
    result = PublishResult(
        external_post_id="fake-post-123",
        status="queued",
    )

    assert result.external_post_id == "fake-post-123"
    assert result.status == "queued"


def test_social_publisher_is_abstract():
    with pytest.raises(TypeError):
        SocialPublisher()