"""
metadata.py — Fetch video metadata from a URL using yt-dlp.

Extracts title, thumbnail URL, duration, and available formats
without downloading the actual video. Designed to run in a background
thread to keep the UI responsive.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

import yt_dlp

from ytdlp_gui.core.exceptions import parse_error

logger = logging.getLogger(__name__)


@dataclass
class FormatInfo:
    """Represents a single downloadable format option."""
    format_id: str
    extension: str
    resolution: str          # e.g. "1920x1080" or "audio only"
    filesize: int | None     # bytes, may be None
    vcodec: str              # "none" for audio-only
    acodec: str              # "none" for video-only
    fps: int | None
    tbr: float | None        # total bitrate in kbps
    format_note: str         # yt-dlp's human label, e.g. "1080p"

    @property
    def is_video(self) -> bool:
        """True if this format contains a video stream."""
        return self.vcodec != "none" and self.vcodec is not None

    @property
    def is_audio(self) -> bool:
        """True if this format contains an audio stream."""
        return self.acodec != "none" and self.acodec is not None

    @property
    def display_label(self) -> str:
        """Human-readable label for the format selector dropdown."""
        parts: list[str] = []

        # Resolution or "Audio Only"
        if self.is_video:
            parts.append(self.format_note or self.resolution)
        else:
            parts.append("🎵 Audio Only")

        # Extension
        parts.append(self.extension.upper())

        # Codec info
        if self.is_video and self.is_audio:
            parts.append("(Video+Audio)")
        elif self.is_video:
            parts.append("(Video Only)")

        # Filesize
        if self.filesize:
            size_mb = self.filesize / (1024 * 1024)
            if size_mb >= 1024:
                parts.append(f"~{size_mb / 1024:.1f} GB")
            else:
                parts.append(f"~{size_mb:.0f} MB")

        # FPS for video
        if self.is_video and self.fps:
            parts.append(f"{self.fps}fps")

        return " · ".join(parts)


@dataclass
class VideoMetadata:
    """Complete metadata for a fetched video."""
    title: str
    thumbnail_url: str | None
    duration: int | None          # seconds
    uploader: str | None
    formats: list[FormatInfo] = field(default_factory=list)

    # Pre-built "best" combo options that yt-dlp merges automatically
    best_options: list[tuple[str, str]] = field(default_factory=list)


def _build_best_options() -> list[tuple[str, str]]:
    """
    Return pre-defined 'smart' format selectors that yt-dlp handles
    automatically (merging best video + best audio with FFmpeg).

    Returns:
        List of (display_label, yt-dlp format string) tuples.
    """
    return [
        ("🏆 Best Quality (Video+Audio)", "bestvideo+bestaudio/best"),
        ("📺 Best 1080p (Video+Audio)", "bestvideo[height<=1080]+bestaudio/best[height<=1080]"),
        ("📺 Best 720p (Video+Audio)", "bestvideo[height<=720]+bestaudio/best[height<=720]"),
        ("📺 Best 480p (Video+Audio)", "bestvideo[height<=480]+bestaudio/best[height<=480]"),
        ("🎵 Best Audio Only (M4A)", "bestaudio[ext=m4a]/bestaudio"),
        ("🎵 Best Audio Only (Any)", "bestaudio/best"),
    ]


def fetch_metadata(url: str, cookies_path: str | None = None) -> VideoMetadata:
    """
    Fetch video metadata from a URL without downloading.

    Args:
        url: The video URL to extract info from.
        cookies_path: Optional path to a cookies.txt file.

    Returns:
        A VideoMetadata object with title, thumbnail, formats, etc.

    Raises:
        Exception: Re-raises yt-dlp errors after logging.
    """
    ydl_opts: dict = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        # Don't extract flat playlist info, just the single video
        "extract_flat": False,
    }

    if cookies_path:
        ydl_opts["cookiefile"] = cookies_path

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

            if info is None:
                raise ValueError("yt-dlp returned no info for this URL.")

            # Parse available formats
            raw_formats = info.get("formats", [])
            formats: list[FormatInfo] = []

            for fmt in raw_formats:
                # Skip storyboard / manifest-only formats
                if fmt.get("vcodec") == "none" and fmt.get("acodec") == "none":
                    continue

                formats.append(FormatInfo(
                    format_id=fmt.get("format_id", "unknown"),
                    extension=fmt.get("ext", "?"),
                    resolution=fmt.get("resolution", "N/A"),
                    filesize=fmt.get("filesize") or fmt.get("filesize_approx"),
                    vcodec=fmt.get("vcodec", "none"),
                    acodec=fmt.get("acodec", "none"),
                    fps=fmt.get("fps"),
                    tbr=fmt.get("tbr"),
                    format_note=fmt.get("format_note", ""),
                ))

            # Sort: video+audio first, then by resolution descending
            formats.sort(
                key=lambda f: (
                    not (f.is_video and f.is_audio),  # combined first
                    not f.is_video,                     # video before audio-only
                    -(f.tbr or 0),                      # higher bitrate first
                ),
            )

            return VideoMetadata(
                title=info.get("title", "Unknown Title"),
                thumbnail_url=info.get("thumbnail"),
                duration=info.get("duration"),
                uploader=info.get("uploader"),
                formats=formats,
                best_options=_build_best_options(),
            )

    except Exception as exc:
        parsed = parse_error(exc)
        logger.error("Metadata fetch failed: %s", parsed)
        raise
