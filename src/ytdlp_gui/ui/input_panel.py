"""
input_panel.py — URL, destination folder, and cookies input panel.

The top section of the app where users provide:
  - A video URL
  - A destination folder for downloads
  - An optional cookies.txt file for authenticated access
  - "Fetch Info" and "Download" action buttons
"""

from __future__ import annotations

import os
from tkinter import filedialog
from typing import Callable

import customtkinter as ctk

from ytdlp_gui.ui.components.tooltip import ToolTip


class InputPanel(ctk.CTkFrame):
    """
    Input panel containing URL, folder, cookies fields, and action buttons.

    Attributes:
        on_fetch: Callback invoked when "Fetch Info" is clicked.
        on_download: Callback invoked when "Download" is clicked.
    """

    # Color constants for the accent theme
    ACCENT_COLOR = "#00B4D8"
    ACCENT_HOVER = "#0096C7"
    SECONDARY_COLOR = "#374151"
    SECONDARY_HOVER = "#4B5563"

    def __init__(
        self,
        master,
        on_fetch: Callable[[], None] | None = None,
        on_download: Callable[[], None] | None = None,
        **kwargs,
    ):
        super().__init__(
            master,
            fg_color=("gray92", "#1e1e2e"),
            corner_radius=12,
            **kwargs,
        )
        self.on_fetch = on_fetch
        self.on_download = on_download

        # Internal state
        self._cookies_path: str | None = None

        self._build_ui()

    def _build_ui(self) -> None:
        """Construct all widgets inside the input panel."""
        self.grid_columnconfigure(1, weight=1)

        # ── Section header ──
        header = ctk.CTkLabel(
            self,
            text="📥  Input",
            font=ctk.CTkFont(size=15, weight="bold"),
            anchor="w",
        )
        header.grid(row=0, column=0, columnspan=4, sticky="w", padx=16, pady=(14, 8))

        # ── Row 1: URL ──
        url_label = ctk.CTkLabel(self, text="URL:", font=ctk.CTkFont(size=13))
        url_label.grid(row=1, column=0, sticky="w", padx=(16, 8), pady=6)

        self.url_entry = ctk.CTkEntry(
            self,
            placeholder_text="Paste video URL here…",
            height=36,
            font=ctk.CTkFont(size=13),
        )
        self.url_entry.grid(row=1, column=1, columnspan=2, sticky="ew", padx=4, pady=6)

        self.fetch_btn = ctk.CTkButton(
            self,
            text="⚡ Fetch Info",
            width=120,
            height=36,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=self.ACCENT_COLOR,
            hover_color=self.ACCENT_HOVER,
            command=self._on_fetch_click,
        )
        self.fetch_btn.grid(row=1, column=3, padx=(8, 16), pady=6)
        ToolTip(self.fetch_btn, text="Fetch video title, thumbnail, and available formats")

        # ── Row 2: Destination folder ──
        folder_label = ctk.CTkLabel(self, text="Folder:", font=ctk.CTkFont(size=13))
        folder_label.grid(row=2, column=0, sticky="w", padx=(16, 8), pady=6)

        self.folder_entry = ctk.CTkEntry(
            self,
            placeholder_text="Choose download folder…",
            height=36,
            font=ctk.CTkFont(size=13),
        )
        # Set default to user's Downloads folder
        default_downloads = os.path.join(os.path.expanduser("~"), "Downloads")
        if os.path.isdir(default_downloads):
            self.folder_entry.insert(0, default_downloads)
        self.folder_entry.grid(row=2, column=1, columnspan=2, sticky="ew", padx=4, pady=6)

        browse_folder_btn = ctk.CTkButton(
            self,
            text="📁 Browse",
            width=120,
            height=36,
            font=ctk.CTkFont(size=13),
            fg_color=self.SECONDARY_COLOR,
            hover_color=self.SECONDARY_HOVER,
            command=self._browse_folder,
        )
        browse_folder_btn.grid(row=2, column=3, padx=(8, 16), pady=6)

        # ── Row 3: Cookies file ──
        cookies_label = ctk.CTkLabel(self, text="Cookies:", font=ctk.CTkFont(size=13))
        cookies_label.grid(row=3, column=0, sticky="w", padx=(16, 8), pady=(6, 14))

        self.cookies_entry = ctk.CTkEntry(
            self,
            placeholder_text="(Optional) Select cookies.txt…",
            height=36,
            font=ctk.CTkFont(size=13),
            state="disabled",
        )
        self.cookies_entry.grid(row=3, column=1, sticky="ew", padx=4, pady=(6, 14))

        browse_cookies_btn = ctk.CTkButton(
            self,
            text="🍪 Browse",
            width=100,
            height=36,
            font=ctk.CTkFont(size=13),
            fg_color=self.SECONDARY_COLOR,
            hover_color=self.SECONDARY_HOVER,
            command=self._browse_cookies,
        )
        browse_cookies_btn.grid(row=3, column=2, padx=4, pady=(6, 14))
        ToolTip(browse_cookies_btn, text="Load cookies.txt for authenticated downloads")

        clear_cookies_btn = ctk.CTkButton(
            self,
            text="✕",
            width=36,
            height=36,
            font=ctk.CTkFont(size=14),
            fg_color="#EF476F",
            hover_color="#D63E5C",
            command=self._clear_cookies,
        )
        clear_cookies_btn.grid(row=3, column=3, sticky="w", padx=(8, 16), pady=(6, 14))
        ToolTip(clear_cookies_btn, text="Remove cookies file")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_url(self) -> str:
        """Return the current URL from the entry field."""
        return self.url_entry.get().strip()

    def get_folder(self) -> str:
        """Return the selected destination folder path."""
        return self.folder_entry.get().strip()

    def get_cookies_path(self) -> str | None:
        """Return the cookies file path, or None if not set."""
        return self._cookies_path

    def set_fetching_state(self, fetching: bool) -> None:
        """Toggle button state during metadata fetching."""
        if fetching:
            self.fetch_btn.configure(text="⏳ Fetching…", state="disabled")
            self.url_entry.configure(state="disabled")
        else:
            self.fetch_btn.configure(text="⚡ Fetch Info", state="normal")
            self.url_entry.configure(state="normal")

    def set_downloading_state(self, downloading: bool) -> None:
        """Toggle button states during an active download."""
        state = "disabled" if downloading else "normal"
        self.fetch_btn.configure(state=state)
        self.url_entry.configure(state=state)

    # ------------------------------------------------------------------
    # Internal callbacks
    # ------------------------------------------------------------------

    def _on_fetch_click(self) -> None:
        """Handle Fetch Info button click."""
        if self.on_fetch:
            self.on_fetch()

    def _browse_folder(self) -> None:
        """Open a folder picker dialog."""
        folder = filedialog.askdirectory(title="Select Download Folder")
        if folder:
            self.folder_entry.delete(0, "end")
            self.folder_entry.insert(0, folder)

    def _browse_cookies(self) -> None:
        """Open a file picker for cookies.txt."""
        filepath = filedialog.askopenfilename(
            title="Select cookies.txt",
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")],
        )
        if filepath:
            self._cookies_path = filepath
            self.cookies_entry.configure(state="normal")
            self.cookies_entry.delete(0, "end")
            self.cookies_entry.insert(0, os.path.basename(filepath))
            self.cookies_entry.configure(state="disabled")

    def _clear_cookies(self) -> None:
        """Remove the loaded cookies file."""
        self._cookies_path = None
        self.cookies_entry.configure(state="normal")
        self.cookies_entry.delete(0, "end")
        self.cookies_entry.configure(state="disabled")
