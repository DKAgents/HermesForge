#!/usr/bin/env python3
"""
compute_strategy_regime.py — Strategy-Regime Performance Heatmap

Backfills regime tags for historical trades (since trades.csv has no
regime columns), then computes a strategy × regime performance matrix
showing which strategies perform best in which market regimes.

Backfill uses historical VIX, DXY, and Fear & Greed data to reconstruct
what the regime was on each trade's entry date.

Usage:
    python3 compute_strategy_regime.py               # backfill + heatmap
    python3 compute_strategy_regime.py --backfill     # backfill only
    python3 compute_strategy_regime.py --heatmap      # heatmap only (needs backfilled data)
    python3 compute_strategy_regime.py --json         # JSON output
"""

import sys
import json
import pathlib
import argparse
import pandas as pd
import numpy as np
from datetime import datetime, timezone

sys.path.insert(0, str(pathlib.Path(__file__).parent))
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / "paper_trading"))
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / "validation"))

TRADES_PATH = pathlib.Path(__file__).parent.parent / "paper_trading" / "trades.csv"
CACHE_DIR = pathlib.Path.home() / ".hermes" / "market_data" / "regime_backfill"


def _fetch_historical_vix() -> pd.DataFrame:
    """Fetch historical VIX data via yfinance."""
    import yfinance as yf
    vix = yf.Ticker("^VIX")
    hist = vix.history(period="2y")
    if hist.empty:
        return pd.DataFrame()
    hist.index = hist.index.tz_localize(None)
    return hist[["Close"]].rename(columns={"Close": "vix"})


def _fetch_historical_dxy() -> pd.DataFrame:
    """Fetch historical DXY data via yfinance."""
    import yfinance as yf
    dxy = yf.Ticker("DX-Y.NYB")
    hist = dxy.history(period="2y")
    if hist.empty:
        return pd.DataFrame()
    hist.index = hist.index.tz_localize(None)
    return hist[["Close"]].rename(columns={"Close": "dxy"})


def _fetch_historical_fg() -> pd.DataFrame:
    """Fetch historical Fear & Greed data from alternative.me."""
    import requests
    url = "https://api.alternative.me/fng/?limit=0&format=json"
    try:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        data = resp.json().get("data", [])
        if not data:
            return pd.DataFrame()
        df = pd.DataFrame(data)
        df["timestamp"] = pd.to_datetime(df["timestamp"].astype(int), unit="s")
        df["fear_greed"] = df["value"].astype(int)
        df = df.set_index("timestamp")[["fear_greed"]]
        df.index = df.index.tz_localize(None)
        return df
    except Exception as e:
        print(f"  Warning: F&G fetch failed: {e}")
        return pd.DataFrame()


def _classify_vix_regime(vix_val: float) -> str:
    """Classify VIX into regime."""
    if vix_val < 15:
        return "risk_on"
    elif vix_val < 20:
        return "normal"
    elif vix_val < 28:
        return "elevated"
    else:
        return "risk_off"


def _classify_crypto_regime(fg_val: int) -> str:
    """Classify crypto regime from Fear & Greed."""
    if fg_val > 75:
        return "greed"
    elif fg_val > 55:
        return "risk_on"
    elif fg_val > 45:
        return "neutral"
    elif fg_val > 25:
        return "fear"
    else:
        return "risk_off"


def _classify_overall(stock_regime: str, crypto_regime: str) -> str:
    """Classify overall regime."""
    if stock_regime == "risk_off" or crypto_regime == "risk_off":
        return "risk_off"
    elif stock_regime == "risk_on" and crypto_regime in ("risk_on", "neutral"):
        return "risk_on"
    elif stock_regime in ("elevated",) or crypto_regime in ("fear", "greed"):
        return "caution"
    else:
        return "neutral"


def backfill_regime_tags() -> pd.DataFrame:
    """
    Backfill regime tags for all trades in trades.csv.
    
    Adds columns: regime_stock, regime_crypto, regime_overall, vix, dxy, fear_greed
    """
    if not TRADES_PATH.exists():
        print("  No trades.csv found")
        return pd.DataFrame()
    
    df = pd.read_csv(TRADES_PATH)
    
    # Check if already backfilled
    regime_cols = ["regime_stock", "regime_crypto", "regime_overall", "vix", "dxy", "fear_greed"]
    has_regime = all(c in df.columns for c in regime_cols)
    
    if has_regime and df["regime_overall"].notna().sum() > 0:
        print(f"  Already backfilled ({df['regime_overall'].notna().sum()} trades tagged)")
        return df
    
    print("  Fetching historical data for regime backfill...")
    
    # Fetch historical data
    vix_hist = _fetch_historical_vix()
    dxy_hist = _fetch_historical_dxy()
    fg_hist = _fetch_historical_fg()
    
    print(f"  VIX: {len(vix_hist)} bars, DXY: {len(dxy_hist)} bars, F&G: {len(fg_hist)} bars")
    
    # Add regime columns if missing
    for col in regime_cols:
        if col not in df.columns:
            df[col] = None
    
    # Parse entry dates
    df["entry_date"] = pd.to_datetime(df["entry_date"], errors="coerce")
    
    # Backfill each trade
    tagged = 0
    for idx, row in df.iterrows():
        entry_date = row["entry_date"]
        if pd.isna(entry_date):
            continue
        
        # Normalize to date (no timezone)
        entry_date = entry_date.tz_localize(None) if entry_date.tzinfo else entry_date
        
        # Find closest VIX value
        vix_val = None
        if not vix_hist.empty:
            vix_subset = vix_hist.loc[:entry_date]
            if not vix_subset.empty:
                vix_val = float(vix_subset.iloc[-1]["vix"])
        
        # Find closest DXY value
        dxy_val = None
        if not dxy_hist.empty:
            dxy_subset = dxy_hist.loc[:entry_date]
            if not dxy_subset.empty:
                dxy_val = float(dxy_subset.iloc[-1]["dxy"])
        
        # Find closest F&G value
        fg_val = None
        if not fg_hist.empty:
            fg_subset = fg_hist.loc[:entry_date]
            if not fg_subset.empty:
                fg_val = int(fg_subset.iloc[-1]["fear_greed"])
        
        # Classify regimes
        stock_regime = _classify_vix_regime(vix_val) if vix_val else "unknown"
        crypto_regime = _classify_crypto_regime(fg_val) if fg_val is not None else "unknown"
        overall = _classify_overall(stock_regime, crypto_regime)
        
        # Set values
        df.at[idx, "regime_stock"] = stock_regime
        df.at[idx, "regime_crypto"] = crypto_regime
        df.at[idx, "regime_overall"] = overall
        df.at[idx, "vix"] = vix_val
        df.at[idx, "dxy"] = dxy_val
        df.at[idx, "fear_greed"] = fg_val
        
        tagged += 1
    
    # Save backfilled trades
    df.to_csv(TRADES_PATH, index=False)
    print(f"  Backfilled {tagged} trades with regime tags → saved to {TRADES_PATH}")
    
    return df


def compute_strategy_regime_heatmap() -> dict:
    """
    Compute strategy × regime performance matrix.
    
    For each strategy × regime combination, compute:
    - trade count
    - win rate
    - avg R multiple
    - total R
    
    Returns:
    {
        "matrix": {strategy: {regime: {count, win_rate, avg_r, total_r}}},
        "best_combos": [...],  # top performing strategy-regime pairs
        "worst_combos": [...],
        "regime_counts": {regime: int},
        "strategy_counts": {strategy: int},
    }
    """
    if not TRADES_PATH.exists():
        return {"matrix": {}, "note": "no trades.csv"}
    
    df = pd.read_csv(TRADES_PATH)
    
    # Check if regime columns exist
    if "regime_overall" not in df.columns or df["regime_overall"].isna().all():
        # Need to backfill first
        df = backfill_regime_tags()
    
    # Filter to closed trades with regime data
    closed = df[df["status"] == "closed"].copy()
    closed = closed[closed["regime_overall"].notna() & (closed["regime_overall"] != "")]
    
    if len(closed) < 3:
        return {"matrix": {}, "note": f"only {len(closed)} closed trades with regime tags"}
    
    closed["r_multiple"] = pd.to_numeric(closed["r_multiple"], errors="coerce")
    
    # Build matrix
    matrix = {}
    regimes = ["risk_on", "neutral", "caution", "risk_off", "complacent"]
    strategies = sorted(closed["strategy_id"].unique())
    
    for strat in strategies:
        matrix[strat] = {}
        strat_trades = closed[closed["strategy_id"] == strat]
        
        for regime in regimes:
            regime_trades = strat_trades[strat_trades["regime_overall"] == regime]
            n = len(regime_trades)
            
            if n == 0:
                matrix[strat][regime] = {"count": 0, "win_rate": None, "avg_r": None, "total_r": None}
            else:
                wins = (regime_trades["r_multiple"] > 0).sum()
                avg_r = float(regime_trades["r_multiple"].mean())
                total_r = float(regime_trades["r_multiple"].sum())
                matrix[strat][regime] = {
                    "count": n,
                    "win_rate": round(wins / n * 100, 1),
                    "avg_r": round(avg_r, 2),
                    "total_r": round(total_r, 2),
                }
    
    # Find best/worst combos (min 2 trades)
    combos = []
    for strat in strategies:
        for regime in regimes:
            cell = matrix[strat][regime]
            if cell["count"] >= 2:
                combos.append({
                    "strategy": strat,
                    "regime": regime,
                    "count": cell["count"],
                    "win_rate": cell["win_rate"],
                    "avg_r": cell["avg_r"],
                    "total_r": cell["total_r"],
                })
    
    best_combos = sorted(combos, key=lambda x: x["avg_r"], reverse=True)[:5]
    worst_combos = sorted(combos, key=lambda x: x["avg_r"])[:5]
    
    # Regime distribution
    regime_counts = {r: int((closed["regime_overall"] == r).sum()) for r in regimes}
    strategy_counts = {s: int((closed["strategy_id"] == s).sum()) for s in strategies}
    
    return {
        "matrix": matrix,
        "best_combos": best_combos,
        "worst_combos": worst_combos,
        "regime_counts": regime_counts,
        "strategy_counts": strategy_counts,
        "total_closed": len(closed),
    }


def get_strategy_regime_summary() -> dict:
    """Get a concise summary for the regime filter / daily briefing."""
    heatmap = compute_strategy_regime_heatmap()
    
    if heatmap.get("note"):
        return {"available": False, "note": heatmap["note"]}
    
    return {
        "available": True,
        "total_closed": heatmap.get("total_closed", 0),
        "regime_counts": heatmap.get("regime_counts", {}),
        "best_combo": heatmap["best_combos"][0] if heatmap.get("best_combos") else None,
        "worst_combo": heatmap["worst_combos"][0] if heatmap.get("worst_combos") else None,
    }


def print_heatmap_text(data: dict):
    """Print a text-based heatmap table."""
    matrix = data.get("matrix", {})
    if not matrix:
        print(f"  {data.get('note', 'No data')}")
        return
    
    regimes = ["risk_on", "neutral", "caution", "risk_off", "complacent"]
    regime_emoji = {"risk_on": "🟢", "neutral": "⚪", "caution": "🟡", "risk_off": "🔴", "complacent": "⚠️"}
    
    print(f"\n📊 **Strategy × Regime Performance Heatmap**")
    print(f"   {data['total_closed']} closed trades\n")
    
    # Header
    print(f"{'Strategy':<12}", end="")
    for r in regimes:
        print(f" {regime_emoji.get(r,'')}{r:>12}", end="")
    print()
    print("-" * 80)
    
    # Rows
    for strat, cells in sorted(matrix.items()):
        print(f"{strat:<12}", end="")
        for r in regimes:
            cell = cells.get(r, {})
            n = cell.get("count", 0)
            if n == 0:
                print(f" {'—':>13}", end="")
            else:
                wr = cell.get("win_rate", 0)
                avg_r = cell.get("avg_r", 0)
                r_color = "✅" if avg_r > 0 else "❌"
                print(f" {r_color}{n}tr WR{wr:>4.0f}% {avg_r:>+5.1f}R", end="")
        print()
    
    print()
    
    # Best/worst
    if data.get("best_combos"):
        print("✅ **Best Combos (min 2 trades):**")
        for c in data["best_combos"][:3]:
            print(f"  {c['strategy']} @ {c['regime']}: {c['count']} trades, "
                  f"WR={c['win_rate']}%, avg={c['avg_r']:+.2f}R, total={c['total_r']:+.2f}R")
    
    if data.get("worst_combos"):
        print("\n❌ **Worst Combos (min 2 trades):**")
        for c in data["worst_combos"][:3]:
            print(f"  {c['strategy']} @ {c['regime']}: {c['count']} trades, "
                  f"WR={c['win_rate']}%, avg={c['avg_r']:+.2f}R, total={c['total_r']:+.2f}R")
    
    print(f"\nRegime distribution: {data.get('regime_counts', {})}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Strategy-Regime Performance Heatmap")
    ap.add_argument("--backfill", action="store_true", help="Backfill regime tags only")
    ap.add_argument("--heatmap", action="store_true", help="Heatmap only")
    ap.add_argument("--json", action="store_true", help="JSON output")
    args = ap.parse_args()
    
    if args.backfill:
        df = backfill_regime_tags()
        print(f"\nBackfilled {len(df)} trades")
    elif args.heatmap:
        data = compute_strategy_regime_heatmap()
        if args.json:
            print(json.dumps(data, indent=2, default=str))
        else:
            print_heatmap_text(data)
    else:
        # Full run: backfill + heatmap
        print("Step 1: Backfilling regime tags...")
        backfill_regime_tags()
        print("\nStep 2: Computing heatmap...")
        data = compute_strategy_regime_heatmap()
        if args.json:
            print(json.dumps(data, indent=2, default=str))
        else:
            print_heatmap_text(data)
