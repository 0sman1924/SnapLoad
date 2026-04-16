"""
image_utils.py — Thumbnail fetching and image processing.

Downloads thumbnail images from URLs, resizes them with Pillow,
and converts them to CTkImage objects for display in the info panel.
"""

from __future__ import annotations

import io
import logging
from typing import TYPE_CHECKING

import requests
from PIL import Image

if TYPE_CHECKING:
    import customtkinter as ctk

logger = logging.getLogger(__name__)

# Default thumbnail dimensions (16:9 aspect ratio)
DEFAULT_THUMB_WIDTH = 320
DEFAULT_THUMB_HEIGHT = 180


def fetch_thumbnail(
    url: str,
    width: int = DEFAULT_THUMB_WIDTH,
    height: int = DEFAULT_THUMB_HEIGHT,
    timeout: int = 10,
) -> Image.Image | None:
    """
    Download a thumbnail image from a URL and resize it.

    Args:
        url: The thumbnail image URL.
        width: Target width in pixels.
        height: Target height in pixels.
        timeout: HTTP request timeout in seconds.

    Returns:
        A Pillow Image object resized to the target dimensions,
        or None if the fetch fails.
    """
    if not url:
        return None

    try:
        response = requests.get(url, timeout=timeout, stream=True)
        response.raise_for_status()

        image = Image.open(io.BytesIO(response.content))

        # Convert to RGB if necessary (some thumbnails are RGBA or palette)
        if image.mode not in ("RGB", "RGBA"):
            image = image.convert("RGB")

        # Resize with high-quality resampling, maintaining aspect ratio
        image = image.resize((width, height), Image.Resampling.LANCZOS)

        return image

    except requests.RequestException as exc:
        logger.warning("Failed to fetch thumbnail from %s: %s", url, exc)
        return None
    except (OSError, Image.DecompressionBombError) as exc:
        logger.warning("Failed to process thumbnail image: %s", exc)
        return None


def create_placeholder(
    width: int = DEFAULT_THUMB_WIDTH,
    height: int = DEFAULT_THUMB_HEIGHT,
) -> Image.Image:
    """
    Create a dark placeholder image for when no thumbnail is available.

    Args:
        width: Image width in pixels.
        height: Image height in pixels.

    Returns:
        A solid dark-gray Pillow Image.
    """
    return Image.new("RGB", (width, height), color=(30, 30, 40))


def pil_to_ctk_image(
    image: Image.Image,
    size: tuple[int, int] | None = None,
) -> "ctk.CTkImage":
    """
    Convert a Pillow Image to a CTkImage for display in CustomTkinter.

    Args:
        image: The Pillow Image to convert.
        size: Optional (width, height) tuple. Defaults to the image's own size.

    Returns:
        A CTkImage that can be used in CTkLabel or CTkButton widgets.
    """
    import customtkinter as ctk

    if size is None:
        size = image.size

    return ctk.CTkImage(
        light_image=image,
        dark_image=image,
        size=size,
    )
