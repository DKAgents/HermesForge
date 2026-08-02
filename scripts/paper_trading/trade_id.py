#!/usr/bin/env python3
"""
trade_id.py — Terse smart trade identifiers for HermesForge.

Format: {TICKER}-{STRAT_CODE}-{MMDD}{SEQ}
  TICKER     — uppercase ticker (BTC, NVDA, SOL, etc.)
  STRAT_CODE — single letter from strategy ID (B, I, P, L, etc.)
  MMDD       — signal date: zero-padded month + day (0727 = July 27)
  SEQ        — sequence letter for same ticker/strategy/date (A, B, C, ...)

Examples:
  BTC-P-0727A    — BTC, STR-P, July 27, first trade
  NVDA-B-0731A   — NVDA, STR-B, July 31, first trade
  SOL-P-0727B    — SOL, STR-P, July 27, second trade (if duplicate ticker)

Discord message URL construction:
  https://discord.com/channels/{guild_id}/{channel_id}/{message_id}

Usage:
    from trade_id import generate_short_id, make_discord_url, parse_short_id
"""

import re
import datetime
from typing import Optional

# ── Guild ID (HermesForge Discord server) ─────────────────────────────────────

DISCORD_GUILD_ID = "1500553453628428361"

# ── Strategy code mapping ─────────────────────────────────────────────────────
# Extracts the single-letter strategy code from full strategy_id strings.
# e.g. "STR-B-macd-histogram-divergence" -> "B"

_STRAT_PATTERN = re.compile(r"STR-([A-Z])(?:-|$)")


def get_strategy_code(strategy_id: str) -> str:
    """Extract single-letter strategy code from strategy_id."""
    m = _STRAT_PATTERN.search(strategy_id)
    return m.group(1) if m else "X"


def generate_short_id(
    ticker: str,
    strategy_id: str,
    signal_date: str | datetime.date,
    sequence: int = 0,
) -> str:
    """
    Generate a terse trade identifier.

    Args:
        ticker: Asset ticker (e.g. "BTC", "NVDA")
        strategy_id: Full strategy ID (e.g. "STR-P-crosssectional")
        signal_date: Date string "YYYY-MM-DD" or datetime.date
        sequence: 0=A, 1=B, 2=C, ... for multiple trades same ticker/strategy/date

    Returns:
        Terse ID like "BTC-P-0727A"
    """
    # Parse date
    if isinstance(signal_date, str):
        dt = datetime.datetime.strptime(signal_date[:10], "%Y-%m-%d")
    elif isinstance(signal_date, datetime.date):
        dt = datetime.datetime(signal_date.year, signal_date.month, signal_date.day)
    elif isinstance(signal_date, datetime.datetime):
        dt = signal_date
    else:
        raise ValueError(f"Cannot parse signal_date: {signal_date}")

    mmdd = f"{dt.month:02d}{dt.day:02d}"
    strat_code = get_strategy_code(strategy_id)
    seq_letter = chr(ord("A") + sequence) if sequence < 26 else str(sequence)

    return f"{ticker.upper()}-{strat_code}-{mmdd}{seq_letter}"


def parse_short_id(short_id: str) -> dict:
    """
    Parse a terse trade ID back into components.

    Returns:
        {ticker, strategy_code, date (MMDD), sequence (int)}
    """
    pattern = r"^([A-Z0-9]+)-([A-Z])-(\d{4})([A-Z])$"
    m = re.match(pattern, short_id)
    if not m:
        raise ValueError(f"Invalid short_id format: {short_id}")

    ticker, strat_code, mmdd, seq_letter = m.groups()
    sequence = ord(seq_letter) - ord("A")

    return {
        "ticker": ticker,
        "strategy_code": strat_code,
        "mmdd": mmdd,
        "sequence": sequence,
    }


def make_discord_url(
    channel_id: str,
    message_id: str,
    guild_id: str = DISCORD_GUILD_ID,
) -> str:
    """Construct a Discord message URL."""
    return f"https://discord.com/channels/{guild_id}/{channel_id}/{message_id}"


def make_discord_link(
    short_id: str,
    channel_id: str,
    message_id: str,
    guild_id: str = DISCORD_GUILD_ID,
) -> str:
    """
    Create a Markdown hyperlink for the trade ID pointing to the Discord message.

    Returns:
        "[BTC-P-0727A](https://discord.com/channels/.../.../...)"
    """
    url = make_discord_url(channel_id, message_id, guild_id)
    return f"[{short_id}]({url})"


# ── Tests ─────────────────────────────────────────────────────────────────────

def _test():
    # Basic generation
    sid = generate_short_id("BTC", "STR-P-crosssectional", "2026-07-27")
    assert sid == "BTC-P-0727A", f"got {sid}"

    sid2 = generate_short_id("NVDA", "STR-B-macd-histogram-divergence", "2026-07-31")
    assert sid2 == "NVDA-B-0731A", f"got {sid2}"

    # Sequence letters
    sid3 = generate_short_id("SOL", "STR-P-crosssectional", "2026-07-27", sequence=1)
    assert sid3 == "SOL-P-0727B", f"got {sid3}"

    # Parse
    parsed = parse_short_id("BTC-P-0727A")
    assert parsed["ticker"] == "BTC"
    assert parsed["strategy_code"] == "P"
    assert parsed["mmdd"] == "0727"
    assert parsed["sequence"] == 0

    parsed2 = parse_short_id("NVDA-B-0731A")
    assert parsed2["ticker"] == "NVDA"
    assert parsed2["strategy_code"] == "B"

    # Discord URL
    url = make_discord_url("1528555885310513213", "1234567890")
    assert "1500553453628428361" in url
    assert "1528555885310513213" in url
    assert "1234567890" in url

    # Markdown link
    link = make_discord_link("BTC-P-0727A", "1528555885310513213", "1234567890")
    assert link.startswith("[BTC-P-0727A](")
    assert "discord.com" in link

    # datetime.date input
    d = datetime.date(2026, 7, 27)
    sid4 = generate_short_id("BTC", "STR-P", d)
    assert sid4 == "BTC-P-0727A"

    print("✅ All trade_id.py tests passed")


if __name__ == "__main__":
    _test()
