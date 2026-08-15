from dataclasses import dataclass


@dataclass(frozen=True)
class PlatformSpecification:
    name: str
    width: int
    height: int
    aspect_ratio: str
    voice_rules: tuple[str, ...]


PLATFORM_SPECIFICATIONS = {
    "instagram": PlatformSpecification(
        name="instagram",
        width=1080,
        height=1080,
        aspect_ratio="1:1",
        voice_rules=(
            "Visual-first",
            "Engaging",
            "Use concise storytelling",
        ),
    ),
    "x": PlatformSpecification(
        name="x",
        width=1600,
        height=900,
        aspect_ratio="16:9",
        voice_rules=(
            "Concise",
            "Direct",
            "Conversation-oriented",
        ),
    ),
}


def get_platform_specification(platform: str) -> PlatformSpecification:
    try:
        return PLATFORM_SPECIFICATIONS[platform.lower()]
    except KeyError:
        raise ValueError(f"Unsupported platform: {platform}")