"""
timezone_utils.py — Shared timezone helpers for HermesForge.

All internal data processing uses UTC. All user-facing display (Discord posts,
reports, embeds) uses Pacific Time (America/Los_Angeles, which auto-switches
between PDT and PST based on US DST rules).

Usage:
    from timezone_utils import now_pt, format_pt, pt_timestamp
"""

from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo

PT = ZoneInfo("America/Los_Angeles")
UTC = timezone.utc


def now_pt() -> datetime:
    """Current time in Pacific Time (auto DST)."""
    return datetime.now(PT)


def format_pt(fmt: str = "%Y-%m-%d %H:%M %Z") -> str:
    """Format current time in Pacific Time."""
    return now_pt().strftime(fmt)


def pt_timestamp() -> str:
    """ISO timestamp with Pacific timezone offset."""
    return now_pt().isoformat()


def to_pt(dt: datetime) -> datetime:
    """Convert any datetime to Pacific Time."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt.astimezone(PT)


def format_dt_pt(dt: datetime, fmt: str = "%Y-%m-%d %H:%M %Z") -> str:
    """Format a datetime in Pacific Time."""
    return to_pt(dt).strftime(fmt)


def pt_label() -> str:
    """Short timezone label: 'PT' or 'PDT' or 'PST'."""
    return now_pt().strftime("%Z")
