#!/usr/bin/env python3
"""
phase1b_t1_01_hostile.py — Hostile Phase 1B: STR-T1-01 Outside Day Key Reversal (Stocks)

Frozen hostile fill rules (same as STR-Q):
  1. Fill at t+1 open (cannot fill on signal bar)
  2. Taker fee 0.1% per side (0.2% round-trip)
  3. Stops: fill at WORST print on crossing bar (bar low for longs)
  4. Targets: must trade THROUGH level (bar high > target, not ≥)
  5. Time stop: 10 trading days, fill at close + taker fee

Output: hostile_fill_report_t1_01.jsonl — never touches trades.csv or journal.

Usage:
    python3 phase1b_t1_01_hostile.py
    python3 phase1b_t1_01_hostile.py --force   # rescore from scratch
"""

import sys
import json
import argparse
import pathlib
import datetime
import pandas as pd
import numpy as np

REPO_ROOT = pathlib.Path(__file__).parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts" / "scanners"))
sys.path.insert(0, str(REPO_ROOT / "scripts" / "validation"))
sys.path.insert(0, str(REPO_ROOT / "scripts" / "paper_trading"))

from scanner_t1_01_outside_day import scan_ticker, ATR_PERIOD, TIME_STOP_BARS

STRATEGY_ID = "STR-T1-01-outside-day-key-reversal"
TAKER_FEE_BPS = 10          # 0.1% per side
MAX_BARS_HELD = TIME_STOP_BARS  # 10 trading days

REPORT_PATH = pathlib.Path(__file__).parent / "hostile_fill_report_t1_01.jsonl"
CACHE_DIR = pathlib.Path.home() / ".hermes" / "market_data"

# Focus universe for stocks
FOCUS_TICKERS = [
    "AAPL","MSFT","NVDA","AMZN","GOOGL","META","TSLA","AVGO","ORCL","AMD",
    "JPM","BAC","GS","MS","WFC","BLK","SCHW","AXP",
    "LLY","UNH","JNJ","ABBV","MRK","TMO",
    "HD","MCD","NKE","COST","WMT","PG","KO",
    "XOM","CVX","COP","SLB","EOG",
    "CAT","DE","BA","GE","HON","RTX","LMT","UPS",
    "QCOM","TXN","MU","INTC","AMAT",
    "CRM","ADBE","NOW","PANW","CRWD",
    "NFLX","CSCO","IBM","UBER","ABNB","PYPL",
    "V","MA","PFE","CVS","SPY","QQQ","IWM",
]


# ── Hostile fill rules (frozen — same as STR-Q) ────────────────────────────

def apply_taker_fee(price: float) -> float:
    """Deduct taker fee from fill price. Always costs the trader."""
    fee_rate = TAKER_FEE_BPS / 10_000
    return round(price * (1 + fee_rate), 6)


def worst_print(bar_low: float, bar_high: float, direction: str) -> float:
    """Return worst bar print: low for longs (selling stop), high for shorts."""
    return bar_low if direction == "long" else bar_high


def trades_through_target(bar_high: float, bar_low: float, target: float, direction: str) -> bool:
    """Limit target fill: must trade THROUGH, not just touch.
    Long exit (sell limit): bar high must be STRICTLY above target.
    Short exit (buy limit): bar low must be STRICTLY below target."""
    if direction == "long":
        return bar_high > target
    return bar_low < target


def bar_touches_stop(bar_low: float, bar_high: float, stop: float) -> bool:
    """Stop trigger: bar range touches stop level."""
    return bar_low <= stop <= bar_high


# ── Hostile exit simulation ──────────────────────────────────────────────

def simulate_hostile_exit(signal: dict, df: pd.DataFrame) -> dict:
    """Re-simulate exit with hostile fill rules for a single signal.

    The scanner already uses t+1 open for entry. We:
    1. Apply taker fee to entry price
    2. Scan bars from entry_idx+1 onward for exits
    3. Stop: worst print + fee
    4. Target: trade-through required + fee
    5. Time: close of time-stop bar + fee

    Args:
        signal: scanner output dict with all fields
        df: full OHLC dataframe for this ticker

    Returns: dict with hostile exit fields + comparison
    """
    direction = signal["direction"]
    ticker = signal["ticker"]

    # Find signal bar index in dataframe
    signal_date = signal["date"]
    df_idx = pd.to_datetime(df.index)
    matches = df_idx == signal_date
    if not matches.any():
        return {"error": f"signal date {signal_date} not found in df"}
    signal_bar_i = int(np.where(matches)[0][0])

    # Entry at t+1 open (matching scanner convention)
    entry_idx = signal_bar_i + 1
    if entry_idx >= len(df):
        return {"error": "no t+1 bar available"}
    entry_bar = df.iloc[entry_idx]
    paper_entry = float(entry_bar["open"])
    hostile_entry = apply_taker_fee(paper_entry)

    # Scanner-computed stop/target
    paper_stop = float(signal["stop_price"])
    paper_target = float(signal["target_price"])
    risk = abs(paper_entry - paper_stop)

    if risk <= 0:
        return {"error": "zero risk"}

    # Scan forward for exit
    t1_exited = False
    hostile_exit = None
    hostile_reason = None
    hostile_date = None
    hostile_bars = 0

    t1_target = paper_entry + (1.5 * risk) if direction == "long" else paper_entry - (1.5 * risk)

    for j in range(entry_idx + 1, min(entry_idx + MAX_BARS_HELD + 1, len(df))):
        bar = df.iloc[j]
        bar_low = float(bar["low"])
        bar_high = float(bar["high"])
        bars_from_entry = j - entry_idx

        # 1. Stop: worst print on crossing bar
        if bar_touches_stop(bar_low, bar_high, paper_stop):
            wp = worst_print(bar_low, bar_high, direction)
            hostile_exit = apply_taker_fee(wp)
            hostile_reason = "stop"
            hostile_date = str(df.index[j])[:10]
            hostile_bars = bars_from_entry
            break

        # 2. T1 partial check (same 50/50 split as Phase 1A)
        if not t1_exited:
            if direction == "long" and bar_high >= t1_target:
                t1_exited = True
            elif direction == "short" and bar_low <= t1_target:
                t1_exited = True

        # 3. T2 target: trade-through required
        if t1_exited and trades_through_target(bar_high, bar_low, paper_target, direction):
            hostile_exit = apply_taker_fee(paper_target)
            hostile_reason = "target"
            hostile_date = str(df.index[j])[:10]
            hostile_bars = bars_from_entry
            break

    # Time stop
    if hostile_exit is None:
        time_idx = min(entry_idx + MAX_BARS_HELD, len(df) - 1)
        time_bar = df.iloc[time_idx]
        time_close = float(time_bar["close"])
        if t1_exited:
            hostile_exit = apply_taker_fee((t1_target + time_close) / 2)
        else:
            hostile_exit = apply_taker_fee(time_close)
        hostile_reason = "time"
        hostile_date = str(df.index[time_idx])[:10]
        hostile_bars = time_idx - entry_idx

    # Compute R-multiples
    if direction == "long":
        paper_r = (float(signal["exit_price"]) - paper_entry) / risk
        hostile_r = (hostile_exit - paper_entry) / risk  # paper entry for risk basis
    else:
        paper_r = (paper_entry - float(signal["exit_price"])) / risk
        hostile_r = (paper_entry - hostile_exit) / risk

    return {
        "ticker": ticker,
        "signal_date": signal_date,
        "direction": direction,
        "paper_entry": round(paper_entry, 4),
        "hostile_entry": round(hostile_entry, 4),
        "stop_price": round(paper_stop, 4),
        "target_price": round(paper_target, 4),
        "paper_exit": round(float(signal["exit_price"]), 4),
        "paper_exit_reason": signal["exit_reason"],
        "paper_r": round(paper_r, 4),
        "hostile_exit": round(hostile_exit, 4),
        "hostile_reason": hostile_reason,
        "hostile_date": hostile_date,
        "hostile_bars": hostile_bars,
        "hostile_r": round(hostile_r, 4),
        "delta_r": round(hostile_r - paper_r, 4),
        "risk": round(risk, 4),
        "subperiod": signal.get("subperiod", "unknown"),
    }


# ── Report I/O ──────────────────────────────────────────────────────────

def read_existing_keys() -> set:
    keys = set()
    if REPORT_PATH.exists():
        try:
            with open(REPORT_PATH) as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        r = json.loads(line)
                        keys.add(f"{r.get('ticker','')}|{r.get('signal_date','')}")
                    except json.JSONDecodeError:
                        pass
        except Exception:
            pass
    return keys


def append_report(record: dict, existing_keys: set) -> bool:
    key = f"{record.get('ticker','')}|{record.get('signal_date','')}"
    if key in existing_keys:
        return False
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(REPORT_PATH, "a") as f:
        f.write(json.dumps(record, default=str) + "\n")
    existing_keys.add(key)
    return True


# ── Main ────────────────────────────────────────────────────────────────

def run(force: bool = False) -> dict:
    if force and REPORT_PATH.exists():
        REPORT_PATH.unlink()
        print("  (force: cleared existing report)")

    existing_keys = set() if force else read_existing_keys()

    # Load data
    data = {}
    for t in FOCUS_TICKERS:
        p = CACHE_DIR / f"{t}.parquet"
        if p.exists():
            df = pd.read_parquet(p)
            if len(df) > 200:
                data[t] = df
    print(f"Loaded {len(data)} stock tickers")

    # Scan for all signals
    all_signals = []
    for t, df in data.items():
        try:
            sigs = scan_ticker(df, t)
            all_signals.extend(sigs)
        except Exception:
            pass
    print(f"Phase 1A signals: {len(all_signals)}")

    if not all_signals:
        return {"error": "no signals"}

    # Run hostile exit simulation
    results = []
    for sig in all_signals:
        ticker = sig["ticker"]
        df = data.get(ticker)
        if df is None:
            continue
        try:
            r = simulate_hostile_exit(sig, df)
            if "error" not in r:
                append_report(r, existing_keys)
                results.append(r)
        except Exception as e:
            pass

    if not results:
        return {"error": "no hostile results produced"}

    df_r = pd.DataFrame(results)

    # Aggregate stats
    paper_avg_r = float(df_r["paper_r"].mean())
    hostile_avg_r = float(df_r["hostile_r"].mean())
    paper_wr = float((df_r["paper_r"] > 0).mean()) * 100
    hostile_wr = float((df_r["hostile_r"] > 0).mean()) * 100
    paper_sum_r = float(df_r["paper_r"].sum())
    hostile_sum_r = float(df_r["hostile_r"].sum())
    delta_sum = float(df_r["delta_r"].sum())
    avg_delta = float(df_r["delta_r"].mean())

    # Sub-period breakdown
    subperiods = {}
    for sp in df_r["subperiod"].unique():
        sp_data = df_r[df_r["subperiod"] == sp]
        if len(sp_data) >= 3:
            subperiods[sp] = {
                "count": len(sp_data),
                "paper_r": round(float(sp_data["paper_r"].mean()), 3),
                "hostile_r": round(float(sp_data["hostile_r"].mean()), 3),
            }

    # Exit reason comparison
    exit_comparison = {}
    for reason in ["stop", "target", "time"]:
        paper_n = len(df_r[df_r["paper_exit_reason"] == reason])
        hostile_n = len(df_r[df_r["hostile_reason"] == reason])
        if paper_n > 0 or hostile_n > 0:
            exit_comparison[reason] = {"paper": paper_n, "hostile": hostile_n}

    return {
        "strategy": STRATEGY_ID,
        "total_trades": len(results),
        "records_written": len(results),
        "paper_avg_r": round(paper_avg_r, 3),
        "hostile_avg_r": round(hostile_avg_r, 3),
        "paper_win_rate": round(paper_wr, 1),
        "hostile_win_rate": round(hostile_wr, 1),
        "paper_sum_r": round(paper_sum_r, 3),
        "hostile_sum_r": round(hostile_sum_r, 3),
        "avg_delta_r": round(avg_delta, 4),
        "total_delta_r": round(delta_sum, 3),
        "subperiods": subperiods,
        "exit_comparison": exit_comparison,
        "hostile_rules": {
            "entry": "t+1 open + 0.1% taker fee",
            "stop": "worst print on crossing bar + 0.1% taker fee",
            "target": "trade-through required + 0.1% taker fee",
            "time_stop": f"{MAX_BARS_HELD} bars, close + 0.1% taker fee",
            "taker_fee_bps": TAKER_FEE_BPS,
            "round_trip_bps": TAKER_FEE_BPS * 2,
        },
    }


def main():
    ap = argparse.ArgumentParser(description="Hostile Phase 1B — STR-T1-01 stocks")
    ap.add_argument("--force", action="store_true", help="Clear report and rescore")
    ap.add_argument("--json", action="store_true", help="JSON output")
    args = ap.parse_args()

    print(f"\n{'='*65}")
    print(f"Hostile Phase 1B: {STRATEGY_ID}")
    print(f"  Rules: {TAKER_FEE_BPS/100:.1f}% taker fee/side, worst-print stops,")
    print(f"         trade-through targets, {MAX_BARS_HELD}-bar time stop")
    print(f"  Output: {REPORT_PATH}")
    print(f"{'='*65}\n")

    summary = run(force=args.force)

    if "error" in summary:
        print(f"ERROR: {summary['error']}")
        return

    print(f"\n{'='*65}")
    print(f"PHASE 1B RESULTS — {STRATEGY_ID}")
    print(f"{'='*65}")
    print(f"  Total trades scored:   {summary['total_trades']}")
    print(f"  Paper R (avg):          {summary['paper_avg_r']:+.3f}")
    print(f"  Hostile R (avg):        {summary['hostile_avg_r']:+.3f}")
    print(f"  Delta R (avg):          {summary['avg_delta_r']:+.4f}")
    print(f"  Paper Win Rate:         {summary['paper_win_rate']:.1f}%")
    print(f"  Hostile Win Rate:       {summary['hostile_win_rate']:.1f}%")
    print(f"  Paper Sum R:            {summary['paper_sum_r']:+.3f}")
    print(f"  Hostile Sum R:          {summary['hostile_sum_r']:+.3f}")
    print(f"  Total Delta R:          {summary['total_delta_r']:+.3f}")
    print(f"\n  Exit Reason Comparison:")
    for reason, counts in summary["exit_comparison"].items():
        delta = counts["hostile"] - counts["paper"]
        print(f"    {reason}: paper={counts['paper']} → hostile={counts['hostile']} (Δ{delta:+d})")
    if summary.get("subperiods"):
        print(f"\n  Sub-periods:")
        for sp, s in sorted(summary["subperiods"].items()):
            print(f"    {sp}: n={s['count']}, paper R={s['paper_r']:+.3f}, hostile R={s['hostile_r']:+.3f}")

    if args.json:
        print(f"\n--- JSON ---")
        print(json.dumps(summary, indent=2, default=str))

    print(f"\n  Report: {REPORT_PATH} ({summary['records_written']} records)")


if __name__ == "__main__":
    main()