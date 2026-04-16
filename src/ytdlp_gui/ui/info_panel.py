"""
info_panel.py — Video metadata display and format selector.

Shows the video thumbnail, title, uploader, duration, and a dropdown
to select the desired download format. Appears after the user clicks
"Fetch Info" and metadata is successfully retrieved.
"""

from __future__ import annotations

from typing import Callable

import customtkinter as ctk
from PIL import Image

from ytdlp_gui.core.metadata import VideoMetadata
from ytdlp_gui.utils.format_utils import format_duration
from ytdlp_gui.utils.image_utils import (
    create_placeholder,
    pil_to_ctk_image,
)


class InfoPanel(ctk.CTkFrame):
    """
    Video info panel displaying thumbnail, title, and format selector.

    Hidden by default — shown when metadata is loaded via populate().
    """

    ACCENT_COLOR = "#00B4D8"
    ACCENT_HOVER = "#0096C7"
    DOWNLOAD_COLOR = "#06D6A0"
    DOWNLOAD_HOVER = "#05C090"

    def __init__(
        self,
        master,
        on_download: Callable[[str], None] | None = None,
        **kwargs,
    ):
        """
        Initialize the info panel.

        Args:
            master: Parent widget.
            on_download: Callback with the selected format spec string.
        """
        super().__init__(
            master,
            fg_color=("gray92", "#1e1e2e"),
            corner_radius=12,
            **kwargs,
        )
        self.on_download = on_download

        # State
        self._format_map: dict[str, str] = {}  # display_label → format_spec
        self._ctk_image = None  # Keep reference to prevent garbage collection

        self._build_ui()

        # Start hidden — shown when metadata is loaded
        self.grid_remove()

    def _build_ui(self) -> None:
        """Construct the info panel layout."""
        self.grid_columnconfigure(1, weight=1)

        # ── Section header ──
        header = ctk.CTkLabel(
            self,
            text="🎬  Video Info",
            font=ctk.CTkFont(size=15, weight="bold"),
            anchor="w",
        )
        header.grid(row=0, column=0, columnspan=3, sticky="w", padx=16, pady=(14, 8))

        # ── Thumbnail (left side) ──
        placeholder = create_placeholder(280, 158)
        self._ctk_image = pil_to_ctk_image(placeholder, size=(280, 158))

        self.thumbnail_label = ctk.CTkLabel(
            self,
            image=self._ctk_image,
            text="",
            corner_radius=8,
        )
        self.thumbnail_label.grid(
            row=1, column=0, rowspan=4, padx=(16, 12), pady=(4, 14), sticky="nw",
        )

        # ── Title ──
        self.title_label = ctk.CTkLabel(
            self,
            text="Video Title",
            font=ctk.CTkFont(size=16, weight="bold"),
            anchor="w",
            wraplength=400,
        )
        self.title_label.grid(row=1, column=1, columnspan=2, sticky="w", padx=4, pady=(4, 2))

        # ── Uploader & Duration row ──
        self.meta_label = ctk.CTkLabel(
            self,
            text="",
            font=ctk.CTkFont(size=12),
            text_color=("gray40", "#9ca3af"),
            anchor="w",
        )
        self.meta_label.grid(row=2, column=1, columnspan=2, sticky="w", padx=4, pady=(0, 8))

        # ── Format selector ──
        format_label = ctk.CTkLabel(
            self,
            text="Format:",
            font=ctk.CTkFont(size=13),
        )
        format_label.grid(row=3, column=1, sticky="w", padx=4, pady=4)

        self.format_combo = ctk.CTkComboBox(
            self,
            values=["Select a format…"],
            width=380,
            height=36,
            font=ctk.CTkFont(size=12),
            state="readonly",
            dropdown_font=ctk.CTkFont(size=12),
        )
        self.format_combo.grid(row=3, column=2, sticky="w", padx=(4, 16), pady=4)
        self.format_combo.set("Select a format…")

        # ── Download button ──
        self.download_btn = ctk.CTkButton(
            self,
            text="⬇  Download",
            width=180,
            height=42,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=self.DOWNLOAD_COLOR,
            hover_color=self.DOWNLOAD_HOVER,
            text_color="#1a1a2e",
            command=self._on_download_click,
            state="disabled",
        )
        self.download_btn.grid(
            row=4, column=1, columnspan=2, sticky="w", padx=4, pady=(8, 14),
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def populate(self, metadata: VideoMetadata, thumbnail: Image.Image | None = None) -> None:
        """
        Populate the panel with fetched video metadata.

        Args:
            metadata: The VideoMetadata object from the metadata fetcher.
            thumbnail: Optional pre-fetched Pillow Image for the thumbnail.
        """
        # Show the panel
        self.grid()

        # Title
        self.title_label.configure(text=metadata.title)

        # Uploader + Duration
        meta_parts: list[str] = []
        if metadata.uploader:
            meta_parts.append(f"👤 {metadata.uploader}")
        if metadata.duration:
            meta_parts.append(f"⏱ {format_duration(metadata.duration)}")
        self.meta_label.configure(text="  ·  ".join(meta_parts) if meta_parts else "")

        # Thumbnail
        if thumbnail:
            self._ctk_image = pil_to_ctk_image(thumbnail, size=(280, 158))
            self.thumbnail_label.configure(image=self._ctk_image)

        # Build format dropdown
        self._format_map.clear()
        display_options: list[str] = []

        # Add pre-built "best" options first
        for label, format_spec in metadata.best_options:
            display_options.append(label)
            self._format_map[label] = format_spec

        # Add separator
        separator = "─" * 40
        display_options.append(separator)
        self._format_map[separator] = ""

        # Add individual formats
        for fmt in metadata.formats:
            label = fmt.display_label
            # Avoid duplicate labels by appending format_id
            if label in self._format_map:
                label = f"{label} [{fmt.format_id}]"
            display_options.append(label)
            self._format_map[label] = fmt.format_id

        self.format_combo.configure(values=display_options)
        # Default to "Best Quality"
        if display_options:
            self.format_combo.set(display_options[0])

        # Enable download button
        self.download_btn.configure(state="normal")

    def get_selected_format(self) -> str | None:
        """
        Return the yt-dlp format spec for the currently selected format.

        Returns:
            The format string, or None if nothing valid is selected.
        """
        selected = self.format_combo.get()
        fmt = self._format_map.get(selected, "")
        return fmt if fmt else None

    def set_downloading_state(self, downloading: bool) -> None:
        """Toggle the download button state."""
        if downloading:
            self.download_btn.configure(text="⏳ Downloading…", state="disabled")
        else:
            self.download_btn.configure(text="⬇  Download", state="normal")

    def reset(self) -> None:
        """Hide and reset the panel to its default state."""
        self.grid_remove()
        self.title_label.configure(text="Video Title")
        self.meta_label.configure(text="")
        self.format_combo.configure(values=["Select a format…"])
        self.format_combo.set("Select a format…")
        self.download_btn.configure(state="disabled")

        placeholder = create_placeholder(280, 158)
        self._ctk_image = pil_to_ctk_image(placeholder, size=(280, 158))
        self.thumbnail_label.configure(image=self._ctk_image)

    # ------------------------------------------------------------------
    # Internal callbacks
    # ------------------------------------------------------------------

    def _on_download_click(self) -> None:
        """Handle Download button click."""
        fmt = self.get_selected_format()
        if fmt and self.on_download:
            self.on_download(fmt)
