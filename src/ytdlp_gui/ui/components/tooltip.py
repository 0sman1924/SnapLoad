"""
tooltip.py — Hover tooltip widget for CustomTkinter.

Displays a small tooltip popup when the user hovers over a widget.
Styled to match the dark theme with smooth fade-in appearance.
"""

from __future__ import annotations

import customtkinter as ctk


class ToolTip:
    """
    Attach a hover tooltip to any CustomTkinter or Tkinter widget.

    Usage:
        button = ctk.CTkButton(master, text="Download")
        ToolTip(button, text="Start downloading the selected format")
    """

    def __init__(
        self,
        widget,
        text: str,
        delay_ms: int = 500,
        bg_color: str = "#2b2b3d",
        text_color: str = "#e0e0e0",
        font_size: int = 12,
    ):
        """
        Initialize the tooltip.

        Args:
            widget: The widget to attach the tooltip to.
            text: The tooltip text to display.
            delay_ms: Delay before showing the tooltip (milliseconds).
            bg_color: Tooltip background color.
            text_color: Tooltip text color.
            font_size: Font size for the tooltip text.
        """
        self._widget = widget
        self._text = text
        self._delay = delay_ms
        self._bg_color = bg_color
        self._text_color = text_color
        self._font_size = font_size
        self._tooltip_window = None
        self._after_id: str | None = None

        # Bind mouse events
        self._widget.bind("<Enter>", self._on_enter, add="+")
        self._widget.bind("<Leave>", self._on_leave, add="+")
        self._widget.bind("<ButtonPress>", self._on_leave, add="+")

    def _on_enter(self, event=None) -> None:
        """Schedule tooltip display after delay."""
        self._after_id = self._widget.after(self._delay, self._show)

    def _on_leave(self, event=None) -> None:
        """Cancel scheduled tooltip and hide if visible."""
        if self._after_id:
            self._widget.after_cancel(self._after_id)
            self._after_id = None
        self._hide()

    def _show(self) -> None:
        """Create and display the tooltip window."""
        if self._tooltip_window:
            return

        # Calculate position: below and to the right of the cursor
        x = self._widget.winfo_rootx() + 20
        y = self._widget.winfo_rooty() + self._widget.winfo_height() + 5

        # Create a top-level window without decorations
        self._tooltip_window = tw = ctk.CTkToplevel(self._widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")

        # Prevent the tooltip from appearing in the taskbar
        tw.attributes("-topmost", True)

        label = ctk.CTkLabel(
            tw,
            text=self._text,
            fg_color=self._bg_color,
            text_color=self._text_color,
            corner_radius=6,
            font=ctk.CTkFont(size=self._font_size),
            padx=10,
            pady=6,
        )
        label.pack()

    def _hide(self) -> None:
        """Destroy the tooltip window."""
        if self._tooltip_window:
            self._tooltip_window.destroy()
            self._tooltip_window = None
