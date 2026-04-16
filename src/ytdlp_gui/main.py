"""
main.py — Application entry point.

Configures logging, then creates and launches the App.
Run with:  python -m ytdlp_gui.main
"""

from __future__ import annotations

import logging
import sys


def _setup_logging() -> None:
    """Configure application-wide logging with a clean format."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
        handlers=[logging.StreamHandler(sys.stdout)],
    )

    # Reduce noise from third-party libraries
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("PIL").setLevel(logging.WARNING)


def main() -> None:
    """Application entry point."""
    _setup_logging()

    # Import here to ensure logging is configured before any module-level logs
    from ytdlp_gui.app import App

    app = App()
    app.run()


if __name__ == "__main__":
    main()
