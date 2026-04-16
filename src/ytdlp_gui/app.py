"""
app.py — Application class and window configuration.

Creates the CustomTkinter root window, sets the dark theme, configures
geometry/sizing, and embeds the MainWindow frame. This is the "shell"
of the application.
"""

from __future__ import annotations

import os
import sys
import logging

import customtkinter as ctk

from ytdlp_gui import __app_name__, __app_subtitle__, __version__
from ytdlp_gui.ui.main_window import MainWindow

logger = logging.getLogger(__name__)


def _get_asset_path(filename: str) -> str:
    """
    Resolve the path to an asset file, supporting both development
    and PyInstaller-bundled modes.

    Args:
        filename: The asset filename (e.g., "icon.ico").

    Returns:
        Absolute path to the asset file.
    """
    # When bundled with PyInstaller, assets are extracted to a temp dir
    if getattr(sys, "frozen", False):
        base = sys._MEIPASS  # type: ignore[attr-defined]
    else:
        base = os.path.dirname(os.path.abspath(__file__))

    return os.path.join(base, "assets", filename)


class App:
    """
    Main application class.

    Configures the CustomTkinter root window and launches the main event loop.
    """

    # Window dimensions
    DEFAULT_WIDTH = 920
    DEFAULT_HEIGHT = 780
    MIN_WIDTH = 750
    MIN_HEIGHT = 600

    def __init__(self):
        """Initialize the application window and UI."""
        # ── Theme configuration ──
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # ── Root window ──
        self.root = ctk.CTk()
        self.root.title(f"{__app_name__} — {__app_subtitle__}  v{__version__}")
        self.root.geometry(f"{self.DEFAULT_WIDTH}x{self.DEFAULT_HEIGHT}")
        self.root.minsize(self.MIN_WIDTH, self.MIN_HEIGHT)

        # Set window icon (if available)
        icon_path = _get_asset_path("icon.ico")
        if os.path.exists(icon_path):
            try:
                self.root.iconbitmap(icon_path)
            except Exception:
                logger.debug("Could not set window icon: %s", icon_path)

        # ── Configure root grid ──
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(0, weight=1)

        # ── Embed main window ──
        self.main_window = MainWindow(self.root)
        self.main_window.grid(row=0, column=0, sticky="nsew")

        logger.info("%s v%s initialized.", __app_name__, __version__)

    def run(self) -> None:
        """Start the Tkinter event loop."""
        logger.info("Starting main event loop…")
        self.root.mainloop()
