"""
log_panel.py — Scrollable, color-coded log output panel.

Displays timestamped log messages with severity-based coloring:
  - INFO (cyan), SUCCESS (green), WARNING (amber), ERROR (red)

Auto-scrolls to the latest message.
"""

from __future__ import annotations

from datetime import datetime

import customtkinter as ctk

from ytdlp_gui.core.exceptions import ErrorSeverity


class LogPanel(ctk.CTkFrame):
    """
    Scrollable log panel with color-coded, timestamped messages.

    Supports INFO, SUCCESS, WARNING, and ERROR severity levels,
    each rendered in a distinct color for quick visual scanning.
    """

    # Color scheme for each severity level
    SEVERITY_COLORS: dict[ErrorSeverity, str] = {
        ErrorSeverity.INFO: "#60a5fa",      # Soft blue
        ErrorSeverity.SUCCESS: "#06D6A0",    # Green
        ErrorSeverity.WARNING: "#FFD166",    # Amber
        ErrorSeverity.ERROR: "#EF476F",      # Coral red
    }

    def __init__(self, master, **kwargs):
        super().__init__(
            master,
            fg_color=("gray92", "#1e1e2e"),
            corner_radius=12,
            **kwargs,
        )
        self._build_ui()

    def _build_ui(self) -> None:
        """Construct the log panel layout."""
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # ── Header row with clear button ──
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", padx=16, pady=(14, 4))
        header_frame.grid_columnconfigure(0, weight=1)

        header = ctk.CTkLabel(
            header_frame,
            text="📋  Logs",
            font=ctk.CTkFont(size=15, weight="bold"),
            anchor="w",
        )
        header.grid(row=0, column=0, sticky="w")

        clear_btn = ctk.CTkButton(
            header_frame,
            text="🗑 Clear",
            width=80,
            height=28,
            font=ctk.CTkFont(size=12),
            fg_color="#374151",
            hover_color="#4B5563",
            command=self.clear,
        )
        clear_btn.grid(row=0, column=1, sticky="e")

        # ── Log text area ──
        self.textbox = ctk.CTkTextbox(
            self,
            height=150,
            font=ctk.CTkFont(family="Consolas", size=12),
            fg_color=("gray96", "#12121c"),
            corner_radius=8,
            state="disabled",
            wrap="word",
            activate_scrollbars=True,
        )
        self.textbox.grid(row=1, column=0, sticky="nsew", padx=16, pady=(4, 14))

        # Configure text tags for colored severity levels
        for severity, color in self.SEVERITY_COLORS.items():
            self.textbox._textbox.tag_configure(severity.value, foreground=color)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def log(self, message: str, severity: ErrorSeverity = ErrorSeverity.INFO) -> None:
        """
        Append a timestamped, color-coded message to the log.

        Args:
            message: The log message text.
            severity: Severity level determining the text color.
        """
        timestamp = datetime.now().strftime("%H:%M:%S")
        severity_label = severity.value.upper()
        prefix = f"[{timestamp}] {severity_label}: "
        full_text = f"{prefix}{message}\n"

        # Enable writing, insert text with tag, disable again
        self.textbox.configure(state="normal")
        self.textbox._textbox.insert("end", full_text, severity.value)
        self.textbox.configure(state="disabled")

        # Auto-scroll to bottom
        self.textbox._textbox.see("end")

    def log_info(self, message: str) -> None:
        """Shortcut for logging an INFO message."""
        self.log(message, ErrorSeverity.INFO)

    def log_success(self, message: str) -> None:
        """Shortcut for logging a SUCCESS message."""
        self.log(message, ErrorSeverity.SUCCESS)

    def log_warning(self, message: str) -> None:
        """Shortcut for logging a WARNING message."""
        self.log(message, ErrorSeverity.WARNING)

    def log_error(self, message: str) -> None:
        """Shortcut for logging an ERROR message."""
        self.log(message, ErrorSeverity.ERROR)

    def clear(self) -> None:
        """Remove all log entries."""
        self.textbox.configure(state="normal")
        self.textbox._textbox.delete("1.0", "end")
        self.textbox.configure(state="disabled")
