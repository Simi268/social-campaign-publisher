from app.platforms.specifications import get_platform_specification


SHARED_BRAND_VOICE = (
    "Helpful, clear, informative, and professional."
)


def compose_caption(
    content_summary: str,
    platform: str,
) -> str:
    """
    Compose a platform-specific caption from shared brand voice,
    platform rules, and the content summary.
    """

    if not content_summary.strip():
        raise ValueError("Content summary cannot be empty.")

    spec = get_platform_specification(platform)

    if spec.name == "instagram":
        return (
            f"{content_summary.strip()}\n\n"
            "Discover the story, save this post for later, "
            "and share it with someone who would find it useful."
        )

    if spec.name == "x":
        return (
            f"{content_summary.strip()} "
            "Here's what matters most — concise insights, "
            "clear context, and the key takeaway."
        )

    raise ValueError(f"Unsupported platform: {platform}")