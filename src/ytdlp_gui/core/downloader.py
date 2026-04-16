"""
downloader.py — Download engine wrapping yt-dlp with progress hooks.

Manages the yt-dlp download lifecycle: configuring options, registering
progress hooks, and pushing real-time progress data to a thread-safe
queue for the UI to consume.
"""

from __future__ import annotations

import logging
import os
import queue
import shutil
from dataclasses import dataclass
from enum import Enum
from typing import Any

import yt_dlp

from ytdlp_gui.core.exceptions import parse_error

logger = logging.getLogger(__name__)


class DownloadStatus(Enum):
    """Status codes sent through the progress queue."""
    DOWNLOADING = "downloading"
    FINISHED = "finished"
    ERROR = "error"
    POSTPROCESSING = "postprocessing"


@dataclass
class ProgressData:
    """Structured progress update sent from download thread → UI."""
    status: DownloadStatus
    percent: float = 0.0          # 0.0 – 100.0
    speed_bytes: float = 0.0      # bytes per second
    eta_seconds: int | None = None
    downloaded_bytes: int = 0
    total_bytes: int = 0
    filename: str = ""
    error_message: str | None = None


def check_ffmpeg() -> bool:
    """
    Check if FFmpeg is available on the system PATH.

    Returns:
        True if ffmpeg is found, False otherwise.
    """
    return shutil.which("ffmpeg") is not None


class Downloader:
    """
    High-level download manager for yt-dlp.

    Uses progress_hooks to push real-time download data to a queue.Queue,
    which the UI thread polls via .after() to update the progress bar.
    """

    def __init__(self, progress_queue: queue.Queue[ProgressData]):
        """
        Initialize the downloader.

        Args:
            progress_queue: Thread-safe queue for sending progress updates to the UI.
        """
        self._queue = progress_queue
        self._cancelled = False

    def cancel(self) -> None:
        """Signal the downloader to stop at the next progress hook call."""
        self._cancelled = True

    def download(
        self,
        url: str,
        format_spec: str,
        output_dir: str,
        cookies_path: str | None = None,
    ) -> None:
        """
        Download a video/audio from the given URL.

        This method is designed to be called from a worker thread.
        Progress updates are pushed to self._queue.

        Args:
            url: The video URL to download.
            format_spec: yt-dlp format string (e.g. "bestvideo+bestaudio/best" or a format_id).
            output_dir: Directory to save the downloaded file.
            cookies_path: Optional path to a cookies.txt file.

        Raises:
            Exception: On download failure (also pushed to the queue as an error).
        """
        self._cancelled = False

        # Build yt-dlp options
        ydl_opts: dict[str, Any] = {
            "format": format_spec,
            "outtmpl": os.path.join(output_dir, "%(title)s.%(ext)s"),
            "progress_hooks": [self._on_progress],
            "postprocessor_hooks": [self._on_postprocess],
            "quiet": True,
            "no_warnings": False,
            # Merge best video + best audio when using format selectors
            "merge_output_format": "mp4",
        }

        if cookies_path:
            ydl_opts["cookiefile"] = cookies_path

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                logger.info("Starting download: %s (format=%s)", url, format_spec)
                ydl.download([url])

        except Exception as exc:
            if self._cancelled:
                # User cancelled — don't treat as error
                logger.info("Download cancelled by user.")
                self._queue.put(ProgressData(
                    status=DownloadStatus.ERROR,
                    error_message="Download cancelled.",
                ))
                return

            parsed = parse_error(exc)
            logger.error("Download failed: %s", parsed)
            self._queue.put(ProgressData(
                status=DownloadStatus.ERROR,
                error_message=str(parsed),
            ))
            raise

    # ------------------------------------------------------------------
    # Progress hook callbacks (called by yt-dlp from the download thread)
    # ------------------------------------------------------------------

    def _on_progress(self, data: dict[str, Any]) -> None:
        """
        yt-dlp progress hook — called frequently during download.

        Converts the raw progress dict into a ProgressData and pushes
        it onto the queue. Also checks for cancellation.
        """
        if self._cancelled:
            raise yt_dlp.utils.DownloadCancelled("User cancelled the download.")

        status_str = data.get("status", "")

        if status_str == "downloading":
            downloaded = data.get("downloaded_bytes", 0)
            total = data.get("total_bytes") or data.get("total_bytes_estimate") or 0

            # Calculate percentage
            percent = 0.0
            if total > 0:
                percent = min((downloaded / total) * 100, 100.0)

            self._queue.put(ProgressData(
                status=DownloadStatus.DOWNLOADING,
                percent=percent,
                speed_bytes=data.get("speed") or 0.0,
                eta_seconds=data.get("eta"),
                downloaded_bytes=downloaded,
                total_bytes=total,
                filename=data.get("filename", ""),
            ))

        elif status_str == "finished":
            self._queue.put(ProgressData(
                status=DownloadStatus.FINISHED,
                percent=100.0,
                filename=data.get("filename", ""),
            ))

        elif status_str == "error":
            self._queue.put(ProgressData(
                status=DownloadStatus.ERROR,
                error_message=data.get("error", "Unknown download error."),
            ))

    def _on_postprocess(self, data: dict[str, Any]) -> None:
        """yt-dlp postprocessor hook — called during merging/conversion."""
        status_str = data.get("status", "")
        if status_str == "started":
            self._queue.put(ProgressData(
                status=DownloadStatus.POSTPROCESSING,
                percent=100.0,
                filename=data.get("filename", ""),
            ))
