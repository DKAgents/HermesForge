#!/usr/bin/env python3
"""
dedup.py — HermesForge EPIC-009 (US-061)

Deduplication log preventing repeated Discord posts for the same
strategy+ticker+entry-date setup within a lookback window.

Usage (unit test):
    python3 dedup.py --test
"""

import sys
import csv
import pathlib
import datetime

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from timezone_utils import now_pt
import config

LOG_PATH = pathlib.Path(config.DEDUP_LOG_PATH)
FIELDS = ["signal_id", "strategy_id", "ticker", "entry_date", "published_at", "channel"]


def _ensure_log():
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not LOG_PATH.exists():
        with open(LOG_PATH, "w", newline="") as f:
            csv.writer(f).writerow(FIELDS)


def make_signal_id(strategy_id: str, ticker: str, entry_date: str) -> str:
    """signal_id = {strategy_id}_{ticker}_{entry_date}"""
    return f"{strategy_id}_{ticker}_{entry_date}"


def _read_rows() -> list[dict]:
    _ensure_log()
    with open(LOG_PATH, newline="") as f:
        return list(csv.DictReader(f))


def is_duplicate(signal_id: str, lookback_days: int = config.DEFAULT_LOOKBACK_DAYS) -> bool:
    """
    Returns True if signal_id was published within the last lookback_days
    (calendar days, used as a simple proxy for trading days — acceptable
    since daily-bar signals cannot repeat sub-day anyway).
    """
    cutoff = now_pt().replace(tzinfo=None) - datetime.timedelta(days=lookback_days)
    for row in _read_rows():
        if row["signal_id"] != signal_id:
            continue
        try:
            published_at = datetime.datetime.fromisoformat(row["published_at"])
        except ValueError:
            continue
        if published_at >= cutoff:
            return True
    return False


def record_published(signal_id: str, strategy_id: str, ticker: str,
                      entry_date: str, channel: str) -> None:
    """Append a published-signal record to the dedup log."""
    _ensure_log()
    with open(LOG_PATH, "a", newline="") as f:
        csv.writer(f).writerow([
            signal_id, strategy_id, ticker, entry_date,
            now_pt().replace(tzinfo=None).isoformat(), channel,
        ])


def _test():
    import tempfile
    global LOG_PATH
    orig_path = LOG_PATH
    tmp = pathlib.Path(tempfile.mktemp(suffix=".csv"))
    LOG_PATH = tmp
    try:
        sid = make_signal_id("STR-B", "NVDA", "2026-07-20")
        assert sid == "STR-B_NVDA_2026-07-20"

        assert is_duplicate(sid) is False, "fresh log should have no duplicates"

        record_published(sid, "STR-B", "NVDA", "2026-07-20", "stocks")
        assert is_duplicate(sid) is True, "just-recorded signal should be a duplicate"
        assert is_duplicate(sid, lookback_days=0) is False, "0-day lookback should not match"

        other_sid = make_signal_id("STR-B", "AAPL", "2026-07-20")
        assert is_duplicate(other_sid) is False, "different ticker should not collide"

        print("✅ All dedup.py unit tests passed")
    finally:
        LOG_PATH = orig_path
        tmp.unlink(missing_ok=True)


if __name__ == "__main__":
    if "--test" in sys.argv:
        _test()
    else:
        print(__doc__)
