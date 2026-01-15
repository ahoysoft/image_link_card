"""Slug generation utilities."""

from nanoid import generate


def generate_slug(size: int = 21) -> str:
    """Generate a URL-safe nanoid slug.

    Args:
        size: Length of the slug (default 21)

    Returns:
        URL-safe random string
    """
    return generate(size=size)
