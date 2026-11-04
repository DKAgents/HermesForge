"""
US-227 — swing hostile degenerate-stop/outlier gate.

Asserts the actual generator (hostile_fills.run()) emits `outlier_excluded` on
closed swing records and marks a near-zero-risk stop as an outlier (True) while
a normal-risk stop is False — matching STR-Q's DEGENERATE_RISK_FLOOR gate.

Run: python3 scripts/paper_trading/tests/test_hostile_fills.py
"""

import sys
import os
import json
import math
import pathlib
import tempfile

# Absolute paper_trading dir (avoid "../" so hostile_fills' relative REPO_ROOT
# path-computation resolves its gauntlet/discord sys.path inserts correctly).
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd

import hostile_fills
from pnl_accounting import DEGENERATE_RISK_FLOOR, widen_stop, STOP_WIDEN_FACTOR


def _bars(long_entries):
    """A 3-bar daily frame whose bars are listed top-to-bottom."""
    return pd.DataFrame(long_entries)


def _trade(stop_price):
    """A minimal closed+entered swing trade (STR-B) with the given stop."""
    return {
        "trade_id": "STR-B-macd-histogram-divergence_TEST_2026-10-01",
        "ticker": "TEST",
        "direction": "long",
        "strategy_id": "STR-B-macd-histogram-divergence",
        "entry_date": "2026-10-01",
        "entry_price": "100.0",
        "stop_price": stop_price,
        "target_price": "110.0",
        "asset_class": "stock",
        "status": "closed",
        "entry_status": "entered",
        "exit_price": "100.0",
        "exit_reason": "stop",
        "signal_id": "STR-B-macd-histogram-divergence_TEST_2026-10-01",
    }


def _run_with(trade, bars):
    """Run the swing generator against one synthetic trade + synthetic bars.

    Monkeypatches trade_log and bar loading and REPORT_PATH so nothing touches
    the real ledger / market data. Returns the written ledger rows.
    """
    tmp = tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False)
    tmp.close()
    tmp_path = pathlib.Path(tmp.name)

    orig = (
        hostile_fills.trade_log.get_pending_trades,
        hostile_fills.trade_log._read_all_rows,
        hostile_fills._load_bars_since,
        hostile_fills.REPORT_PATH,
    )
    try:
        hostile_fills.trade_log.get_pending_trades = lambda: []
        hostile_fills.trade_log._read_all_rows = lambda: [trade]
        hostile_fills._load_bars_since = lambda ticker, ed, ac: bars
        hostile_fills.REPORT_PATH = tmp_path
        hostile_fills.run(dry_run=False)
        return [json.loads(l) for l in open(tmp_path) if l.strip()]
    finally:
        (hostile_fills.trade_log.get_pending_trades,
         hostile_fills.trade_log._read_all_rows,
         hostile_fills._load_bars_since,
         hostile_fills.REPORT_PATH) = orig
        os.unlink(tmp_path)


def _closed_row(rows):
    return [r for r in rows if r.get("stage") == "closed"][0]


def test_degenerate_stop_marked_outlier():
    """A near-zero-risk stop (setup risk < DEGENERATE_RISK_FLOOR) is flagged
    outlier_excluded=True even though a hostile_r value is still computed."""
    # stop 99.96 -> widened distance ~0.08 -> setup risk ~0.0008 < 0.001 (floor)
    assert math.isclose(widen_stop(100.0, 99.96, "long", STOP_WIDEN_FACTOR),
                        100.0 - 0.08, rel_tol=1e-9)
    bars = _bars([
        {"date": "2026-10-01", "open": 100.0, "high": 101.0, "low": 99.0, "close": 100.0, "bar_idx": 0},
        {"date": "2026-10-02", "open": 99.5, "high": 100.0, "low": 98.5, "close": 99.0, "bar_idx": 1},
        {"date": "2026-10-03", "open": 99.0, "high": 99.8, "low": 98.0, "close": 98.5, "bar_idx": 2},
    ])
    rows = _run_with(_trade("99.96"), bars)
    closed = _closed_row(rows)

    assert closed["outlier_excluded"] is True
    assert closed["hostile_r"] is not None  # still computed, but flagged


def test_normal_stop_not_marked_outlier():
    """A normal-risk stop (setup risk >= DEGENERATE_RISK_FLOOR) is False."""
    assert math.isclose(widen_stop(100.0, 98.0, "long", STOP_WIDEN_FACTOR),
                        96.0, rel_tol=1e-9)
    bars = _bars([
        {"date": "2026-10-01", "open": 100.0, "high": 101.0, "low": 99.0, "close": 100.0, "bar_idx": 0},
        {"date": "2026-10-02", "open": 99.0, "high": 100.5, "low": 97.0, "close": 97.5, "bar_idx": 1},
        {"date": "2026-10-03", "open": 95.0, "high": 97.0, "low": 94.0, "close": 95.0, "bar_idx": 2},
    ])
    rows = _run_with(_trade("98.0"), bars)
    closed = _closed_row(rows)

    assert closed["outlier_excluded"] is False


def test_every_record_carries_outlier_excluded():
    """Non-closed records also emit the field (False)."""
    bars = _bars([
        {"date": "2026-10-01", "open": 100.0, "high": 101.0, "low": 99.0, "close": 100.0, "bar_idx": 0},
        {"date": "2026-10-02", "open": 99.0, "high": 100.5, "low": 97.0, "close": 97.5, "bar_idx": 1},
    ])
    rows = _run_with(_trade("98.0"), bars)
    assert rows, "expected at least one written record"
    for r in rows:
        assert "outlier_excluded" in r, f"missing outlier_excluded on {r.get('stage')} row"


if __name__ == "__main__":
    import inspect
    funcs = [v for k, v in sorted(globals().items())
             if k.startswith("test_") and callable(v)]
    for fn in funcs:
        fn()
        print(f"PASS {fn.__name__}")
    print(f"all {len(funcs)} hostile_fills tests passed")