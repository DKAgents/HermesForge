#!/usr/bin/env python3
"""
run_phase1a_v2_us114.py — HermesForge US-114 Phase 1A v2 Re-validation

Runs the 9 fixed scanners across the full stock universe (529 tickers),
saves results as v2 CSVs (no contamination from look-ahead bias).

Usage:
    python3 ~/HermesForge/scripts/validation/run_phase1a_v2_us114.py [--scanner STR_ID]

Scanners: S, T, U, V, W, AB, AG, R, AJ
"""

import os
import sys
import time
import pathlib
import argparse
import pandas as pd
import traceback

REPO_ROOT = pathlib.Path(__file__).parent.parent.parent
RESULTS_DIR = REPO_ROOT / "scripts" / "validation" / "results"
sys.path.insert(0, str(REPO_ROOT / "scripts" / "validation"))
sys.path.insert(0, str(REPO_ROOT / "scripts" / "validation" / "scanners"))

from universe import get_universe

# ── Scanner imports ──────────────────────────────────────────────────────────
from scanners.scanner_s_elliott_wave import run_backtest as bt_s
from scanners.scanner_t_head_shoulders import run_backtest as bt_t
from scanners.scanner_u_double_top_bottom import run_backtest as bt_u
from scanners.scanner_v_triangles import run_backtest as bt_v
from scanners.scanner_w_flags_pennants import run_backtest as bt_w
from scanners.scanner_ab_obv_divergence import run_backtest as bt_ab
from scanners.scanner_ag_wedge import run_backtest as bt_ag
from scanners.scanner_r_alligator import run_backtest as bt_r
from scanners.scanner_aj_intermarket import run_backtest as bt_aj
from scanners.scanner_aj_intermarket import fetch_intermarket_data, compute_intermarket_signal

SCANNER_MAP = {
    "S":  ("STR-S-stocks-phase1a-v2",  bt_s),
    "T":  ("STR-T-stocks-phase1a-v2",  bt_t),
    "U":  ("STR-U-stocks-phase1a-v2",  bt_u),
    "V":  ("STR-V-stocks-phase1a-v2",  bt_v),
    "W":  ("STR-W-stocks-phase1a-v2",  bt_w),
    "AB": ("STR-AB-stocks-phase1a-v2", bt_ab),
    "AG": ("STR-AG-stocks-phase1a-v2", bt_ag),
    "R":  ("STR-R-stocks-phase1a-v2",  bt_r),
    "AJ": ("STR-AJ-stocks-phase1a-v2", bt_aj),
}

DATA_DIR = pathlib.Path.home() / ".hermes" / "market_data"


def run_one_scanner(scanner_key: str, universe: list, asset_type: str = "stock"):
    """Run Phase 1A for one scanner across the full universe."""
    csv_name, bt_fn = SCANNER_MAP[scanner_key]
    strategy_id = csv_name.replace("-v2", "")  # e.g. STR-S
    
    print(f"\n{'='*70}")
    print(f"  {strategy_id} — scanning {len(universe)} stocks...")
    print(f"{'='*70}")
    
    # Pre-fetch intermarket data for STR-AJ (avoids 531 API calls)
    intermarket_cache = None
    if scanner_key == "AJ":
        print("    Pre-fetching DXY/TNX intermarket data (one-time)...")
        im_data = fetch_intermarket_data()
        if im_data.get("DXY") is not None and im_data.get("TNX") is not None:
            intermarket_cache = compute_intermarket_signal(im_data["DXY"], im_data["TNX"])
            if intermarket_cache is not None and len(intermarket_cache) > 0:
                print(f"    Intermarket data loaded: {len(intermarket_cache)} rows")
            else:
                print("    WARNING: Intermarket data empty — STR-AJ may produce no signals")
        else:
            print("    WARNING: Could not fetch DXY/TNX — STR-AJ will skip all tickers")
    
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
            
            if scanner_key == "AJ":
                trades = bt_fn(df, ticker, long_only=long_only, intermarket=intermarket_cache)
            else:
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
        # Create empty DataFrame with standard columns
        result_df = pd.DataFrame(columns=[
            "symbol", "strategy", "direction", "date", "entry_price",
            "stop_price", "target_price", "exit_type", "exit_price",
            "bars_held", "r_multiple", "signal_type"
        ])
    else:
        result_df = pd.DataFrame(all_trades)
        # Ensure standard column order
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
        pf = result_df[result_df["r_multiple"] > 0]["r_multiple"].sum() / \
             max(abs(result_df[result_df["r_multiple"] < 0]["r_multiple"].sum()), 1e-10)
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
    
    print(f"  Saved → {out_path}")
    return result_df


def main():
    parser = argparse.ArgumentParser(description="Run Phase 1A v2 for US-114 fixed scanners")
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
    print(f"  ALL DONE. v2 results in {RESULTS_DIR}")
    print(f"{'='*70}")


if __name__ == "__main__":
    main()