#!/usr/bin/env python3
"""
track_outcomes.py — HermesForge EPIC-010 (US-068)

Daily job: checks every open paper trade against fresh OHLC bars using
intraday HIGH/LOW (not close-only) so wicks that would have hit a stop or
target are correctly detected, per the user's engine-wide design decision
(2026-07-20).

KNOWN DESIGN TENSION (flagged, not silently resolved): Strategy A's
strategy note (STR-20260719-ma-pullback-fibonacci-entry.md) explicitly
specifies a CLOSE-ONLY primary stop ("Exit on the close, not intraday --
a single intraday pierce is not sufficient"). The user's engine-wide
decision for this paper trading engine is intraday high/low for ALL
strategies, for consistency and wick-realism. This module follows the
user's engine-wide directive for all three strategies (A, B, D) uniformly.
This is a deliberate divergence from Strategy A's documented behavior --
worth reconciling later (candidate for a Pending-Updates note on STR-A,
or an explicit engine-level exception if the user wants Strategy A treated
differently). Not resolved here; flagged for visibility.

Time-stop bar limits (from each scanner's actual coded constant, not the
strategy note's prose -- scanner code is what's live/authoritative):
  Strategy A: MAX_BARS_HELD = 8   (note says "12 trading days" -- code/doc
              mismatch, flagged separately, using code value since it's
              what actually generates the signals)
  Strategy B: MAX_BARS_HELD = 8
  Strategy D: MAX_HOLD = 8

Tie-break rule (both stop and target true on the same bar -- gap-through
scenario): STOP WINS (conservative default), since none of the three
strategies has an explicit tie-break rule coded for this exact case.

Usage:
    python3 track_outcomes.py --dry-run
    python3 track_outcomes.py --test
"""

import sys
import argparse
import pathlib
import datetime
import pandas as pd

REPO_ROOT = pathlib.Path(__file__).parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts" / "validation"))
sys.path.insert(0, str(pathlib.Path(__file__).parent))

import trade_log  # noqa: E402

MARKET_DATA_DIR = pathlib.Path.home() / ".hermes" / "market_data"

MAX_BARS_HELD = {
    "STR-A-ma-pullback-fibonacci": 8,
    "STR-B-macd-histogram-divergence": 8,
    "STR-D-sr-role-reversal": 8,
}


def _load_bars_since(ticker: str, entry_date: str) -> pd.DataFrame:
    """Load cached OHLC bars for ticker strictly after entry_date, chronological order."""
    path = MARKET_DATA_DIR / f"{ticker}.parquet"
    if not path.exists():
        raise FileNotFoundError(f"No cached data for {ticker}")
    df = pd.read_parquet(path)
    df.index = pd.to_datetime(df.index)
    df = df.sort_index()
    entry_ts = pd.to_datetime(entry_date)
    return df[df.index > entry_ts]


def _check_bar(direction: str, high: float, low: float, stop_price: float, target_price: float):
    """
    Returns 'target', 'stop', or None for a single bar's high/low vs.
    stop/target. If both conditions are true (gap-through), STOP WINS.
    """
    if direction == "long":
        target_hit = high >= target_price
        stop_hit = low <= stop_price
    else:  # short
        target_hit = low <= target_price
        stop_hit = high >= stop_price

    if stop_hit:
        return "stop"  # stop wins on tie (conservative default)
    if target_hit:
        return "target"
    return None


def track_trade(trade: dict) -> dict:
    """
    Walk forward through all unchecked bars for one open trade.
    Returns a result dict: {trade_id, action: 'closed'|'still_open'|'error',
    exit_reason (if closed), exit_price, exit_date, bars_held}
    """
    trade_id = trade["trade_id"]
    ticker = trade["ticker"]
    direction = trade["direction"]
    stop_price = float(trade["stop_price"])
    target_price = float(trade["target_price"])
    strategy_id = trade["strategy_id"]
    max_bars = MAX_BARS_HELD.get(strategy_id, 8)

    try:
        bars = _load_bars_since(ticker, trade["entry_date"])
    except FileNotFoundError as e:
        return {"trade_id": trade_id, "action": "error", "error": str(e)}

    if bars.empty:
        return {"trade_id": trade_id, "action": "still_open", "reason": "no new bars yet"}

    for offset, (bar_date, row) in enumerate(bars.iterrows(), start=1):
        high = float(row["high"])
        low = float(row["low"])

        hit = _check_bar(direction, high, low, stop_price, target_price)

        if hit == "stop":
            return {
                "trade_id": trade_id, "action": "closed", "exit_reason": "stop",
                "exit_price": stop_price, "exit_date": str(bar_date)[:10], "bars_held": offset,
            }
        if hit == "target":
            return {
                "trade_id": trade_id, "action": "closed", "exit_reason": "target",
                "exit_price": target_price, "exit_date": str(bar_date)[:10], "bars_held": offset,
            }

        if offset >= max_bars:
            # Time stop: exit at this bar's close
            return {
                "trade_id": trade_id, "action": "closed", "exit_reason": "time",
                "exit_price": float(row["close"]), "exit_date": str(bar_date)[:10], "bars_held": offset,
            }

    return {"trade_id": trade_id, "action": "still_open", "reason": f"{len(bars)} bars checked, no hit yet"}


def run(dry_run: bool = False) -> dict:
    open_trades = trade_log.get_open_trades()
    summary = {
        "open_before": len(open_trades),
        "closed_target": 0, "closed_stop": 0, "closed_time": 0,
        "still_open": 0, "errors": 0, "error_details": [],
    }

    for trade in open_trades:
        result = track_trade(trade)

        if result["action"] == "error":
            summary["errors"] += 1
            summary["error_details"].append(f"{result['trade_id']}: {result['error']}")
            continue

        if result["action"] == "still_open":
            summary["still_open"] += 1
            continue

        # closed
        reason = result["exit_reason"]
        summary[f"closed_{reason}"] += 1
        print(f"  CLOSE ({reason}): {result['trade_id']} @ {result['exit_price']} on {result['exit_date']}")

        if not dry_run:
            trade_log.close_trade(
                result["trade_id"], result["exit_date"], result["exit_price"],
                result["exit_reason"], bars_held=result["bars_held"],
            )

    return summary


def main():
    ap = argparse.ArgumentParser(description="HermesForge paper trade outcome tracker")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    summary = run(dry_run=args.dry_run)
    print(f"\n{'='*60}")
    print(f"SUMMARY: {summary['open_before']} open before -> "
          f"{summary['closed_target']} target, {summary['closed_stop']} stop, "
          f"{summary['closed_time']} time-stop closed, {summary['still_open']} still open, "
          f"{summary['errors']} errors")
    for e in summary["error_details"]:
        print(f"  ERROR: {e}")


# ---------------------------------------------------------------------------
# Unit test — the core "wick" case this story exists for
# ---------------------------------------------------------------------------

def _test():
    import tempfile

    orig_path = trade_log.LOG_PATH
    orig_market_dir = MARKET_DATA_DIR

    trade_log.LOG_PATH = pathlib.Path(tempfile.mktemp(suffix=".csv"))

    tmp_market_dir = pathlib.Path(tempfile.mkdtemp())
    globals()["MARKET_DATA_DIR"] = tmp_market_dir

    try:
        # Synthetic OHLC: entry on day0, target hit intraday on day1 via
        # a wick (high crosses target) even though close stays below target.
        dates = pd.date_range("2026-07-01", periods=5, freq="D")
        df = pd.DataFrame({
            "open":   [100, 101, 108, 107, 106],
            "high":   [102, 116, 109, 108, 107],   # day1 high=116 wicks above target=115
            "low":    [99,  100, 106, 105, 104],
            "close":  [101, 108, 108, 107, 106],   # day1 close=108, BELOW target=115
            "volume": [1000]*5,
        }, index=dates)
        df.to_parquet(tmp_market_dir / "TESTX.parquet")

        tid = trade_log.open_trade({
            "strategy_id": "STR-B-macd-histogram-divergence",
            "ticker": "TESTX", "asset_class": "stock", "data_source": "yfinance",
            "direction": "long", "entry_date": "2026-07-01",
            "entry_price": 100.0, "stop_price": 95.0, "target_price": 115.0,
            "position_size_pct": 1.0,
        })

        open_trades = trade_log.get_open_trades()
        assert len(open_trades) == 1
        trade = open_trades[0]

        result = track_trade(trade)
        assert result["action"] == "closed", f"expected closed, got {result}"
        assert result["exit_reason"] == "target", (
            f"expected target hit via wick (high=116 > target=115), got {result['exit_reason']}"
        )
        assert result["exit_price"] == 115.0
        assert result["bars_held"] == 1, f"should close on day1 (first bar after entry), got {result['bars_held']}"

        print("✅ Wick-detection test passed: high crossed target intraday while close stayed below it")

        # --- Stop-wins-on-tie test: same bar both conditions true ---
        dates2 = pd.date_range("2026-07-01", periods=3, freq="D")
        df2 = pd.DataFrame({
            "open":   [100, 101, 102],
            "high":   [102, 116, 103],   # day1 high wicks above target=115 (target true)
            "low":    [99,  94,  101],   # day1 low ALSO wicks below stop=95 (stop true)
            "close":  [101, 108, 102],
            "volume": [1000]*3,
        }, index=dates2)
        df2.to_parquet(tmp_market_dir / "TESTY.parquet")

        tid2 = trade_log.open_trade({
            "strategy_id": "STR-B-macd-histogram-divergence",
            "ticker": "TESTY", "asset_class": "stock", "data_source": "yfinance",
            "direction": "long", "entry_date": "2026-07-01",
            "entry_price": 100.0, "stop_price": 95.0, "target_price": 115.0,
            "position_size_pct": 1.0,
        })
        trade2 = [t for t in trade_log.get_open_trades() if t["trade_id"] == tid2][0]
        result2 = track_trade(trade2)
        assert result2["exit_reason"] == "stop", f"expected stop-wins-on-tie, got {result2['exit_reason']}"
        print("✅ Stop-wins-on-tie test passed")

        print("\n✅ All track_outcomes.py unit tests passed")

    finally:
        trade_log.LOG_PATH = orig_path
        globals()["MARKET_DATA_DIR"] = orig_market_dir


if __name__ == "__main__":
    if "--test" in sys.argv:
        _test()
    else:
        main()
