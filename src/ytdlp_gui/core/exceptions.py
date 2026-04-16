"""
exceptions.py — Custom exception classes and error message parser.

Maps raw yt-dlp exceptions into user-friendly, actionable messages
that are displayed in the Log Panel.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum


class ErrorSeverity(Enum):
    """Severity levels for log messages."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    SUCCESS = "success"


@dataclass
class ParsedError:
    """A user-friendly error with severity and optional suggestion."""
    message: str
    severity: ErrorSeverity = ErrorSeverity.ERROR
    suggestion: str | None = None

    def __str__(self) -> str:
        """Format the error for display in the log panel."""
        text = self.message
        if self.suggestion:
            text += f" 💡 {self.suggestion}"
        return text


# ---------------------------------------------------------------------------
# Error pattern registry
# Each tuple: (regex pattern to match against the raw error string,
#               user-friendly message,
#               optional suggestion,
#               severity)
# ---------------------------------------------------------------------------
_ERROR_PATTERNS: list[tuple[str, str, str | None, ErrorSeverity]] = [
    # DNS / Network resolution failures
    (
        r"Failed to resolve.*getaddrinfo failed",
        "DNS resolution failed — could not connect to the server.",
        "This is usually a temporary network glitch. Try again in a few seconds.",
        ErrorSeverity.ERROR,
    ),
    # Connection timeout
    (
        r"(timed?\s*out|TimeoutError|ConnectTimeoutError)",
        "Connection timed out.",
        "Check your internet connection and try again.",
        ErrorSeverity.ERROR,
    ),
    # HTTP 403 — Forbidden (needs cookies)
    (
        r"(HTTP Error 403|403\s*Forbidden|Sign in to confirm)",
        "Access forbidden — the server rejected the request.",
        "Try providing a cookies.txt file from a logged-in browser session.",
        ErrorSeverity.ERROR,
    ),
    # Login / authentication required
    (
        r"(login|sign\s*in|authenticate|cookies)",
        "Authentication required to access this content.",
        "Export cookies.txt from your browser and load it in the Cookies field.",
        ErrorSeverity.WARNING,
    ),
    # Private / members-only video
    (
        r"(private video|members.only|is private)",
        "This video is private or members-only.",
        "Use a cookies.txt file from an account with access to this video.",
        ErrorSeverity.ERROR,
    ),
    # Geo-restricted content
    (
        r"(geo.restricted|not available in your country|blocked.in)",
        "This video is geo-restricted in your region.",
        "Try using a VPN or a cookies file from an allowed region.",
        ErrorSeverity.ERROR,
    ),
    # Video unavailable / removed
    (
        r"(video.*unavailable|has been removed|does not exist|Video unavailable)",
        "This video is unavailable or has been removed.",
        None,
        ErrorSeverity.ERROR,
    ),
    # Age-restricted content
    (
        r"(age.restricted|age.gate|confirm your age)",
        "This video is age-restricted.",
        "Provide a cookies.txt file from a logged-in account to bypass the age gate.",
        ErrorSeverity.ERROR,
    ),
    # Unsupported URL / extractor
    (
        r"(Unsupported URL|no suitable.*extractor|is not a valid URL)",
        "This URL is not supported or is invalid.",
        "Double-check the URL and ensure it's from a supported site.",
        ErrorSeverity.ERROR,
    ),
    # FFmpeg not found
    (
        r"(ffmpeg|ffprobe|avconv).*(not found|is not recognized|missing)",
        "FFmpeg was not found on your system.",
        "Install FFmpeg and ensure it's in your system PATH. Some formats require it for merging.",
        ErrorSeverity.ERROR,
    ),
    # Postprocessor / merge error
    (
        r"(Postprocessing|merging|muxing).*error",
        "Error during post-processing (merging audio/video).",
        "Ensure FFmpeg is installed and up-to-date.",
        ErrorSeverity.ERROR,
    ),
    # Rate limiting / too many requests
    (
        r"(429|Too Many Requests|rate.limit)",
        "Rate limited — too many requests to the server.",
        "Wait a minute and try again, or use a cookies file.",
        ErrorSeverity.WARNING,
    ),
    # Disk space / permission errors
    (
        r"(No space left|disk full|Permission denied|Access is denied)",
        "File system error — cannot write to the output directory.",
        "Check disk space and folder permissions.",
        ErrorSeverity.ERROR,
    ),
]


def parse_error(raw_error: str | Exception) -> ParsedError:
    """
    Parse a raw yt-dlp error string or exception into a user-friendly message.

    Iterates through known error patterns and returns the first match.
    Falls back to a sanitized version of the original error if no pattern matches.

    Args:
        raw_error: The raw error string or Exception from yt-dlp.

    Returns:
        A ParsedError with a clean message and optional suggestion.
    """
    error_str = str(raw_error)

    # Try each registered pattern
    for pattern, message, suggestion, severity in _ERROR_PATTERNS:
        if re.search(pattern, error_str, re.IGNORECASE):
            return ParsedError(
                message=message,
                severity=severity,
                suggestion=suggestion,
            )

    # Fallback: sanitize the raw error for display
    # Strip the "ERROR: [extractor] id:" prefix that yt-dlp adds
    cleaned = re.sub(r"^ERROR:\s*\[.*?\]\s*\S+:\s*", "", error_str).strip()
    if not cleaned:
        cleaned = error_str.strip()

    return ParsedError(
        message=cleaned if len(cleaned) < 200 else cleaned[:200] + "…",
        severity=ErrorSeverity.ERROR,
        suggestion=None,
    )
