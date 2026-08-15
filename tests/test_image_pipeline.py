from pathlib import Path

from PIL import Image

from app.content.image_pipeline import create_image_variant


def create_test_image(path: Path) -> None:
    image = Image.new("RGB", (2000, 1200), "white")
    image.save(path)


def test_instagram_image_dimensions(tmp_path):
    source = tmp_path / "source.jpg"
    create_test_image(source)

    output = create_image_variant(
        source,
        "instagram",
        tmp_path / "output",
    )

    with Image.open(output) as image:
        assert image.size == (1080, 1080)


def test_x_image_dimensions(tmp_path):
    source = tmp_path / "source.jpg"
    create_test_image(source)

    output = create_image_variant(
        source,
        "x",
        tmp_path / "output",
    )

    with Image.open(output) as image:
        assert image.size == (1600, 900)


def test_missing_source_image_raises_error(tmp_path):
    missing = tmp_path / "missing.jpg"

    try:
        create_image_variant(
            missing,
            "instagram",
            tmp_path / "output",
        )
        assert False
    except FileNotFoundError:
        assert True