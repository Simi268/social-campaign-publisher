from app.platforms.specifications import get_platform_specification


def test_instagram_specification():
    spec = get_platform_specification("instagram")

    assert spec.width == 1080
    assert spec.height == 1080
    assert spec.aspect_ratio == "1:1"


def test_x_specification():
    spec = get_platform_specification("x")

    assert spec.width == 1600
    assert spec.height == 900
    assert spec.aspect_ratio == "16:9"


def test_platform_lookup_is_case_insensitive():
    assert get_platform_specification("Instagram").name == "instagram"