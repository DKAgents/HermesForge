#!/usr/bin/env python3
"""
run_phase1a_v3_us115.py — HermesForge US-115 Phase 1A v3 Re-validation

Runs the 10 market_structure-modified scanners across the full stock universe
(529 tickers), saves results as v3 CSVs (structure-based entry/stop/target).

Usage:
    python3 ~/HermesForge/scripts/validation/run_phase1a_v3_us115.py [--scanner STR_ID]
    python3 ~/HermesForge/scripts/validation/run_phase1a_v3_us115.py --scanner STR-X  # single scanner test

Scanners: X, Z, AA, AC, AD, AE, AF, Y, R, B
"""

import os
import sys
import time
import pathlib
import argparse
import pandas as pd
import numpy as np
import traceback

REPO_ROOT = pathlib.Path(__file__).parent.parent.parent
RESULTS_DIR = REPO_ROOT / "scripts" / "validation" / "results"
sys.path.insert(0, str(REPO_ROOT / "scripts" / "validation"))
sys.path.insert(0, str(REPO_ROOT / "scripts" / "validation" / "scanners"))

from universe import get_universe

# ── Scanner imports ──────────────────────────────────────────────────────────
from scanners.scanner_x_parabolic_sar import run_backtest as bt_x
from scanners.scanner_z_stochastic import run_backtest as bt_z
from scanners.scanner_aa_williams_r import run_backtest as bt_aa
from scanners.scanner_ac_cci import run_backtest as bt_ac
from scanners.scanner_ad_keltner import run_backtest as bt_ad
from scanners.scanner_ae_4week_rule import run_backtest as bt_ae
from scanners.scanner_af_candlestick import run_backtest as bt_af
from scanners.scanner_y_adx_dmi import run_backtest as bt_y
from scanners.scanner_r_alligator import run_backtest as bt_r

# STR-B uses a different interface — import scan directly and wrap it
from scanners.scanner_b_macd_divergence import scan as scan_b
# Also need the exit simulation from B's internal helpers
from scanners import scanner_b_macd_divergence as scanner_b_mod


def run_backtest_b(df: pd.DataFrame, ticker: str, long_only: bool = False) -> list:
    """Adapter: wraps STR-B's scan() into HermesForge standard trade output."""
    if "subperiod" not in df.columns:
        df = df.copy()
        df["subperiod"] = df.index.to_period("Q").astype(str)
    signals = scan_b(df, ticker)
    # scan_b already embeds exit_price, exit_reason, r_multiple, bars_held
    # We need to map to standard columns
    trades = []
    for sig in signals:
        # Skip short signals if long_only
        if long_only and sig.get("direction") == "short":
            continue
        trades.append({
            "symbol": sig.get("ticker", ticker),
            "strategy": sig.get("strategy_id", "STR-B-macd-divergence"),
            "direction": sig["direction"],
            "date": sig["date"],
            "entry_price": sig["entry_price"],
            "stop_price": sig["stop_price"],
            "target_price": sig["target_price"],
            "exit_type": sig.get("exit_reason", "time"),
            "exit_price": sig["exit_price"],
            "bars_held": sig["bars_held"],
            "r_multiple": sig["r_multiple"],
            "signal_type": sig.get("signal_bar_index", ""),
        })
    return trades


SCANNER_MAP = {
    "X":  ("STR-X-stocks-phase1a-v3",  bt_x),
    "Z":  ("STR-Z-stocks-phase1a-v3",  bt_z),
    "AA": ("STR-AA-stocks-phase1a-v3", bt_aa),
    "AC": ("STR-AC-stocks-phase1a-v3", bt_ac),
    "AD": ("STR-AD-stocks-phase1a-v3", bt_ad),
    "AE": ("STR-AE-stocks-phase1a-v3", bt_ae),
    "AF": ("STR-AF-stocks-phase1a-v3", bt_af),
    "Y":  ("STR-Y-stocks-phase1a-v3",  bt_y),
    "R":  ("STR-R-stocks-phase1a-v3",  bt_r),
    "B":  ("STR-B-stocks-phase1a-v3",  run_backtest_b),
}

DATA_DIR = pathlib.Path.home() / ".hermes" / "market_data"


def run_one_scanner(scanner_key: str, universe: list, asset_type: str = "stock"):
    """Run Phase 1A for one scanner across the full universe."""
    csv_name, bt_fn = SCANNER_MAP[scanner_key]
    strategy_id = csv_name.replace("-v3", "")

    print(f"\n{'='*70}")
    print(f"  {strategy_id} — scanning {len(universe)} stocks...")
    print(f"{'='*70}")

    all_trades = []
    errors = 0
    skipped = 0
    t0 = time.time()

    for i, ticker in enumerate(universe, 1):
        cache_path = DATA_DIR / f"{ticker}.parquet"
        if not cache_path.exists():
            skipped += 1
            continue

        try:
            df = pd.read_parquet(cache_path)
            if "Date" in df.columns:
                df = df.set_index("Date")
            if not isinstance(df.index, pd.DatetimeIndex):
                df.index = pd.to_datetime(df.index)

            # Standardize column names
            df.columns = [c.lower() for c in df.columns]

            long_only = (asset_type == "stock")

            trades = bt_fn(df, ticker, long_only=long_only)

            if trades:
                all_trades.extend(trades)

            if i % 50 == 0:
                elapsed = time.time() - t0
                print(f"    [{i}/{len(universe)}] {ticker} — {len(trades) if trades else 0} trades "
                      f"(total: {len(all_trades)} | {elapsed:.0f}s)")

        except Exception as e:
            errors += 1
            if errors <= 5:
                print(f"    ERROR {ticker}: {e}")
                traceback.print_exc(limit=1, file=sys.stderr)

    elapsed = time.time() - t0

    if not all_trades:
        print(f"  No signals found across {len(universe)} stocks.")
        result_df = pd.DataFrame(columns=[
            "symbol", "strategy", "direction", "date", "entry_price",
            "stop_price", "target_price", "exit_type", "exit_price",
            "bars_held", "r_multiple", "signal_type"
        ])
    else:
        result_df = pd.DataFrame(all_trades)
        std_cols = [
            "symbol", "strategy", "direction", "date", "entry_price",
            "stop_price", "target_price", "exit_type", "exit_price",
            "bars_held", "r_multiple", "signal_type"
        ]
        for c in std_cols:
            if c not in result_df.columns:
                result_df[c] = ""
        result_df = result_df[std_cols]

    # Save
    out_path = RESULTS_DIR / f"{csv_name}.csv"
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    result_df.to_csv(out_path, index=False)

    # Summary
    n = len(result_df)
    if n > 0:
        win_rate = (result_df["r_multiple"] > 0).mean() * 100
        avg_r = result_df["r_multiple"].mean()
        pos_r = result_df[result_df["r_multiple"] > 0]["r_multiple"].sum()
        neg_r = abs(result_df[result_df["r_multiple"] < 0]["r_multiple"].sum())
        pf = pos_r / neg_r if neg_r > 1e-10 else float('inf')
        print(f"\n  RESULTS for {strategy_id}:")
        print(f"    Total trades: {n}")
        print(f"    Win rate:     {win_rate:.1f}%")
        print(f"    Avg R:        {avg_r:.4f}")
        print(f"    Profit factor: {pf:.3f}")
        print(f"    Errors:       {errors}")
        print(f"    Skipped:      {skipped}")
        print(f"    Time:         {elapsed:.0f}s")
    else:
        print(f"  No trades found for {strategy_id}")

    print(f"  Saved \u2192 {out_path}")
    return result_df


def main():
    parser = argparse.ArgumentParser(description="Run Phase 1A v3 for US-115 structure-based scanners")
    parser.add_argument("--scanner", choices=list(SCANNER_MAP.keys()), help="Run only one scanner")
    parser.add_argument("--subset", type=int, default=0, help="Run on first N tickers only (for testing)")
    args = parser.parse_args()

    universe = get_universe()
    if args.subset > 0:
        universe = universe[:args.subset]

    print(f"Full universe: {len(universe)} stocks")
    print(f"Data cache:    {DATA_DIR}")

    scanners_to_run = [args.scanner] if args.scanner else list(SCANNER_MAP.keys())

    for sk in scanners_to_run:
        run_one_scanner(sk, universe)

    print(f"\n{'='*70}")
    print(f"  ALL DONE. v3 results in {RESULTS_DIR}")
    print(f"{'='*70}")


if __name__ == "__main__":
    main()