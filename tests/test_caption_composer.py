import pytest

from app.content.caption_composer import compose_caption


CONTENT = "AI is changing how teams build software."


def test_instagram_caption_is_platform_specific():
    caption = compose_caption(CONTENT, "instagram")

    assert CONTENT in caption
    assert "save this post" in caption


def test_x_caption_is_platform_specific():
    caption = compose_caption(CONTENT, "x")

    assert CONTENT in caption
    assert "key takeaway" in caption


def test_platform_captions_are_different():
    instagram = compose_caption(CONTENT, "instagram")
    x = compose_caption(CONTENT, "x")

    assert instagram != x


def test_empty_content_is_rejected():
    with pytest.raises(ValueError):
        compose_caption("", "instagram")