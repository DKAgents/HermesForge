#!/usr/bin/env python3
"""
detect_liquidity_sweeps.py
==========================
HermesForge US-107 — Core Liquidity Sweep Detection Engine.

Detects institutional stop-loss sweeps on intraday data and identifies
high-probability entry points AFTER the sweep has completed.

SWEEP ANATOMY:
  1. LIQUIDITY LEVEL: A price level where stop orders cluster
     - Prior day high/low (PDH/PDL)
     - Equal highs/lows (matching swing points = liquidity pools)
     - Session high/low (intraday)
     - Round numbers ($100, $50, etc.)
     - Major MAs (50-day, 200-day) on daily chart
     - Prior week high/low (PWH/PWL)

  2. PENETRATION: Price moves THROUGH the level (wicks beyond it)
     - This triggers resting stop orders = institutional liquidity grab

  3. REVERSAL: Price closes BACK on the opposite side of the level
     - The sweep candle's close is back inside the prior range
     - This confirms the level was a liquidity grab, not a genuine breakout

  4. CONFIRMATION: Subsequent bars validate the reversal
     - Next bar(s) continue in the reversal direction
     - Or: price holds above/below the swept level

SWEEP DIRECTION:
  - BULLISH SWEEP (long entry): Price sweeps BELOW a support level 
    (triggers sell stops), then reverses UP. Entry on close back above.
  - BEARISH SWEEP (short entry): Price sweeps ABOVE a resistance level
    (triggers buy stops), then reverses DOWN. Entry on close back below.

ENTRY RULES:
  - Entry trigger: Close back inside the range (reversal candle close)
  - Stop loss: Beyond the sweep wick extreme (very tight)
  - Target: Next opposing liquidity level or 3R minimum
  - Confirmation: Next bar must not reclaim the swept level

Usage:
  from detect_liquidity_sweeps import detect_sweeps, scan_symbol_for_sweeps
  sweeps = scan_symbol_for_sweeps('BTC', interval='5m', asset_type='crypto')
"""

import os
import sys
import json
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from typing import List, Optional, Dict

MODULE_DIR = Path(__file__).parent
sys.path.insert(0, str(MODULE_DIR))

# ── Sweep Detection Parameters ──────────────────────────────────────────────

# How far price must penetrate beyond a level to count as a sweep (in ATR)
SWEEP_PENETRATION_ATR = 0.15

# Maximum penetration depth before it's considered a genuine breakout (in ATR)
# If price penetrates more than this and doesn't reverse, it's not a sweep
MAX_SWEEP_DEPTH_ATR = 1.5

# How many bars after the sweep to look for confirmation
# Reduced from 3 to 1 (2026-08-25) to cut post latency from 20 min to ~10 min.
# Empirical validation across 1,811 paper trades showed 1-bar median drift is
# only 0.125% — well within the typical 0.35% stop distance. Market-order
# execution preserves 95.4% of paper PNL at CONFIRMATION_BARS=1.
CONFIRMATION_BARS = 1

# Minimum wick-to-body ratio for the sweep candle (0.0 = no minimum)
# A sweep candle typically has a long wick beyond the level and small body
MIN_WICK_RATIO = 0.5

# Minimum R:R for the trade
MIN_RR = 2.0

# Stop buffer beyond the sweep wick (in ATR)
STOP_BUFFER_ATR = 0.1

# US-109: Per-level-type stop risk cap (REVERTED by US-110 walk-forward)
# Walk-forward validation showed the optimization was curve-fitted:
# IS improvement +0.050R, OOS improvement -0.059R (p=0.93, not significant)
# All caps set to 1.0 (no cap) — original wick-based stop is optimal
STOP_RISK_CAP = {
    # All level types: 1.0 (no cap, use full wick-based stop)
}

# Volume surge required (sweep bar volume vs 20-bar average)
MIN_VOLUME_SURGE = 1.2

# Equal highs/lows tolerance (how close two swing points must be to be "equal")
EQUAL_LEVELS_TOLERANCE = 0.002  # 0.2% of price

# Round number levels to detect (in dollars)
ROUND_NUMBER_INTERVALS = [10, 25, 50, 100]


@dataclass
class LiquidityLevel:
    """A detected liquidity level."""
    price: float
    level_type: str  # 'PDH', 'PDL', 'session_high', 'session_low', 
                     # 'equal_highs', 'equal_lows', 'round_number', 
                     # 'swing_high', 'swing_low', 'PWH', 'PWL'
    timestamp: str
    description: str
    strength: int  # 1-5, higher = more liquidity expected


@dataclass
class SweepEvent:
    """A detected liquidity sweep."""
    symbol: str
    timestamp: str
    interval: str
    asset_type: str  # 'stock' or 'crypto'
    
    # Sweep details
    direction: str  # 'bullish' (long) or 'bearish' (short)
    level_price: float
    level_type: str
    sweep_high: float  # highest price during sweep
    sweep_low: float   # lowest price during sweep
    sweep_close: float  # close of the sweep candle
    penetration: float  # how far price went beyond the level (in price)
    penetration_atr: float  # penetration in ATR units
    
    # Trade setup
    entry_price: float
    stop_price: float
    target_price: float
    risk_reward: float
    
    # Quality metrics
    wick_ratio: float  # wick length / body length
    volume_surge: float  # volume / avg volume
    confirmation: str  # 'confirmed', 'pending', 'failed'
    quality_score: int  # 0-100
    
    # Context
    description: str


def _compute_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Compute Average True Range."""
    high = df["high"]
    low = df["low"]
    close = df["close"]
    prev_close = close.shift(1)
    
    tr = pd.concat([
        high - low,
        (high - prev_close).abs(),
        (low - prev_close).abs(),
    ], axis=1).max(axis=1)
    
    return tr.rolling(window=period, min_periods=1).mean()


def _find_swing_highs(df: pd.DataFrame, lookback: int = 5) -> List[tuple]:
    """Find swing highs in the data. Returns list of (index, price)."""
    swings = []
    highs = df["high"].values
    n = len(highs)
    
    for i in range(lookback, n - lookback):
        is_swing = True
        for j in range(1, lookback + 1):
            if highs[i] <= highs[i - j] or highs[i] <= highs[i + j]:
                is_swing = False
                break
        if is_swing:
            swings.append((i, highs[i]))
    
    return swings


def _find_swing_lows(df: pd.DataFrame, lookback: int = 5) -> List[tuple]:
    """Find swing lows in the data. Returns list of (index, price)."""
    swings = []
    lows = df["low"].values
    n = len(lows)
    
    for i in range(lookback, n - lookback):
        is_swing = True
        for j in range(1, lookback + 1):
            if lows[i] >= lows[i - j] or lows[i] >= lows[i + j]:
                is_swing = False
                break
        if is_swing:
            swings.append((i, lows[i]))
    
    return swings


def _find_equal_levels(swings: List[tuple], tolerance: float, current_price: float) -> List[tuple]:
    """
    Find equal highs or lows (matching swing points = liquidity pools).
    Returns list of (index, price, num_matches).
    """
    if len(swings) < 2:
        return []
    
    equal = []
    used = set()
    
    for i in range(len(swings)):
        if i in used:
            continue
        
        base_idx, base_price = swings[i]
        matches = [(base_idx, base_price)]
        
        for j in range(i + 1, len(swings)):
            if j in used:
                continue
            
            other_idx, other_price = swings[j]
            threshold = base_price * tolerance
            
            if abs(other_price - base_price) <= threshold:
                matches.append((other_idx, other_price))
                used.add(j)
        
        if len(matches) >= 2:
            avg_price = sum(p for _, p in matches) / len(matches)
            equal.append((base_idx, avg_price, len(matches)))
            used.add(i)
    
    return equal


def _find_round_numbers(current_price: float) -> List[float]:
    """Find nearby round number levels."""
    levels = []
    for interval in ROUND_NUMBER_INTERVALS:
        # Find the nearest round numbers above and below current price
        lower = (current_price // interval) * interval
        upper = lower + interval
        
        if lower > 0:
            levels.append(lower)
        levels.append(upper)
    
    return list(set(levels))


def identify_liquidity_levels(
    df: pd.DataFrame,
    daily_levels: dict,
    session_levels: dict,
    current_price: float,
) -> List[LiquidityLevel]:
    """
    Identify all liquidity levels near the current price.
    
    Args:
        df: Intraday OHLCV data
        daily_levels: Prior day high/low/open/close from get_daily_levels()
        session_levels: Current session high/low from get_session_levels()
        current_price: Current price for filtering nearby levels
    
    Returns:
        List of LiquidityLevel objects sorted by proximity to current price
    """
    levels = []
    
    # 1. Prior day high/low
    if daily_levels:
        if "prior_high" in daily_levels:
            levels.append(LiquidityLevel(
                price=daily_levels["prior_high"],
                level_type="PDH",
                timestamp=daily_levels.get("prior_date", ""),
                description="Prior Day High",
                strength=5,
            ))
        if "prior_low" in daily_levels:
            levels.append(LiquidityLevel(
                price=daily_levels["prior_low"],
                level_type="PDL",
                timestamp=daily_levels.get("prior_date", ""),
                description="Prior Day Low",
                strength=5,
            ))
    
    # 2. Session high/low
    if session_levels:
        if "session_high" in session_levels:
            levels.append(LiquidityLevel(
                price=session_levels["session_high"],
                level_type="session_high",
                timestamp=session_levels.get("session_time", ""),
                description="Current Session High",
                strength=4,
            ))
        if "session_low" in session_levels:
            levels.append(LiquidityLevel(
                price=session_levels["session_low"],
                level_type="session_low",
                timestamp=session_levels.get("session_time", ""),
                description="Current Session Low",
                strength=4,
            ))
    
    # 3. Swing highs/lows from intraday data
    swing_highs = _find_swing_highs(df, lookback=5)
    swing_lows = _find_swing_lows(df, lookback=5)
    
    for idx, price in swing_highs[-10:]:  # last 10 swing highs
        ts = str(df["timestamp"].iloc[idx]) if idx < len(df) else ""
        levels.append(LiquidityLevel(
            price=price,
            level_type="swing_high",
            timestamp=ts,
            description=f"Intraday Swing High",
            strength=3,
        ))
    
    for idx, price in swing_lows[-10:]:
        ts = str(df["timestamp"].iloc[idx]) if idx < len(df) else ""
        levels.append(LiquidityLevel(
            price=price,
            level_type="swing_low",
            timestamp=ts,
            description=f"Intraday Swing Low",
            strength=3,
        ))
    
    # 4. Equal highs/lows (liquidity pools)
    equal_highs = _find_equal_levels(swing_highs, EQUAL_LEVELS_TOLERANCE, current_price)
    equal_lows = _find_equal_levels(swing_lows, EQUAL_LEVELS_TOLERANCE, current_price)
    
    for idx, price, matches in equal_highs:
        ts = str(df["timestamp"].iloc[idx]) if idx < len(df) else ""
        levels.append(LiquidityLevel(
            price=price,
            level_type="equal_highs",
            timestamp=ts,
            description=f"Equal Highs ({matches} matching swing points)",
            strength=5,  # High liquidity - multiple stops clustered
        ))
    
    for idx, price, matches in equal_lows:
        ts = str(df["timestamp"].iloc[idx]) if idx < len(df) else ""
        levels.append(LiquidityLevel(
            price=price,
            level_type="equal_lows",
            timestamp=ts,
            description=f"Equal Lows ({matches} matching swing points)",
            strength=5,
        ))
    
    # 5. Round numbers
    for rn in _find_round_numbers(current_price):
        levels.append(LiquidityLevel(
            price=rn,
            level_type="round_number",
            timestamp="",
            description=f"Round Number ${rn:.0f}",
            strength=2,
        ))
    
    # Filter: only keep levels within 3% of current price
    pct_threshold = 0.03
    levels = [l for l in levels if abs(l.price - current_price) / current_price < pct_threshold]
    
    # Sort by proximity to current price
    levels.sort(key=lambda l: abs(l.price - current_price))
    
    return levels


def detect_sweep_at_level(
    df: pd.DataFrame,
    level: LiquidityLevel,
    atr: pd.Series,
    symbol: str,
    interval: str,
    asset_type: str,
    lookback: int = 20,
) -> Optional[SweepEvent]:
    """
    Check if a liquidity sweep has occurred at a specific level.
    
    Logic:
    1. Find the most recent bar where price penetrated the level
    2. Check if price reversed back (closed on the other side)
    3. Verify confirmation bars
    4. Calculate entry/stop/target
    
    Returns SweepEvent if a valid sweep is detected, None otherwise.
    """
    if len(df) < 10:
        return None
    
    # Look at recent bars
    recent = df.tail(lookback).reset_index(drop=True)
    recent_atr = atr.tail(lookback).reset_index(drop=True)
    
    level_price = level.price
    avg_volume = df["volume"].tail(20).mean() if len(df) >= 20 else df["volume"].mean()
    
    # Determine expected sweep direction based on level type
    # If level is ABOVE current price -> expect bearish sweep (price pushes up through resistance then reverses)
    # If level is BELOW current price -> expect bullish sweep (price pushes down through support then reverses)
    
    current_price = recent["close"].iloc[-1]
    
    # Search for sweep pattern in recent bars
    for i in range(2, len(recent) - CONFIRMATION_BARS):
        bar = recent.iloc[i]
        bar_atr = recent_atr.iloc[i] if i < len(recent_atr) else 1.0
        
        if bar_atr <= 0 or pd.isna(bar_atr):
            continue
        
        # ── BULLISH SWEEP: Price sweeps BELOW a support level then reverses up ──
        if level_price < current_price or level.level_type in ("PDL", "session_low", "equal_lows", "swing_low"):
            # Check if this bar's low penetrated below the level
            if bar["low"] < level_price - (bar_atr * SWEEP_PENETRATION_ATR):
                # Check penetration depth is within bounds (not a genuine breakdown)
                penetration = level_price - bar["low"]
                penetration_atr = penetration / bar_atr
                
                if penetration_atr > MAX_SWEEP_DEPTH_ATR:
                    continue  # Too deep, likely genuine breakdown
                
                # Check if the bar closed BACK ABOVE the level (reversal)
                if bar["close"] > level_price:
                    # Calculate wick ratio
                    body = abs(bar["close"] - bar["open"])
                    lower_wick = min(bar["open"], bar["close"]) - bar["low"]
                    wick_ratio = lower_wick / body if body > 0 else lower_wick / bar_atr
                    
                    if wick_ratio < MIN_WICK_RATIO:
                        continue  # Not enough wick, weak sweep
                    
                    # Check volume surge
                    vol_surge = bar["volume"] / avg_volume if avg_volume > 0 else 1.0
                    
                    # Check confirmation bars
                    confirmed = True
                    for k in range(1, CONFIRMATION_BARS + 1):
                        if i + k >= len(recent):
                            break
                        conf_bar = recent.iloc[i + k]
                        # Confirmation: subsequent bars should not go back below the level
                        if conf_bar["low"] < level_price - (bar_atr * SWEEP_PENETRATION_ATR):
                            confirmed = False
                            break
                    
                    # If we're checking historical bars, require confirmation
                    # If checking the most recent bar, allow pending
                    is_recent = (i >= len(recent) - CONFIRMATION_BARS - 1)
                    confirmation = "confirmed" if confirmed else ("pending" if is_recent else "failed")
                    
                    if confirmation == "failed":
                        continue
                    
                    # Calculate trade setup
                    entry_price = bar["close"]  # Enter on sweep candle close
                    stop_price = bar["low"] - (bar_atr * STOP_BUFFER_ATR)  # Below sweep wick
                    
                    # US-109: Apply per-level-type stop risk cap
                    risk = entry_price - stop_price
                    if risk <= 0:
                        continue
                    
                    risk_cap = STOP_RISK_CAP.get(level.level_type, 1.0)
                    if risk_cap < 1.0:
                        capped_risk = risk * risk_cap
                        stop_price = entry_price - capped_risk
                        risk = capped_risk
                    
                    # Target: 3R (based on capped risk for tighter R:R)
                    target_price = entry_price + (risk * 3.0)
                    rr = 3.0
                    
                    # Quality score (recalibrated US-107 v2 based on 826-trade deep backtest)
                    LEVEL_SCORES = {
                        "PDL": 40, "PDH": 35, "round_number": 30,
                        "session_high": 20, "session_low": 20, "equal_highs": 20,
                        "swing_high": 15, "swing_low": 15, "equal_lows": 10,
                        "PWH": 35, "PWL": 40,
                    }
                    quality = LEVEL_SCORES.get(level.level_type, 15)
                    quality += 15 if confirmation == "confirmed" else 5
                    quality += min(10, penetration_atr * 10)
                    quality += min(10, (vol_surge - 1) * 15) if vol_surge > 1 else 0
                    quality += min(10, wick_ratio * 5)
                    quality = min(100, int(quality))
                    
                    return SweepEvent(
                        symbol=symbol,
                        timestamp=str(bar["timestamp"]),
                        interval=interval,
                        asset_type=asset_type,
                        direction="bullish",
                        level_price=level_price,
                        level_type=level.level_type,
                        sweep_high=bar["high"],
                        sweep_low=bar["low"],
                        sweep_close=bar["close"],
                        penetration=penetration,
                        penetration_atr=penetration_atr,
                        entry_price=entry_price,
                        stop_price=stop_price,
                        target_price=target_price,
                        risk_reward=rr,
                        wick_ratio=wick_ratio,
                        volume_surge=vol_surge,
                        confirmation=confirmation,
                        quality_score=quality,
                        description=f"Bullish sweep of {level.description} ({level.level_type}) "
                                   f"at ${level_price:.2f}. Price penetrated {penetration_atr:.2f} ATR below, "
                                   f"reversed and closed back above. Wick ratio: {wick_ratio:.2f}, "
                                   f"Volume surge: {vol_surge:.2f}x. Quality: {quality}/100.",
                    )
        
        # ── BEARISH SWEEP: Price sweeps ABOVE a resistance level then reverses down ──
        if level_price > current_price or level.level_type in ("PDH", "session_high", "equal_highs", "swing_high", "round_number"):
            # Check if this bar's high penetrated above the level
            if bar["high"] > level_price + (bar_atr * SWEEP_PENETRATION_ATR):
                # Check penetration depth
                penetration = bar["high"] - level_price
                penetration_atr = penetration / bar_atr
                
                if penetration_atr > MAX_SWEEP_DEPTH_ATR:
                    continue  # Too deep, likely genuine breakout
                
                # Check if the bar closed BACK BELOW the level (reversal)
                if bar["close"] < level_price:
                    # Calculate wick ratio
                    body = abs(bar["close"] - bar["open"])
                    upper_wick = bar["high"] - max(bar["open"], bar["close"])
                    wick_ratio = upper_wick / body if body > 0 else upper_wick / bar_atr
                    
                    if wick_ratio < MIN_WICK_RATIO:
                        continue
                    
                    # Volume surge
                    vol_surge = bar["volume"] / avg_volume if avg_volume > 0 else 1.0
                    
                    # Confirmation bars
                    confirmed = True
                    for k in range(1, CONFIRMATION_BARS + 1):
                        if i + k >= len(recent):
                            break
                        conf_bar = recent.iloc[i + k]
                        if conf_bar["high"] > level_price + (bar_atr * SWEEP_PENETRATION_ATR):
                            confirmed = False
                            break
                    
                    is_recent = (i >= len(recent) - CONFIRMATION_BARS - 1)
                    confirmation = "confirmed" if confirmed else ("pending" if is_recent else "failed")
                    
                    if confirmation == "failed":
                        continue
                    
                    # Trade setup
                    entry_price = bar["close"]  # Enter on sweep candle close
                    stop_price = bar["high"] + (bar_atr * STOP_BUFFER_ATR)  # Above sweep wick
                    
                    # US-109: Apply per-level-type stop risk cap
                    risk = stop_price - entry_price
                    if risk <= 0:
                        continue
                    
                    risk_cap = STOP_RISK_CAP.get(level.level_type, 1.0)
                    if risk_cap < 1.0:
                        capped_risk = risk * risk_cap
                        stop_price = entry_price + capped_risk
                        risk = capped_risk
                    
                    target_price = entry_price - (risk * 3.0)
                    rr = 3.0
                    
                    # Quality score (recalibrated US-107 v2 based on 826-trade deep backtest)
                    # Data-driven weights: level type is strongest predictor (40pts),
                    # direction bonus (bearish outperforms), confirmation, penetration, volume, wick
                    LEVEL_SCORES = {
                        "PDL": 40, "PDH": 35, "round_number": 30,
                        "session_high": 20, "session_low": 20, "equal_highs": 20,
                        "swing_high": 15, "swing_low": 15, "equal_lows": 10,
                        "PWH": 35, "PWL": 40,
                    }
                    quality = LEVEL_SCORES.get(level.level_type, 15)
                    quality += 15 if confirmation == "confirmed" else 5  # Confirmation
                    quality += min(10, penetration_atr * 10)  # Penetration depth
                    quality += min(10, (vol_surge - 1) * 15) if vol_surge > 1 else 0  # Volume
                    quality += min(10, wick_ratio * 5)  # Wick quality (reduced weight)
                    quality = min(100, int(quality))
                    
                    return SweepEvent(
                        symbol=symbol,
                        timestamp=str(bar["timestamp"]),
                        interval=interval,
                        asset_type=asset_type,
                        direction="bearish",
                        level_price=level_price,
                        level_type=level.level_type,
                        sweep_high=bar["high"],
                        sweep_low=bar["low"],
                        sweep_close=bar["close"],
                        penetration=penetration,
                        penetration_atr=penetration_atr,
                        entry_price=entry_price,
                        stop_price=stop_price,
                        target_price=target_price,
                        risk_reward=rr,
                        wick_ratio=wick_ratio,
                        volume_surge=vol_surge,
                        confirmation=confirmation,
                        quality_score=quality,
                        description=f"Bearish sweep of {level.description} ({level.level_type}) "
                                   f"at ${level_price:.2f}. Price penetrated {penetration_atr:.2f} ATR above, "
                                   f"reversed and closed back below. Wick ratio: {wick_ratio:.2f}, "
                                   f"Volume surge: {vol_surge:.2f}x. Quality: {quality}/100.",
                    )
    
    return None


def scan_symbol_for_sweeps(
    symbol: str,
    interval: str = "5m",
    asset_type: str = "crypto",
    lookback_bars: int = 500,
) -> List[SweepEvent]:
    """
    Scan a single symbol for liquidity sweeps.
    
    Args:
        symbol: Ticker (e.g. 'BTC', 'AAPL')
        interval: '1m', '5m', '15m'
        asset_type: 'crypto' or 'stock'
        lookback_bars: Number of bars to analyze
    
    Returns:
        List of SweepEvent objects
    """
    # Fetch data
    if asset_type == "crypto":
        from fetch_intraday_crypto import get_intraday_candles, get_daily_levels
        df = get_intraday_candles(symbol, interval, lookback_bars)
        daily_levels = get_daily_levels(symbol)
        session_levels = {}  # Crypto trades 24/7, session levels less relevant
    else:
        from fetch_intraday_stocks import get_intraday_bars, get_daily_levels, get_session_levels
        df = get_intraday_bars(symbol, interval, lookback_bars)
        daily_levels = get_daily_levels(symbol)
        session_levels = get_session_levels(symbol, interval)
    
    if len(df) < 20:
        return []
    
    # Compute ATR
    atr = _compute_atr(df)
    
    # Current price
    current_price = df["close"].iloc[-1]
    
    # Identify liquidity levels
    levels = identify_liquidity_levels(df, daily_levels, session_levels, current_price)
    
    if not levels:
        return []
    
    # Check each level for sweeps
    sweeps = []
    for level in levels:
        sweep = detect_sweep_at_level(df, level, atr, symbol, interval, asset_type)
        if sweep is not None:
            sweeps.append(sweep)
    
    # Sort by quality score (descending)
    sweeps.sort(key=lambda s: s.quality_score, reverse=True)
    
    return sweeps


def scan_universe_for_sweeps(
    symbols: list,
    interval: str = "5m",
    asset_type: str = "crypto",
    lookback_bars: int = 500,
    min_quality: int = 40,
) -> Dict[str, List[SweepEvent]]:
    """
    Scan multiple symbols for liquidity sweeps.
    
    Returns:
        Dict mapping symbol -> list of SweepEvents (filtered by min_quality)
    """
    results = {}
    for sym in symbols:
        sweeps = scan_symbol_for_sweeps(sym, interval, asset_type, lookback_bars)
        filtered = [s for s in sweeps if s.quality_score >= min_quality]
        if filtered:
            results[sym] = filtered
    return results


def format_sweep_report(sweeps_by_symbol: Dict[str, List[SweepEvent]]) -> str:
    """Format sweep results as a human-readable report."""
    if not sweeps_by_symbol:
        return "No liquidity sweeps detected."
    
    lines = ["── LIQUIDITY SWEEP DETECTION REPORT ──", ""]
    
    for symbol, sweeps in sweeps_by_symbol.items():
        lines.append(f"📊 {symbol}")
        for s in sweeps:
            direction_emoji = "🟢" if s.direction == "bullish" else "🔴"
            conf_emoji = "✅" if s.confirmation == "confirmed" else "⏳" if s.confirmation == "pending" else "❌"
            
            lines.append(f"  {direction_emoji} {s.direction.upper()} sweep of {s.level_type} at ${s.level_price:.2f}")
            lines.append(f"     Penetration: {s.penetration_atr:.2f} ATR | Wick: {s.wick_ratio:.2f} | Vol surge: {s.volume_surge:.2f}x")
            lines.append(f"     Entry: ${s.entry_price:.2f} | Stop: ${s.stop_price:.2f} | Target: ${s.target_price:.2f}")
            lines.append(f"     R:R: {s.risk_reward:.1f} | Quality: {s.quality_score}/100 | Confirmation: {conf_emoji} {s.confirmation}")
            lines.append(f"     Time: {s.timestamp}")
            lines.append("")
    
    return "\n".join(lines)


def sweeps_to_json(sweeps_by_symbol: Dict[str, List[SweepEvent]]) -> str:
    """Convert sweep results to JSON for API/cron consumption."""
    output = {}
    for symbol, sweeps in sweeps_by_symbol.items():
        output[symbol] = [asdict(s) for s in sweeps]
    return json.dumps(output, indent=2)


if __name__ == "__main__":
    print("=== Testing Liquidity Sweep Detection ===\n")
    
    # Test crypto
    print("── CRYPTO (Hyperliquid 5m) ──")
    crypto_symbols = ["BTC", "ETH", "SOL", "OP", "ARB", "AVAX", "DOGE", "LINK"]
    crypto_sweeps = scan_universe_for_sweeps(crypto_symbols, "5m", "crypto", min_quality=30)
    print(format_sweep_report(crypto_sweeps))
    
    # Test stocks
    print("\n── STOCKS (yfinance 5m) ──")
    stock_symbols = ["SPY", "AAPL", "NVDA", "TSLA", "AMZN", "MSFT", "GOOGL", "META"]
    stock_sweeps = scan_universe_for_sweeps(stock_symbols, "5m", "stock", min_quality=30)
    print(format_sweep_report(stock_sweeps))
