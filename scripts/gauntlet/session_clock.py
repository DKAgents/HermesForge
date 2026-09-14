"""
Session Clock Module (PROP-001)
Tracks trading sessions, liquidity tiers, funding settlement timing,
session overlaps, and CME gap windows.
"""

from datetime import datetime, timezone


# ── Session Definitions (UTC) ─────────────────────────────────────────────

# ASIA:  00:00 - 08:00 UTC
# EU:    08:00 - 13:30 UTC
# US:    13:30 - 21:00 UTC
# LOW_LIQUIDITY: 21:00 - 00:00 UTC (and portions of Saturday)
# WEEKEND: Saturday 00:00 through Sunday 23:59 UTC

# Day constants for weekday()
MONDAY = 0
TUESDAY = 1
WEDNESDAY = 2
THURSDAY = 3
FRIDAY = 4
SATURDAY = 5
SUNDAY = 6


def current_session(timestamp_unix: float = None) -> str:
    """
    Return the current trading session as a string.

    Args:
        timestamp_unix: POSIX timestamp (float, seconds). Defaults to now (UTC).

    Returns:
        'ASIA', 'EU', 'US', 'LOW_LIQUIDITY', or 'WEEKEND'
    """
    if timestamp_unix is None:
        dt = datetime.now(timezone.utc)
    else:
        dt = datetime.fromtimestamp(timestamp_unix, tz=timezone.utc)

    weekday = dt.weekday()
    hour = dt.hour
    minute = dt.minute
    time_float = hour + minute / 60.0

    # Weekend: Saturday 00:00 through Sunday 23:59
    if weekday == SATURDAY or weekday == SUNDAY:
        return 'WEEKEND'

    # Friday after 21:00 UTC is effectively weekend
    if weekday == FRIDAY and time_float >= 21.0:
        return 'WEEKEND'

    # ASIA: 00:00-08:00 UTC
    if time_float < 8.0:
        return 'ASIA'

    # EU: 08:00-13:30 UTC
    if time_float < 13.5:
        return 'EU'

    # US: 13:30-21:00 UTC
    if time_float < 21.0:
        return 'US'

    # 21:00-00:00 UTC → LOW_LIQUIDITY
    return 'LOW_LIQUIDITY'


def liquidity_tier(session: str) -> str:
    """
    Map a session name to its liquidity tier.

    Args:
        session: session string from current_session()

    Returns:
        'HIGH', 'MEDIUM', or 'LOW'
    """
    tiers = {
        'US': 'HIGH',
        'EU': 'HIGH',
        'ASIA': 'MEDIUM',
        'LOW_LIQUIDITY': 'LOW',
        'WEEKEND': 'LOW',
    }
    return tiers.get(session, 'LOW')


def minutes_to_settlement(timestamp_unix: float = None) -> int:
    """
    Minutes until the next hourly funding settlement (always on the hour).

    Args:
        timestamp_unix: POSIX timestamp (float, seconds). Defaults to now (UTC).

    Returns:
        int: minutes remaining until next hour boundary (0-59)
    """
    if timestamp_unix is None:
        dt = datetime.now(timezone.utc)
    else:
        dt = datetime.fromtimestamp(timestamp_unix, tz=timezone.utc)

    minutes_past = dt.minute
    seconds_past = dt.second

    if minutes_past == 0 and seconds_past == 0:
        return 0

    # Minutes until next full hour
    remaining = 60 - minutes_past
    if seconds_past > 0:
        remaining -= 1

    return max(0, remaining)


def session_overlap(current_time_unix: float = None) -> str:
    """
    Determine which sessions are currently overlapping.

    Overlap windows (approximate):
      - ASIA+EU:    08:00 UTC                   (ASIA tail + EU open)
      - EU+US:      13:30 - 16:00 UTC           (EU afternoon + US open)

    Args:
        current_time_unix: POSIX timestamp. Defaults to now.

    Returns:
        str: e.g. 'ASIA+EU', 'EU+US', 'ASIA', 'EU', 'US', 'LOW_LIQUIDITY', 'WEEKEND'
    """
    if current_time_unix is None:
        dt = datetime.now(timezone.utc)
    else:
        dt = datetime.fromtimestamp(current_time_unix, tz=timezone.utc)

    weekday = dt.weekday()
    hour = dt.hour
    minute = dt.minute
    time_float = hour + minute / 60.0

    # Weekend
    if weekday == SATURDAY or weekday == SUNDAY:
        return 'WEEKEND'
    if weekday == FRIDAY and time_float >= 21.0:
        return 'WEEKEND'

    # EU+US overlap: 13:30 - 16:00 UTC
    if 13.5 <= time_float < 16.0:
        return 'EU+US'

    # ASIA+EU overlap: 08:00 UTC (brief tail overlap)
    # Actually ASIA is 00:00-08:00 and EU is 08:00-13:30.
    # The only overlap point is exactly 08:00. But practically there's a
    # thin band around it. We define ASIA+EU at 07:30-08:00.
    if 7.5 <= time_float < 8.0:
        return 'ASIA+EU'

    # Pure sessions
    session = current_session(timestamp_unix=current_time_unix)
    return session


def is_cme_gap_window(timestamp_unix: float = None) -> bool:
    """
    Check if we are in the CME gap window (Friday close to Sunday open).

    CME futures close Friday ~21:00 UTC and reopen Sunday ~22:00 UTC.
    Gap risk exists in this window.

    Args:
        timestamp_unix: POSIX timestamp. Defaults to now.

    Returns:
        bool: True if inside the CME gap window
    """
    if timestamp_unix is None:
        dt = datetime.now(timezone.utc)
    else:
        dt = datetime.fromtimestamp(timestamp_unix, tz=timezone.utc)

    weekday = dt.weekday()
    hour = dt.hour
    minute = dt.minute
    time_float = hour + minute / 60.0

    # Friday after close: 21:00 UTC Friday through Saturday 23:59
    if weekday == FRIDAY and time_float >= 21.0:
        return True

    # Saturday all day
    if weekday == SATURDAY:
        return True

    # Sunday before open: 00:00 - 21:59 UTC Sunday
    if weekday == SUNDAY and time_float < 22.0:
        return True

    return False


def weekend_flag(timestamp_unix: float = None) -> bool:
    """
    Check if the current time falls in the weekend window.

    Weekend: Saturday 00:00 UTC through Sunday 23:59 UTC,
    plus Friday after 21:00 UTC (effectively weekend for crypto markets).

    Args:
        timestamp_unix: POSIX timestamp. Defaults to now.

    Returns:
        bool: True if it's the weekend
    """
    session = current_session(timestamp_unix=timestamp_unix)
    return session == 'WEEKEND'