"""
format_utils.py — Human-readable formatting helpers.

Converts raw bytes, seconds, and speed values into clean strings
for display in the UI progress panel and log panel.
"""

from __future__ import annotations


def format_bytes(num_bytes: int | float | None) -> str:
    """
    Convert a byte count into a human-readable size string.

    Examples:
        format_bytes(0)         → "0 B"
        format_bytes(1536)      → "1.5 KB"
        format_bytes(1048576)   → "1.0 MB"
        format_bytes(None)      → "N/A"
    """
    if num_bytes is None or num_bytes < 0:
        return "N/A"

    units = ["B", "KB", "MB", "GB", "TB"]
    size = float(num_bytes)

    for unit in units:
        if abs(size) < 1024.0:
            # Show decimals only for KB and above
            if unit == "B":
                return f"{int(size)} {unit}"
            return f"{size:.1f} {unit}"
        size /= 1024.0

    return f"{size:.1f} PB"


def format_speed(bytes_per_sec: float | None) -> str:
    """
    Convert download speed (bytes/s) into a readable string.

    Examples:
        format_speed(1048576)   → "1.0 MB/s"
        format_speed(512000)    → "500.0 KB/s"
        format_speed(None)      → "-- MB/s"
    """
    if bytes_per_sec is None or bytes_per_sec <= 0:
        return "-- MB/s"

    return f"{format_bytes(bytes_per_sec)}/s"


def format_eta(seconds: int | None) -> str:
    """
    Convert ETA seconds into a human-readable time string.

    Examples:
        format_eta(90)    → "01:30"
        format_eta(3661)  → "1:01:01"
        format_eta(None)  → "--:--"
    """
    if seconds is None or seconds < 0:
        return "--:--"

    hours, remainder = divmod(int(seconds), 3600)
    minutes, secs = divmod(remainder, 60)

    if hours > 0:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"


def format_duration(seconds: int | None) -> str:
    """
    Convert a video duration (seconds) into a display string.

    Examples:
        format_duration(632)   → "10:32"
        format_duration(7261)  → "2:01:01"
        format_duration(None)  → "Unknown"
    """
    if seconds is None or seconds < 0:
        return "Unknown"

    return format_eta(seconds)


def truncate_title(title: str, max_length: int = 60) -> str:
    """
    Truncate a video title for display, adding ellipsis if needed.

    Args:
        title: The full video title.
        max_length: Maximum character length before truncation.

    Returns:
        The truncated title with "…" appended if it was shortened.
    """
    if len(title) <= max_length:
        return title
    return title[: max_length - 1].rstrip() + "…"
