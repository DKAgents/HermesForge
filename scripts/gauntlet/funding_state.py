"""
Funding State Module (PROP-001)
Implements the Hyperliquid funding formula exactly per specification.
"""

import math
import statistics
from datetime import datetime, timezone


# ── Constants ──────────────────────────────────────────────────────────────
INTEREST_COMPONENT = 0.0001          # 0.01% per 8h period
PREMIUM_CAP = 0.0005                 # ±0.05% clamp on raw premium (per 8h)
HARD_CAP_HOURLY = 0.04               # 4% per hour
SETTLEMENT_INTERVAL_MINUTES = 60     # hourly settlements


# ── Funding Rate ───────────────────────────────────────────────────────────

def compute_funding_rate(premium_raw_8h: float) -> float:
    """
    Compute the 8-hour funding rate from a raw premium (over the same 8h window).

    Formula (per the Hyperliquid spec):
      premium = max(min(premium_raw, 0.0005), -0.0005)
      rate    = clamp(interest_component + premium, -hard_cap, hard_cap)

    Returns the **8-hour** funding rate as a decimal (e.g. 0.0001 = 0.01%).
    """
    premium = max(min(premium_raw_8h, PREMIUM_CAP), -PREMIUM_CAP)
    raw = INTEREST_COMPONENT + premium
    rate = max(min(raw, HARD_CAP_HOURLY), -HARD_CAP_HOURLY)
    return rate


# ── Hourly Payment ─────────────────────────────────────────────────────────

def compute_hourly_payment(position_size_usd: float, funding_rate_8h: float) -> float:
    """
    Compute the USD payment for a single hourly settlement.

    hourly_payment = (1/8) * funding_rate_8h * position_size_usd

    Positive  payment → long  pays / short receives
    Negative payment → short pays / long  receives
    """
    return (1.0 / 8.0) * funding_rate_8h * position_size_usd


# ── Z-Score ────────────────────────────────────────────────────────────────

def compute_funding_z(funding_rates_8h_history: list) -> float:
    """
    Z-score of the latest funding rate relative to the distribution of the
    full history.  The *last* element is treated as the latest observation.

    For a single-element list the z-score is 0.0 (no detectable deviation).
    For an empty list the z-score is 0.0.
    """
    if len(funding_rates_8h_history) < 2:
        return 0.0
    latest = funding_rates_8h_history[-1]
    rest = funding_rates_8h_history[:-1]
    mean = statistics.mean(rest)
    stdev = statistics.stdev(rest) if len(rest) >= 2 else 0.0
    if stdev == 0.0:
        return 0.0 if latest == mean else (float('inf') if latest > mean else float('-inf'))
    return (latest - mean) / stdev


# ── Carry (bps / hour) ─────────────────────────────────────────────────────

def compute_carry_bps_per_hour(funding_rate_8h: float) -> float:
    """
    Funding cost expressed in basis points per hour of holding a long position.

    1 bp = 0.01% = 0.0001

    The 8h rate is first divided by 8 to get the hourly rate, then multiplied
    by 10000 to convert to bp.
    """
    hourly = funding_rate_8h / 8.0
    return hourly * 10000.0


# ── Settlement Countdown ───────────────────────────────────────────────────

def settlement_countdown(current_time_unix: int | float | None = None) -> int:
    """
    Minutes until the next hourly settlement (top of the hour).

    If *current_time_unix* is omitted the current system time is used.
    Returns an integer 0–59.
    """
    if current_time_unix is None:
        dt = datetime.now(timezone.utc)
    else:
        dt = datetime.fromtimestamp(current_time_unix, tz=timezone.utc)
    minutes_past = dt.minute
    seconds_past = dt.second
    remaining_seconds = (SETTLEMENT_INTERVAL_MINUTES - minutes_past) * 60 - seconds_past
    # Floor to the nearest whole minute, wrap 60 → 0 (exact top of hour).
    minutes = remaining_seconds // 60
    return 0 if minutes == 60 else minutes


# ── Crowding Assessment ────────────────────────────────────────────────────

def assess_crowding(funding_z: float, oi_trend: float) -> tuple:
    """
    Combine funding z-score and OI trend into a crowding assessment.

    Parameters
    ----------
    funding_z : float
        Z-score of the current funding rate.
    oi_trend : float
        Smoothed OI trend (e.g. 7-day ROC as a decimal).

    Returns
    -------
    (crowding_flag: bool, severity: str)
        severity ∈ {'low', 'moderate', 'high', 'extreme'}
    """
    # ── funding signal ──
    if abs(funding_z) < 1.0:
        f_sev = 0
    elif abs(funding_z) < 2.0:
        f_sev = 1
    elif abs(funding_z) < 3.0:
        f_sev = 2
    else:
        f_sev = 3

    # ── OI trend signal ──
    oi_abs = abs(oi_trend)
    if oi_abs < 0.05:
        o_sev = 0
    elif oi_abs < 0.10:
        o_sev = 1
    elif oi_abs < 0.20:
        o_sev = 2
    else:
        o_sev = 3

    combined = f_sev + o_sev

    if combined == 0:
        severity = 'low'
    elif combined <= 2:
        severity = 'moderate'
    elif combined <= 4:
        severity = 'high'
    else:
        severity = 'extreme'

    crowding_flag = combined >= 3  # 'high' or 'extreme'
    return (crowding_flag, severity)