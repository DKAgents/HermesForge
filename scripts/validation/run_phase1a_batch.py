#!/usr/bin/env python3
"""
Batch-run Phase 1A for all 13 untested scanners.
Captures signal count + first 10 signals per asset type.
Writes results to /root/HermesForge/04-Strategies/phase1a-results.md
"""
import sys
import os
import importlib
import traceback
from pathlib import Path

STOCK_SYMBOLS = ["SPY", "QQQ", "AAPL", "NVDA", "TSLA", "AMZN", "MSFT", "GOOGL", "META", "AMD", "NFLX", "JPM", "BAC", "XOM", "CVX", "PFE", "UNH", "COST"]
CRYPTO_SYMBOLS = ["BTC", "ETH", "SOL", "AAVE", "ADA", "DOT", "BNB", "LINK"]

SCANNERS_DIR = Path("/root/HermesForge/scripts/validation/scanners")
OUTPUT_PATH = Path("/root/HermesForge/04-Strategies/phase1a-results.md")

SCANNER_NAMES = [
    "scanner_t_head_shoulders",
    "scanner_u_double_top_bottom",
    "scanner_aa_williams_r",
    "scanner_ab_obv_divergence",
    "scanner_ac_cci",
    "scanner_ad_keltner",
    "scanner_ae_4week_rule",
    "scanner_ag_wedge",
    "scanner_ai_seasonal",
    "scanner_aj_intermarket",
    "scanner_x_parabolic_sar",
    "scanner_s_elliott_wave",
    "scanner_r_alligator",
]

def run_one(scanner_name, symbols, asset_type):
    """Import scanner, call run_phase1a, return (df, error_str)."""
    sys.path.insert(0, str(SCANNERS_DIR))
    try:
        mod = importlib.import_module(scanner_name)
    except Exception as e:
        return None, f"import error: {e}"
    finally:
        if str(SCANNERS_DIR) in sys.path:
            sys.path.remove(str(SCANNERS_DIR))

    try:
        df = mod.run_phase1a(symbols, asset_type)
        return df, None
    except Exception as e:
        return None, f"runtime error: {e}\n{traceback.format_exc(limit=3)}"


def format_signals(df, max_rows=10):
    """Extract ticker, direction, entry_price from DataFrame."""
    if df is None or len(df) == 0:
        return 0, []
    
    rows = []
    for _, row in df.head(max_rows).iterrows():
        ticker = row.get("ticker", "?")
        direction = row.get("direction", "?")
        entry = row.get("entry_price", "?")
        if isinstance(entry, float):
            entry = f"{entry:.4f}"
        rows.append((ticker, direction, entry))
    return len(df), rows


def main():
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    lines = []
    lines.append("# Phase 1A Scanner Results")
    lines.append("")
    lines.append(f"**Date**: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M UTC')}")
    lines.append(f"**Stock symbols**: {len(STOCK_SYMBOLS)} symbols")
    lines.append(f"**Crypto symbols**: {len(CRYPTO_SYMBOLS)} symbols")
    lines.append("")
    lines.append("---")
    lines.append("")
    
    for i, name in enumerate(SCANNER_NAMES, 1):
        print(f"\n{'='*60}")
        print(f"[{i}/13] {name}")
        print(f"{'='*60}")
        
        lines.append(f"## {i}. {name}")
        lines.append("")
        
        # --- Stocks ---
        print(f"  Stocks ({len(STOCK_SYMBOLS)} symbols)...")
        df, err = run_one(name, STOCK_SYMBOLS, "stock")
        if err:
            lines.append(f"**Status**: error")
            lines.append(f"```\n{err}\n```")
            lines.append("")
            print(f"    ERROR: {err.split(chr(10))[0]}")
        else:
            count, first10 = format_signals(df)
            lines.append(f"**Status**: ran")
            lines.append(f"**Asset**: stocks")
            lines.append(f"**Signals found**: {count}")
            if first10:
                lines.append("")
                lines.append("| Ticker | Direction | Entry Price |")
                lines.append("|--------|-----------|-------------|")
                for ticker, direction, entry in first10:
                    lines.append(f"| {ticker} | {direction} | {entry} |")
            lines.append("")
            print(f"    {count} signals")
        
        # --- Crypto ---
        print(f"  Crypto ({len(CRYPTO_SYMBOLS)} symbols)...")
        df, err = run_one(name, CRYPTO_SYMBOLS, "crypto")
        if err:
            lines.append(f"**Status**: error")
            lines.append(f"**Asset**: crypto")
            lines.append(f"```\n{err}\n```")
            lines.append("")
            print(f"    ERROR: {err.split(chr(10))[0]}")
        else:
            count, first10 = format_signals(df)
            lines.append(f"**Status**: ran")
            lines.append(f"**Asset**: crypto")
            lines.append(f"**Signals found**: {count}")
            if first10:
                lines.append("")
                lines.append("| Ticker | Direction | Entry Price |")
                lines.append("|--------|-----------|-------------|")
                for ticker, direction, entry in first10:
                    lines.append(f"| {ticker} | {direction} | {entry} |")
            lines.append("")
            print(f"    {count} signals")
        
        lines.append("---")
        lines.append("")
        
        # Flush partial results
        OUTPUT_PATH.write_text("\n".join(lines))
    
    print(f"\nDone. Results written to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()