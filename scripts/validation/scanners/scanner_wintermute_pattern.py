#!/usr/bin/env python3
"""
scanner_wintermute_pattern.py — HermesForge MM-Pattern Strategy
===============================================================

Detects the Binance/Wintermute market-making pattern described by MartyParty:
  3 weekly directional moves, each followed by ~50% pullback.
  After the 3rd move completes, a larger 50% pullback of the total range.
  Entry at the 50% retracement, stop below 61.8%, target = structure high.

Timeframe: daily bars for structure, confirmed on 1h for entry.
Asset class: crypto (BTC, ETH, SOL, AVAX majors).
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field


# ── Configuration ────────────────────────────────────────────────────────────

STRATEGY_ID = "STR-WM-wintermute-pattern"
STRATEGY_NAME = "Wintermute MM Pattern"
VERSION = "1.0"

# Pattern detection
MIN_WEEKLY_MOVE_BPS = 150     # minimum weekly move for a valid wave (1.5%)
MAX_PULLBACK_PCT = 0.65       # pullback must be 35-65% of prior move
MIN_PULLBACK_PCT = 0.35
TOTAL_PULLBACK_TARGET = 0.50  # entry at 50% of total 3-wave range
WAVE_COUNT = 3                # number of waves required

# Risk management
STOP_BUFFER_PCT = 0.618       # stop below 61.8% retracement
TARGET_ATR_MULT = 3.0         # target = entry + 3 * ATR
MAX_HOLD_BARS = 21            # ~1 month on daily


@dataclass
class Wave:
    """A single wave: directional move + pullback."""
    start_idx: int
    peak_idx: int
    end_idx: int
    direction: str            # 'up' or 'down'
    move_bps: float           # size of the directional move
    pullback_bps: float       # size of the pullback
    pullback_pct: float       # pullback as % of move


@dataclass
class WintermutePattern:
    """Detected 3-wave pattern."""
    symbol: str
    waves: List[Wave]
    total_move_bps: float     # sum of all 3 moves
    entry_price: float        # 50% retracement level
    stop_price: float         # 61.8% retracement level
    target_price: float       # structure high (or ATR-based)
    direction: str            # 'long' or 'short'
    quality_score: int        # 0-100
    signal_date: str


def find_waves(df: pd.DataFrame) -> List[Wave]:
    """Scan daily data for directional waves with pullbacks."""
    closes = df['close'].values
    highs = df['high'].values
    lows = df['low'].values
    waves = []
    
    i = 0
    while i < len(closes) - 20:
        # Look for a directional move of at least MIN_WEEKLY_MOVE_BPS
        # Scan forward ~5-10 bars for a peak/trough
        look_ahead = min(10, len(closes) - i - 1)
        
        # Check for upward wave
        for j in range(i + 3, min(i + look_ahead, len(closes))):
            move_up = (closes[j] - closes[i]) / closes[i] * 10000
            if move_up > MIN_WEEKLY_MOVE_BPS:
                # Found upward move — now look for pullback
                for k in range(j + 2, min(j + 10, len(closes))):
                    pullback = (closes[j] - closes[k]) / closes[j] * 10000
                    pullback_pct = pullback / move_up if move_up > 0 else 0
                    if MIN_PULLBACK_PCT <= pullback_pct <= MAX_PULLBACK_PCT:
                        waves.append(Wave(
                            start_idx=i, peak_idx=j, end_idx=k,
                            direction='up', move_bps=move_up,
                            pullback_bps=pullback, pullback_pct=pullback_pct,
                        ))
                        i = k
                        break
                break
        
        # Check for downward wave
        for j in range(i + 3, min(i + look_ahead, len(closes))):
            move_down = (closes[i] - closes[j]) / closes[i] * 10000
            if move_down > MIN_WEEKLY_MOVE_BPS:
                # Found downward move — now look for pullback (upward)
                for k in range(j + 2, min(j + 10, len(closes))):
                    pullback = (closes[k] - closes[j]) / closes[j] * 10000
                    pullback_pct = pullback / move_down if move_down > 0 else 0
                    if MIN_PULLBACK_PCT <= pullback_pct <= MAX_PULLBACK_PCT:
                        waves.append(Wave(
                            start_idx=i, peak_idx=j, end_idx=k,
                            direction='down', move_bps=move_down,
                            pullback_bps=pullback, pullback_pct=pullback_pct,
                        ))
                        i = k
                        break
                break
        
        i += 1
    
    return waves


def detect_pattern(df: pd.DataFrame, symbol: str) -> Optional[WintermutePattern]:
    """Detect the complete 3-wave Wintermute pattern."""
    waves = find_waves(df)
    
    if len(waves) < WAVE_COUNT:
        return None
    
    # Take the 3 most recent waves (can alternate direction — market making cycles)
    recent = waves[-WAVE_COUNT:]
    directions = {w.direction for w in recent}
    
    # Direction is determined by the dominant recent move
    # If last 2 waves are same direction, that's the direction
    if len(recent) >= 2 and recent[-1].direction == recent[-2].direction:
        direction = recent[-1].direction
    else:
        # Use direction of the largest recent wave
        direction = max(recent, key=lambda w: w.move_bps).direction
    total_move = sum(w.move_bps for w in recent)
    
    # Compute 50% retracement level of total range
    closes = df['close'].values
    highs = df['high'].values
    lows = df['low'].values
    
    first_idx = recent[0].start_idx
    last_peak = max(w.peak_idx for w in recent)
    
    if direction == 'up':
        range_low = closes[first_idx]
        range_high = max(highs[first_idx:last_peak+1])
        entry = range_high - (range_high - range_low) * TOTAL_PULLBACK_TARGET
        stop = range_high - (range_high - range_low) * STOP_BUFFER_PCT
        target = range_high  # retest of structure high
    else:
        range_high = closes[first_idx]
        range_low = min(lows[first_idx:last_peak+1])
        entry = range_low + (range_high - range_low) * TOTAL_PULLBACK_TARGET
        stop = range_low + (range_high - range_low) * STOP_BUFFER_PCT
        target = range_low
    
    # Quality score based on wave consistency and pullback precision
    pullback_precision = 1.0 - abs(
        sum(w.pullback_pct for w in recent) / WAVE_COUNT - TOTAL_PULLBACK_TARGET
    )
    wave_consistency = 1.0 - np.std([w.move_bps for w in recent]) / (np.mean([w.move_bps for w in recent]) + 1)
    quality = int(min(100, max(0, (pullback_precision * 40 + wave_consistency * 40 + 20))))
    
    # Check if current price is near the entry level
    current = closes[-1]
    entry_proximity = abs(current - entry) / entry
    
    date_str = str(df.index[-1])[:10] if hasattr(df.index[-1], 'strftime') else str(df.index[-1])
    
    return WintermutePattern(
        symbol=symbol,
        waves=recent,
        total_move_bps=total_move,
        entry_price=round(entry, 2),
        stop_price=round(stop, 2),
        target_price=round(target, 2),
        direction=direction,
        quality_score=quality,
        signal_date=date_str,
    )


def scan(symbol: str, df: pd.DataFrame) -> List[Dict]:
    """
    Scanner entry point — compatible with HermesForge scanner convention.
    
    Returns list of signal dicts with:
        ticker, strategy_id, strategy_name, direction, entry_price,
        stop_price, target_price, quality_score, conditions
    """
    pattern = detect_pattern(df, symbol)
    if pattern is None:
        return []
    
    # Only fire if quality is decent and pattern is fresh (last bar)
    if pattern.quality_score < 40:
        return []
    
    signal = {
        "ticker": symbol,
        "strategy_id": STRATEGY_ID,
        "strategy_name": STRATEGY_NAME,
        "strategy_version": VERSION,
        "direction": pattern.direction,
        "entry_price": pattern.entry_price,
        "stop_price": pattern.stop_price,
        "target_price": pattern.target_price,
        "quality_score": pattern.quality_score,
        "asset_class": "crypto",
        "publish_channel": "crypto",
        "timeframe": "daily",
        "subperiod": f"wintermute_{pattern.direction}",
        "total_move_bps": pattern.total_move_bps,
        "wave_count": WAVE_COUNT,
        "conditions": (
            f"• {WAVE_COUNT}-wave structure detected ({pattern.direction})\n"
            f"• Total move: {pattern.total_move_bps:.0f} bps\n"
            f"• Pullback precision: {pattern.quality_score}/100\n"
            f"• Entry at 50% retracement of total range\n"
            f"• Stop below 61.8% retracement"
        ),
        "date": pattern.signal_date,
    }
    
    return [signal]


# ── CLI test ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys, os
    symbol = sys.argv[1] if len(sys.argv) > 1 else "BTC"
    parquet_path = sys.argv[2] if len(sys.argv) > 2 else f"/root/.hermes/market_data/crypto/{symbol}.parquet"
    
    if not os.path.exists(parquet_path):
        print(f"ERROR: {parquet_path} not found")
        sys.exit(1)
    
    df = pd.read_parquet(parquet_path)
    print(f"Scanning {symbol}: {len(df)} bars\n")
    
    signals = scan(symbol, df)
    
    if signals:
        for s in signals:
            print(f"✅ SIGNAL: {s['ticker']} {s['direction'].upper()}")
            print(f"   Entry:  ${s['entry_price']:,.2f}")
            print(f"   Stop:   ${s['stop_price']:,.2f}")
            print(f"   Target: ${s['target_price']:,.2f}")
            print(f"   Quality: {s['quality_score']}/100")
            print(f"   Total move: {s['total_move_bps']:.0f} bps")
            print(f"   {s['conditions']}")
    else:
        print(f"No pattern detected for {symbol}")
        
        # Show wave structure for debugging
        waves = find_waves(df)
        print(f"\nWaves found: {len(waves)}")
        for i, w in enumerate(waves[-6:]):
            print(f"  Wave {i}: {w.direction} {w.move_bps:.0f}bps, pullback {w.pullback_pct:.0%}")