"""
progress_panel.py — Download progress display with bar, speed, and ETA.

Shows a progress bar, percentage, download speed, ETA, and file size
during an active download. Hidden when no download is in progress.
"""

from __future__ import annotations

import customtkinter as ctk

from ytdlp_gui.core.downloader import DownloadStatus, ProgressData
from ytdlp_gui.utils.format_utils import format_bytes, format_eta, format_speed


class ProgressPanel(ctk.CTkFrame):
    """
    Progress panel with animated progress bar and live download stats.

    Hidden by default — shown during an active download and updated
    via the update_progress() method called from the queue poller.
    """

    ACCENT_COLOR = "#00B4D8"
    SUCCESS_COLOR = "#06D6A0"
    WARNING_COLOR = "#FFD166"
    CANCEL_COLOR = "#EF476F"
    CANCEL_HOVER = "#D63E5C"

    def __init__(self, master, on_cancel=None, **kwargs):
        super().__init__(
            master,
            fg_color=("gray92", "#1e1e2e"),
            corner_radius=12,
            **kwargs,
        )
        self.on_cancel = on_cancel
        self._build_ui()

        # Start hidden
        self.grid_remove()

    def _build_ui(self) -> None:
        """Construct the progress panel layout."""
        self.grid_columnconfigure(0, weight=1)

        # ── Section header row with cancel button ──
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", padx=16, pady=(14, 4))
        header_frame.grid_columnconfigure(0, weight=1)

        header = ctk.CTkLabel(
            header_frame,
            text="📊  Progress",
            font=ctk.CTkFont(size=15, weight="bold"),
            anchor="w",
        )
        header.grid(row=0, column=0, sticky="w")

        self.cancel_btn = ctk.CTkButton(
            header_frame,
            text="✕ Cancel",
            width=90,
            height=30,
            font=ctk.CTkFont(size=12),
            fg_color=self.CANCEL_COLOR,
            hover_color=self.CANCEL_HOVER,
            command=self._on_cancel_click,
        )
        self.cancel_btn.grid(row=0, column=1, sticky="e")

        # ── Status label (e.g., "Downloading…", "Merging…", "Complete!") ──
        self.status_label = ctk.CTkLabel(
            self,
            text="Preparing…",
            font=ctk.CTkFont(size=13),
            text_color=("gray40", "#9ca3af"),
            anchor="w",
        )
        self.status_label.grid(row=1, column=0, sticky="w", padx=16, pady=(4, 4))

        # ── Progress bar ──
        self.progress_bar = ctk.CTkProgressBar(
            self,
            height=20,
            corner_radius=10,
            progress_color=self.ACCENT_COLOR,
        )
        self.progress_bar.grid(row=2, column=0, sticky="ew", padx=16, pady=4)
        self.progress_bar.set(0)

        # ── Percentage label ──
        self.percent_label = ctk.CTkLabel(
            self,
            text="0.0%",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=self.ACCENT_COLOR,
        )
        self.percent_label.grid(row=3, column=0, sticky="w", padx=16, pady=(4, 2))

        # ── Stats row: Speed | ETA | Size ──
        stats_frame = ctk.CTkFrame(self, fg_color="transparent")
        stats_frame.grid(row=4, column=0, sticky="ew", padx=16, pady=(2, 14))
        stats_frame.grid_columnconfigure((0, 1, 2), weight=1)

        self.speed_label = ctk.CTkLabel(
            stats_frame,
            text="⚡ -- MB/s",
            font=ctk.CTkFont(size=13),
            anchor="w",
        )
        self.speed_label.grid(row=0, column=0, sticky="w")

        self.eta_label = ctk.CTkLabel(
            stats_frame,
            text="⏱ ETA: --:--",
            font=ctk.CTkFont(size=13),
            anchor="center",
        )
        self.eta_label.grid(row=0, column=1)

        self.size_label = ctk.CTkLabel(
            stats_frame,
            text="📦 0 B / 0 B",
            font=ctk.CTkFont(size=13),
            anchor="e",
        )
        self.size_label.grid(row=0, column=2, sticky="e")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def show(self) -> None:
        """Show the progress panel and reset to initial state."""
        self.grid()
        self.progress_bar.set(0)
        self.percent_label.configure(text="0.0%", text_color=self.ACCENT_COLOR)
        self.status_label.configure(text="Preparing…")
        self.speed_label.configure(text="⚡ -- MB/s")
        self.eta_label.configure(text="⏱ ETA: --:--")
        self.size_label.configure(text="📦 0 B / 0 B")
        self.cancel_btn.configure(state="normal")
        self.progress_bar.configure(progress_color=self.ACCENT_COLOR)

    def hide(self) -> None:
        """Hide the progress panel."""
        self.grid_remove()

    def update_progress(self, data: ProgressData) -> None:
        """
        Update the progress display with new data from the download thread.

        Args:
            data: A ProgressData object from the download queue.
        """
        if data.status == DownloadStatus.DOWNLOADING:
            # Update progress bar (0.0 to 1.0 range)
            bar_value = data.percent / 100.0
            self.progress_bar.set(bar_value)

            # Update labels
            self.percent_label.configure(text=f"{data.percent:.1f}%")
            self.status_label.configure(text="Downloading…")
            self.speed_label.configure(text=f"⚡ {format_speed(data.speed_bytes)}")
            self.eta_label.configure(text=f"⏱ ETA: {format_eta(data.eta_seconds)}")
            self.size_label.configure(
                text=f"📦 {format_bytes(data.downloaded_bytes)} / {format_bytes(data.total_bytes)}"
            )

        elif data.status == DownloadStatus.POSTPROCESSING:
            self.progress_bar.set(1.0)
            self.progress_bar.configure(progress_color=self.WARNING_COLOR)
            self.percent_label.configure(text="100%")
            self.status_label.configure(text="🔄 Post-processing (merging audio/video)…")
            self.speed_label.configure(text="")
            self.eta_label.configure(text="")
            self.cancel_btn.configure(state="disabled")

        elif data.status == DownloadStatus.FINISHED:
            self.progress_bar.set(1.0)
            self.progress_bar.configure(progress_color=self.SUCCESS_COLOR)
            self.percent_label.configure(text="100%", text_color=self.SUCCESS_COLOR)
            self.status_label.configure(text="✅ Download complete!")
            self.speed_label.configure(text="")
            self.eta_label.configure(text="")
            self.size_label.configure(text="")
            self.cancel_btn.configure(state="disabled")

        elif data.status == DownloadStatus.ERROR:
            self.progress_bar.configure(progress_color=self.CANCEL_COLOR)
            self.status_label.configure(text=f"❌ {data.error_message or 'Download failed'}")
            self.cancel_btn.configure(state="disabled")

    # ------------------------------------------------------------------
    # Internal callbacks
    # ------------------------------------------------------------------

    def _on_cancel_click(self) -> None:
        """Handle Cancel button click."""
        if self.on_cancel:
            self.on_cancel()
