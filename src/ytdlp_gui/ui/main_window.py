"""
main_window.py — Root window layout assembling all UI panels.

Orchestrates the interaction between InputPanel, InfoPanel,
ProgressPanel, and LogPanel. Manages the download workflow:
  Fetch Info → Select Format → Download → Complete/Error
"""

from __future__ import annotations

import queue
import logging
from typing import TYPE_CHECKING

import customtkinter as ctk

from ytdlp_gui.core.downloader import Downloader, DownloadStatus, ProgressData, check_ffmpeg
from ytdlp_gui.core.exceptions import ErrorSeverity, parse_error
from ytdlp_gui.core.metadata import VideoMetadata, fetch_metadata
from ytdlp_gui.ui.info_panel import InfoPanel
from ytdlp_gui.ui.input_panel import InputPanel
from ytdlp_gui.ui.log_panel import LogPanel
from ytdlp_gui.ui.progress_panel import ProgressPanel
from ytdlp_gui.utils.image_utils import fetch_thumbnail
from ytdlp_gui.utils.threading_utils import QueuePoller, WorkerThread

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class MainWindow(ctk.CTkFrame):
    """
    Main application frame that assembles and coordinates all panels.

    Layout (top to bottom):
      1. InputPanel   — URL, folder, cookies inputs
      2. InfoPanel    — Video metadata & format selector (hidden until fetch)
      3. ProgressPanel — Download progress (hidden until download starts)
      4. LogPanel     — Scrollable log output
    """

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)

        # Thread-safe queues
        self._progress_queue: queue.Queue[ProgressData] = queue.Queue()
        self._metadata_queue: queue.Queue = queue.Queue()

        # Download engine
        self._downloader = Downloader(self._progress_queue)

        # Queue pollers (initialized when needed)
        self._progress_poller: QueuePoller | None = None
        self._metadata_poller: QueuePoller | None = None

        # State
        self._current_metadata: VideoMetadata | None = None
        self._download_active = False

        self._build_ui()
        self._check_ffmpeg()

    def _build_ui(self) -> None:
        """Construct the main layout with all panels."""
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)  # Log panel expands

        # ── 1. Input Panel ──
        self.input_panel = InputPanel(
            self,
            on_fetch=self._handle_fetch,
        )
        self.input_panel.grid(row=0, column=0, sticky="ew", padx=16, pady=(16, 8))

        # ── 2. Info Panel (hidden by default) ──
        self.info_panel = InfoPanel(
            self,
            on_download=self._handle_download,
        )
        self.info_panel.grid(row=1, column=0, sticky="ew", padx=16, pady=8)

        # ── 3. Progress Panel (hidden by default) ──
        self.progress_panel = ProgressPanel(
            self,
            on_cancel=self._handle_cancel,
        )
        self.progress_panel.grid(row=2, column=0, sticky="ew", padx=16, pady=8)

        # ── 4. Log Panel ──
        self.log_panel = LogPanel(self)
        self.log_panel.grid(row=3, column=0, sticky="nsew", padx=16, pady=(8, 16))

    def _check_ffmpeg(self) -> None:
        """Check if FFmpeg is available and log a warning if not."""
        if check_ffmpeg():
            self.log_panel.log_info("FFmpeg detected ✓")
        else:
            self.log_panel.log_warning(
                "FFmpeg not found on PATH! Some formats require FFmpeg for "
                "merging video+audio. Install it from https://ffmpeg.org and "
                "add it to your system PATH."
            )

    # ==================================================================
    # FETCH INFO WORKFLOW
    # ==================================================================

    def _handle_fetch(self) -> None:
        """
        Handle "Fetch Info" button click.

        Validates the URL, starts a background thread to fetch metadata,
        and sets up a poller to receive the result.
        """
        url = self.input_panel.get_url()

        # Validate URL
        if not url:
            self.log_panel.log_warning("Please enter a video URL.")
            return

        if not url.startswith(("http://", "https://")):
            self.log_panel.log_warning("Invalid URL — must start with http:// or https://")
            return

        # Reset previous info
        self.info_panel.reset()
        self.progress_panel.hide()

        # Update UI state
        self.input_panel.set_fetching_state(True)
        self.log_panel.log_info(f"Fetching info for: {url}")

        # Start metadata fetch in background thread
        cookies = self.input_panel.get_cookies_path()
        worker = WorkerThread(
            target=self._fetch_metadata_task,
            args=(url, cookies),
            result_queue=self._metadata_queue,
            name="MetadataFetcher",
        )
        worker.start()

        # Start polling for results
        if self._metadata_poller:
            self._metadata_poller.stop()

        self._metadata_poller = QueuePoller(
            root=self.winfo_toplevel(),
            data_queue=self._metadata_queue,
            callback=self._on_metadata_result,
            interval_ms=100,
        )
        self._metadata_poller.start()

    def _fetch_metadata_task(self, url: str, cookies_path: str | None) -> tuple:
        """
        Background task: fetch metadata and thumbnail.

        Returns:
            (metadata, thumbnail_image) tuple.
        """
        metadata = fetch_metadata(url, cookies_path)

        # Also fetch the thumbnail image
        thumbnail = None
        if metadata.thumbnail_url:
            thumbnail = fetch_thumbnail(metadata.thumbnail_url)

        return metadata, thumbnail

    def _on_metadata_result(self, result: tuple) -> None:
        """Handle the metadata fetch result from the worker thread."""
        self.input_panel.set_fetching_state(False)

        if self._metadata_poller:
            self._metadata_poller.stop()

        status, data = result

        if status == "success":
            metadata, thumbnail = data
            self._current_metadata = metadata

            # Populate the info panel
            self.info_panel.populate(metadata, thumbnail)

            # Log success
            self.log_panel.log_success(f"Fetched: {metadata.title}")
            if metadata.formats:
                self.log_panel.log_info(f"Found {len(metadata.formats)} available formats")

        elif status == "error":
            exc = data
            parsed = parse_error(exc)
            self.log_panel.log_error(str(parsed))

    # ==================================================================
    # DOWNLOAD WORKFLOW
    # ==================================================================

    def _handle_download(self, format_spec: str) -> None:
        """
        Handle "Download" button click from the info panel.

        Validates the output folder, starts the download in a background
        thread, and sets up a progress poller.
        """
        # Validate output folder
        output_dir = self.input_panel.get_folder()
        if not output_dir:
            self.log_panel.log_warning("Please select a download folder.")
            return

        url = self.input_panel.get_url()
        cookies = self.input_panel.get_cookies_path()

        # Update UI state
        self._download_active = True
        self.input_panel.set_downloading_state(True)
        self.info_panel.set_downloading_state(True)
        self.progress_panel.show()
        self.log_panel.log_info(f"Starting download (format: {format_spec})…")

        # Create fresh downloader with a fresh queue
        self._progress_queue = queue.Queue()
        self._downloader = Downloader(self._progress_queue)

        # Start download in background thread
        worker = WorkerThread(
            target=self._downloader.download,
            args=(url, format_spec, output_dir, cookies),
            name="DownloadWorker",
        )
        worker.start()

        # Start progress poller
        if self._progress_poller:
            self._progress_poller.stop()

        self._progress_poller = QueuePoller(
            root=self.winfo_toplevel(),
            data_queue=self._progress_queue,
            callback=self._on_progress_update,
            interval_ms=100,
        )
        self._progress_poller.start()

    def _on_progress_update(self, data: ProgressData) -> None:
        """Handle progress updates from the download thread."""
        self.progress_panel.update_progress(data)

        if data.status == DownloadStatus.FINISHED:
            self._on_download_complete()

        elif data.status == DownloadStatus.ERROR:
            self._on_download_error(data.error_message)

        elif data.status == DownloadStatus.POSTPROCESSING:
            self.log_panel.log_info("Post-processing: merging audio and video…")

    def _on_download_complete(self) -> None:
        """Handle successful download completion."""
        self._download_active = False
        self.input_panel.set_downloading_state(False)
        self.info_panel.set_downloading_state(False)
        self.log_panel.log_success("Download complete! ✅")

        if self._progress_poller:
            self._progress_poller.stop()

    def _on_download_error(self, error_message: str | None) -> None:
        """Handle download failure."""
        self._download_active = False
        self.input_panel.set_downloading_state(False)
        self.info_panel.set_downloading_state(False)
        self.log_panel.log_error(error_message or "Download failed.")

        if self._progress_poller:
            self._progress_poller.stop()

    def _handle_cancel(self) -> None:
        """Handle Cancel button click during download."""
        if self._download_active:
            self._downloader.cancel()
            self.log_panel.log_warning("Cancelling download…")
