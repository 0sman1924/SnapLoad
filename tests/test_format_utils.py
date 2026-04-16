"""
test_format_utils.py — Unit tests for the formatting utility functions.
"""

from ytdlp_gui.utils.format_utils import (
    format_bytes,
    format_duration,
    format_eta,
    format_speed,
    truncate_title,
)


class TestFormatBytes:
    """Tests for format_bytes()."""

    def test_zero_bytes(self):
        assert format_bytes(0) == "0 B"

    def test_bytes(self):
        assert format_bytes(512) == "512 B"

    def test_kilobytes(self):
        assert format_bytes(1536) == "1.5 KB"

    def test_megabytes(self):
        assert format_bytes(1048576) == "1.0 MB"

    def test_gigabytes(self):
        result = format_bytes(1073741824)
        assert result == "1.0 GB"

    def test_none_returns_na(self):
        assert format_bytes(None) == "N/A"

    def test_negative_returns_na(self):
        assert format_bytes(-1) == "N/A"


class TestFormatSpeed:
    """Tests for format_speed()."""

    def test_megabytes_per_sec(self):
        assert format_speed(1048576) == "1.0 MB/s"

    def test_none_returns_placeholder(self):
        assert format_speed(None) == "-- MB/s"

    def test_zero_returns_placeholder(self):
        assert format_speed(0) == "-- MB/s"


class TestFormatEta:
    """Tests for format_eta()."""

    def test_seconds_only(self):
        assert format_eta(45) == "00:45"

    def test_minutes_and_seconds(self):
        assert format_eta(90) == "01:30"

    def test_hours(self):
        assert format_eta(3661) == "1:01:01"

    def test_none_returns_placeholder(self):
        assert format_eta(None) == "--:--"


class TestFormatDuration:
    """Tests for format_duration()."""

    def test_normal_duration(self):
        assert format_duration(632) == "10:32"

    def test_none_returns_unknown(self):
        assert format_duration(None) == "Unknown"


class TestTruncateTitle:
    """Tests for truncate_title()."""

    def test_short_title_unchanged(self):
        assert truncate_title("Hello World") == "Hello World"

    def test_long_title_truncated(self):
        title = "A" * 100
        result = truncate_title(title, max_length=60)
        assert len(result) <= 60
        assert result.endswith("…")

    def test_exact_length_unchanged(self):
        title = "A" * 60
        assert truncate_title(title, max_length=60) == title
