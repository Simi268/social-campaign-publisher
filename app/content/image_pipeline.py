from pathlib import Path

from PIL import Image, ImageOps

from app.platforms.specifications import get_platform_specification


OUTPUT_DIR = Path("generated/images")


def create_image_variant(
    source_path: str | Path,
    platform: str,
    output_dir: str | Path = OUTPUT_DIR,
) -> Path:
    """
    Create a correctly-sized image variant for a supported platform.

    The image is center-cropped while preserving the source image's
    aspect ratio before being resized to the platform specification.
    """

    source_path = Path(source_path)
    output_dir = Path(output_dir)

    if not source_path.exists():
        raise FileNotFoundError(f"Source image not found: {source_path}")

    spec = get_platform_specification(platform)

    output_dir.mkdir(parents=True, exist_ok=True)

    with Image.open(source_path) as image:
        image = image.convert("RGB")

        variant = ImageOps.fit(
            image,
            (spec.width, spec.height),
            method=Image.Resampling.LANCZOS,
            centering=(0.5, 0.5),
        )

        output_path = output_dir / f"{source_path.stem}_{spec.name}.jpg"

        variant.save(
            output_path,
            format="JPEG",
            quality=90,
            optimize=True,
        )

    return output_path