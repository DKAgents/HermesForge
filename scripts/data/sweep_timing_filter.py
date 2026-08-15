#!/usr/bin/env python3
"""
sweep_timing_filter.py
======================
HermesForge US-107 — Sweep Timing Filter for Existing Strategies

This module acts as a pre-entry filter for ALL existing strategies.
Before any strategy fires a signal, this filter checks whether a 
liquidity sweep has recently occurred near the signal's entry price.

THREE MODES:

1. REQUIRE_SWEEP (gate): Only allow entry if a recent sweep is detected.
   - Strategy signal is BLOCKED if no sweep found within the lookback window.
   - Use for strategies that suffer from being stopped out before the real move.

2. BOOST_ON_SWEEP (enhancer): If a sweep is detected, boost the signal quality.
   - Signal is allowed regardless, but sweep confirmation adds quality score.
   - Sweep-aligned signals get priority in the daily signal batch.

3. DELAY_UNTIL_SWEEP (wait): Hold the signal and wait for a sweep to confirm.
   - If strategy fires but no sweep yet, mark signal as "waiting for sweep."
   - When a sweep occurs at the relevant level, signal is activated.
   - Max wait time: 5 bars (25 min on 5m, 75 min on 15m).

INTEGRATION:
  Called from capture_signals.py before posting any signal.
  
  result = check_sweep_alignment(symbol, entry_price, direction, asset_type)
  if result['action'] == 'block':
      skip_signal()
  elif result['action'] == 'boost':
      signal.quality += result['boost_amount']
      signal.sweep_confirmed = True
  elif result['action'] == 'wait':
      signal.status = 'pending_sweep'
      signal.sweep_watch_level = result['nearest_level']

Usage:
  from sweep_timing_filter import check_sweep_alignment
  result = check_sweep_alignment('BTC', 63000, 'long', 'crypto')
"""

import os
import sys
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta

MODULE_DIR = Path(__file__).parent
sys.path.insert(0, str(MODULE_DIR))

from detect_liquidity_sweeps import (
    LiquidityLevel, SweepEvent, _compute_atr,
    identify_liquidity_levels, detect_sweep_at_level,
    scan_symbol_for_sweeps,
)

# ── Configuration ────────────────────────────────────────────────────────────

# Mode: 'require', 'boost', or 'delay' (default: boost)
DEFAULT_MODE = "boost"

# How many bars to look back for a sweep (on 5m = 25 bars = ~2 hours)
SWEEP_LOOKBACK_BARS = 25

# Price tolerance: how close the sweep level must be to the signal entry (in ATR)
SWEEP_PROXIMITY_ATR = 2.0

# Minimum quality score for a sweep to count
MIN_SWEEP_QUALITY = 40

# Boost amount added to signal quality when sweep is confirmed
SWEEP_BOOST_AMOUNT = 15

# Max wait time in delay mode (bars)
MAX_WAIT_BARS = 5

# ── US-108: Tiered Sweep Filter Configuration ────────────────────────────────
# Per-strategy sweep filter modes based on Phase 1B v2 confluence study.
# STR-D (weakest baseline, strongest sweep fit) → require mode
# STR-A/B/I (already have internal confirmation) → boost mode
# Premium require tier: only count the strongest sweep level types (PDH/PDL/round_number)

TIERED_MODES = {
    "STR-D": "require",   # Weakest baseline (p=0.435), strongest sweep fit
    "STR-A": "boost",     # Has MA/Fib confirmation internally
    "STR-B": "boost",     # Has MACD divergence confirmation internally
    "STR-I": "boost",     # Has momentum + ATR trailing stop internally
}

# Premium level types — strongest performers in deep backtest
# PDH: 62.5% WR, +1.110R | PDL: 70.4% WR, +2.581R | round_number: 61.6% WR, +0.907R
PREMIUM_LEVEL_TYPES = {"pdh", "pdl", "round_number"}

# Level types to exclude on stocks (poor performers in deep backtest)
# equal_lows: 34.6% WR on stocks (was 67.7% in small sample — overestimated)
EXCLUDED_STOCK_LEVEL_TYPES = {"equal_lows"}

# Level types allowed on crypto (equal_lows performs at +1.648R on crypto)
# No exclusions for crypto — all level types valid


def _get_mode_for_strategy(strategy_id: str) -> str:
    """Determine sweep filter mode based on strategy ID (US-108 tiered approach)."""
    for prefix, mode in TIERED_MODES.items():
        if prefix in strategy_id:
            return mode
    # Default: boost mode for unknown strategies
    return "boost"


def _filter_valid_sweeps(sweeps: list, asset_type: str, strategy_id: str = "",
                         premium_only: bool = False) -> list:
    """
    Filter sweeps based on asset type and tiered filter rules.
    
    US-108:
    - Stocks: exclude equal_lows (34.6% WR, overestimated in small sample)
    - Crypto: all level types valid (equal_lows +1.648R)
    - Premium tier: only PDH/PDL/round_number (strongest performers)
    """
    valid = []
    for s in sweeps:
        if s.quality_score < MIN_SWEEP_QUALITY:
            continue
        if s.confirmation not in ("confirmed", "pending"):
            continue
        
        level_type = getattr(s, 'level_type', '').lower().replace(' ', '_')
        
        # Premium filter: only allow strongest level types
        if premium_only and level_type not in PREMIUM_LEVEL_TYPES:
            continue
        
        # Asset-type exclusions
        if asset_type == "stock" and level_type in EXCLUDED_STOCK_LEVEL_TYPES:
            continue
        
        valid.append(s)
    
    return valid


def check_sweep_alignment(
    symbol: str,
    entry_price: float,
    direction: str,  # 'long' or 'short'
    asset_type: str = "crypto",
    interval: str = "5m",
    mode: str = DEFAULT_MODE,
    strategy_id: str = "",  # US-108: for tiered mode selection
) -> dict:
    """
    Check if a recent liquidity sweep aligns with the proposed trade.
    
    Args:
        symbol: Ticker symbol
        entry_price: Proposed entry price from the strategy
        direction: 'long' or 'short'
        asset_type: 'crypto' or 'stock'
        interval: Intraday interval to check
        mode: 'require', 'boost', or 'delay' (overridden by tiered mode if strategy_id given)
        strategy_id: Strategy ID for US-108 tiered mode selection
    
    Returns:
        {
            'action': 'allow' | 'block' | 'boost' | 'wait',
            'sweep_found': bool,
            'sweep_direction': str | None,  # 'bullish' or 'bearish'
            'sweep_quality': int | None,
            'sweep_level': float | None,
            'sweep_level_type': str | None,
            'sweep_time': str | None,
            'boost_amount': int,
            'nearest_level': float | None,  # For delay mode
            'description': str,
        }
    """
    # US-108: Override mode based on strategy tier
    if strategy_id:
        mode = _get_mode_for_strategy(strategy_id)
    
    # Map strategy direction to sweep direction
    # Long trade -> want bullish sweep (price swept below support, reversed up)
    # Short trade -> want bearish sweep (price swept above resistance, reversed down)
    desired_sweep = "bullish" if direction == "long" else "bearish"
    
    # Fetch recent sweeps
    try:
        sweeps = scan_symbol_for_sweeps(symbol, interval, asset_type, lookback_bars=SWEEP_LOOKBACK_BARS + 50)
    except Exception as e:
        return {
            "action": "allow",
            "sweep_found": False,
            "sweep_direction": None,
            "sweep_quality": None,
            "sweep_level": None,
            "sweep_level_type": None,
            "sweep_time": None,
            "boost_amount": 0,
            "nearest_level": None,
            "description": f"Sweep check failed ({e}), allowing signal.",
        }
    
    # US-108: Filter sweeps based on tiered rules (asset type exclusions, premium filter)
    valid_sweeps = _filter_valid_sweeps(sweeps, asset_type, strategy_id)
    
    # Check for direction-aligned sweep
    aligned_sweep = None
    for s in valid_sweeps:
        if s.direction == desired_sweep:
            # Check proximity: sweep level should be near entry price
            # Fetch ATR for proximity calculation
            if asset_type == "crypto":
                from fetch_intraday_crypto import get_intraday_candles
                df = get_intraday_candles(symbol, interval, 50)
            else:
                from fetch_intraday_stocks import get_intraday_bars
                df = get_intraday_bars(symbol, interval, 50)
            
            if len(df) > 14:
                atr = _compute_atr(df).iloc[-1]
                proximity = abs(s.entry_price - entry_price)
                
                if proximity <= SWEEP_PROXIMITY_ATR * atr:
                    aligned_sweep = s
                    break
    
    # Find nearest liquidity level (for delay mode)
    nearest_level = None
    if mode == "delay" and aligned_sweep is None:
        for s in valid_sweeps:
            if abs(s.entry_price - entry_price) / entry_price < 0.02:  # within 2%
                nearest_level = s.level_price
                break
        if nearest_level is None:
            # Find any nearby liquidity level
            if asset_type == "crypto":
                from fetch_intraday_crypto import get_intraday_candles, get_daily_levels
                df = get_intraday_candles(symbol, interval, 100)
                daily_levels = get_daily_levels(symbol)
                session_levels = {}
            else:
                from fetch_intraday_stocks import get_intraday_bars, get_daily_levels, get_session_levels
                df = get_intraday_bars(symbol, interval, 100)
                daily_levels = get_daily_levels(symbol)
                session_levels = get_session_levels(symbol, interval)
            
            if len(df) > 0:
                current_price = df["close"].iloc[-1]
                levels = identify_liquidity_levels(df, daily_levels, session_levels, current_price)
                if levels:
                    nearest_level = levels[0].price
    
    # Determine action based on mode
    if aligned_sweep is not None:
        # Sweep found and aligned with trade direction
        if mode == "require":
            action = "allow"
        elif mode == "boost":
            action = "boost"
        else:  # delay
            action = "allow"
        
        return {
            "action": action,
            "sweep_found": True,
            "sweep_direction": aligned_sweep.direction,
            "sweep_quality": aligned_sweep.quality_score,
            "sweep_level": aligned_sweep.level_price,
            "sweep_level_type": aligned_sweep.level_type,
            "sweep_time": aligned_sweep.timestamp,
            "boost_amount": SWEEP_BOOST_AMOUNT if mode == "boost" else 0,
            "nearest_level": None,
            "description": (
                f"✅ {aligned_sweep.direction} sweep detected at {aligned_sweep.level_type} "
                f"${aligned_sweep.level_price:.2f} (quality: {aligned_sweep.quality_score}/100). "
                f"Entry aligns with sweep direction. "
                f"+{SWEEP_BOOST_AMOUNT} quality boost." if mode == "boost" else
                f"✅ Sweep confirmed: {aligned_sweep.direction} at {aligned_sweep.level_type} "
                f"${aligned_sweep.level_price:.2f}. Entry allowed."
            ),
        }
    else:
        # No aligned sweep found
        if mode == "require":
            return {
                "action": "block",
                "sweep_found": False,
                "sweep_direction": None,
                "sweep_quality": None,
                "sweep_level": None,
                "sweep_level_type": None,
                "sweep_time": None,
                "boost_amount": 0,
                "nearest_level": nearest_level,
                "description": (
                    f"❌ No {desired_sweep} sweep detected near ${entry_price:.2f} "
                    f"in last {SWEEP_LOOKBACK_BARS} bars. Signal blocked "
                    f"(require mode). Nearest level: "
                    f"${nearest_level:.2f}" if nearest_level else "N/A"
                ),
            }
        elif mode == "delay":
            return {
                "action": "wait",
                "sweep_found": False,
                "sweep_direction": None,
                "sweep_quality": None,
                "sweep_level": None,
                "sweep_level_type": None,
                "sweep_time": None,
                "boost_amount": 0,
                "nearest_level": nearest_level,
                "description": (
                    f"⏳ No sweep yet. Waiting up to {MAX_WAIT_BARS} bars "
                    f"for {desired_sweep} sweep near ${entry_price:.2f}. "
                    f"Watch level: ${nearest_level:.2f}" if nearest_level else "No nearby level to watch."
                ),
            }
        else:  # boost
            return {
                "action": "allow",
                "sweep_found": False,
                "sweep_direction": None,
                "sweep_quality": None,
                "sweep_level": None,
                "sweep_level_type": None,
                "sweep_time": None,
                "boost_amount": 0,
                "nearest_level": nearest_level,
                "description": (
                    f"No aligned sweep detected near ${entry_price:.2f}. "
                    f"Signal allowed without boost (boost mode)."
                ),
            }


def get_sweep_context_for_signal(
    symbol: str,
    entry_price: float,
    direction: str,
    asset_type: str = "crypto",
    interval: str = "5m",
) -> dict:
    """
    Get sweep context data for tagging a signal.
    
    This is a lighter-weight version that just reports sweep status
    without blocking or boosting. Used for signal metadata tagging.
    
    Returns dict with sweep_context fields for the signal record.
    """
    result = check_sweep_alignment(
        symbol, entry_price, direction, asset_type, interval, mode="boost"
    )
    
    return {
        "sweep_found": result["sweep_found"],
        "sweep_direction": result["sweep_direction"],
        "sweep_quality": result["sweep_quality"],
        "sweep_level_type": None,  # Would need to return from check_sweep_alignment
        "sweep_aligned": (
            result["sweep_direction"] == ("bullish" if direction == "long" else "bearish")
            if result["sweep_direction"] else False
        ),
        "sweep_description": result["description"],
    }


def batch_check_sweeps(signals: list, asset_type: str = "crypto") -> list:
    """
    Check sweep alignment for a batch of signals.
    
    Args:
        signals: List of dicts with 'symbol', 'entry_price', 'direction'
        asset_type: 'crypto' or 'stock'
    
    Returns:
        List of signals with sweep_context added
    """
    enriched = []
    for sig in signals:
        sweep_ctx = get_sweep_context_for_signal(
            sig["symbol"],
            sig.get("entry_price", 0),
            sig.get("direction", "long"),
            asset_type,
        )
        sig["sweep_context"] = sweep_ctx
        if sweep_ctx["sweep_aligned"]:
            sig["quality_boost"] = SWEEP_BOOST_AMOUNT
        enriched.append(sig)
    
    return enriched


if __name__ == "__main__":
    print("=== Sweep Timing Filter Test ===\n")
    
    # Test with crypto
    print("── Crypto (boost mode) ──")
    test_signals = [
        {"symbol": "BTC", "entry_price": 63000, "direction": "long"},
        {"symbol": "BTC", "entry_price": 63000, "direction": "short"},
        {"symbol": "ETH", "entry_price": 1880, "direction": "long"},
        {"symbol": "SOL", "entry_price": 75, "direction": "long"},
    ]
    
    for sig in test_signals:
        result = check_sweep_alignment(
            sig["symbol"], sig["entry_price"], sig["direction"],
            asset_type="crypto", mode="boost",
        )
        print(f"\n{sig['symbol']} {sig['direction']} @ ${sig['entry_price']}")
        print(f"  Action: {result['action']}")
        print(f"  Sweep: {result['sweep_found']}")
        if result["sweep_found"]:
            print(f"  Direction: {result['sweep_direction']}")
            print(f"  Quality: {result['sweep_quality']}/100")
            print(f"  Level: ${result['sweep_level']:.2f}")
        print(f"  Desc: {result['description'][:100]}")
    
    # Test require mode
    print("\n── Crypto (require mode) ──")
    result = check_sweep_alignment("BTC", 63000, "long", "crypto", mode="require")
    print(f"BTC long @ $63000 (require): {result['action']} - {result['description'][:80]}")
    
    # Test stocks
    print("\n── Stocks (boost mode) ──")
    stock_signals = [
        {"symbol": "AAPL", "entry_price": 305, "direction": "long"},
        {"symbol": "NVDA", "entry_price": 225, "direction": "long"},
        {"symbol": "MSFT", "entry_price": 495, "direction": "long"},
    ]
    
    for sig in stock_signals:
        result = check_sweep_alignment(
            sig["symbol"], sig["entry_price"], sig["direction"],
            asset_type="stock", mode="boost",
        )
        print(f"\n{sig['symbol']} {sig['direction']} @ ${sig['entry_price']}")
        print(f"  Action: {result['action']}")
        print(f"  Sweep: {result['sweep_found']}")
        if result["sweep_found"]:
            print(f"  Direction: {result['sweep_direction']}")
            print(f"  Quality: {result['sweep_quality']}/100")
        print(f"  Desc: {result['description'][:100]}")
