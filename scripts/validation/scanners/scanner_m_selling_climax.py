#!/usr/bin/env python3
"""
scanner_m_selling_climax.py — STR-M: Selling Climax Reversal

Standalone scanner for Phase 1A validation. NOT added to live registry.

Entry: ATR/Close > 2x its 50-day avg (high-vol regime) + 3+ consecutive
      down days + reversal day (new low but close above prior close) +
      volume >= 2x average + price above SMA200
Exit: Stop at reversal day low, 3:1 R:R target (50% at 2:1), time stop 15 bars
Direction: Long-only
Regime: High-volatility (selling climax / capitulation bottom)

Usage: python3 scanner_m_selling_climax.py [--json]
"""

import sys
import pathlib
import pandas as pd
import numpy as np

STRATEGY_ID = "STR-M-selling-climax-reversal"
ATR_PERIOD = 14
VOL_LOOKBACK = 50
VOL_THRESHOLD = 2.0      # ATR/Close > 2.0x its 50-day average
DECLINE_DAYS = 3          # 3+ consecutive down days
VOLUME_MULT = 2.0         # volume >= 2x average
SMA_PERIOD = 200
TARGET_RR = 3.0           # 3:1 R:R
PARTIAL_RR = 2.0          # 50% exit at 2:1
TIME_STOP_BARS = 15
MIN_RR = 1.0

CACHE_DIR = pathlib.Path.home() / ".hermes" / "market_data"


def compute_atr(df: pd.DataFrame, period=ATR_PERIOD) -> pd.Series:
    """Compute Average True Range."""
    high = df['high']
    low = df['low']
    close = df['close']
    prev_close = close.shift(1)
    
    tr = pd.concat([
        high - low,
        (high - prev_close).abs(),
        (low - prev_close).abs(),
    ], axis=1).max(axis=1)
    
    return tr.rolling(window=period, min_periods=1).mean()


def scan_ticker(df: pd.DataFrame, ticker: str) -> list:
    """Scan a single ticker for selling climax reversal signals."""
    signals = []
    
    if len(df) < max(SMA_PERIOD, VOL_LOOKBACK) + 10:
        return signals
    
    atr = compute_atr(df)
    sma = df['close'].rolling(window=SMA_PERIOD).mean()
    volume_avg = df['volume'].rolling(window=20).mean()
    
    # Normalized ATR (ATR / Close) for volatility regime detection
    atr_normalized = atr / df['close']
    atr_norm_avg = atr_normalized.rolling(window=VOL_LOOKBACK).mean()
    
    for i in range(max(SMA_PERIOD, VOL_LOOKBACK) + DECLINE_DAYS + 2, len(df) - TIME_STOP_BARS):
        # 1. High-volatility regime filter
        if pd.isna(atr_norm_avg.iloc[i]):
            continue
        vol_ratio = atr_normalized.iloc[i] / atr_norm_avg.iloc[i]
        if vol_ratio < VOL_THRESHOLD:
            continue
        
        # 2. Multi-day decline (3+ consecutive down days ending at i-1)
        decline = True
        for d in range(1, DECLINE_DAYS + 1):
            idx = i - d
            if idx < 1:
                decline = False
                break
            if df['close'].iloc[idx] >= df['close'].iloc[idx - 1]:
                decline = False
                break
        if not decline:
            continue
        
        # 3. Reversal day (today = i): new low for the decline, close above prior close
        decline_lows = [df['low'].iloc[i - d] for d in range(1, DECLINE_DAYS + 1)]
        prior_low = min(decline_lows)
        
        if df['low'].iloc[i] >= prior_low:
            continue  # didn't make a new low
        
        if df['close'].iloc[i] <= df['close'].iloc[i - 1]:
            continue  # didn't close above prior close (not a reversal)
        
        # 4. Volume confirmation (>= 2x average)
        if pd.isna(volume_avg.iloc[i]) or df['volume'].iloc[i] < VOLUME_MULT * volume_avg.iloc[i]:
            continue
        
        # 5. Price above SMA200 (long-only filter)
        if pd.isna(sma.iloc[i]) or df['close'].iloc[i] < sma.iloc[i]:
            continue
        
        # Entry confirmed — simulate trade
        entry_price = df['close'].iloc[i]
        stop_price = df['low'].iloc[i]  # reversal day low
        
        if stop_price >= entry_price:
            continue
        
        risk = entry_price - stop_price
        if risk <= 0:
            continue
        
        target_price = entry_price + TARGET_RR * risk
        partial_target = entry_price + PARTIAL_RR * risk
        
        # Simulate with partial exit at 2:1, remainder at 3:1 or trailing
        exit_price = None
        exit_reason = None
        exit_date = None
        partial_exited = False
        remaining_entry = entry_price  # for tracking remainder
        
        for j in range(i + 1, min(i + TIME_STOP_BARS + 1, len(df))):
            bar = df.iloc[j]
            
            # Check stop first
            if bar['low'] <= stop_price:
                if partial_exited:
                    exit_price = stop_price
                    exit_reason = 'stop'
                else:
                    exit_price = stop_price
                    exit_reason = 'stop'
                exit_date = df.index[j]
                break
            
            # Check partial target (50% at 2:1)
            if not partial_exited and bar['high'] >= partial_target:
                partial_exited = True
                # Track: 50% exited at partial_target, remainder continues
            
            # Check full target (remaining 50% at 3:1)
            if partial_exited and bar['high'] >= target_price:
                # Blended exit: 50% at partial_target, 50% at target_price
                exit_price = (partial_target + target_price) / 2
                exit_reason = 'target'
                exit_date = df.index[j]
                break
        
        if exit_price is None:
            # Time stop — exit at close
            last_idx = min(i + TIME_STOP_BARS, len(df) - 1)
            close_price = df['close'].iloc[last_idx]
            if partial_exited:
                # Blended: 50% at partial_target, 50% at time stop close
                exit_price = (partial_target + close_price) / 2
            else:
                exit_price = close_price
            exit_reason = 'time'
            exit_date = df.index[last_idx]
        
        r_multiple = (exit_price - entry_price) / risk
        
        signals.append({
            'ticker': ticker,
            'date': df.index[i].strftime('%Y-%m-%d'),
            'entry_price': round(entry_price, 2),
            'stop_price': round(stop_price, 2),
            'exit_price': round(exit_price, 2),
            'exit_reason': exit_reason,
            'r_multiple': round(r_multiple, 3),
            'vol_ratio': round(vol_ratio, 2),
            'volume_ratio': round(df['volume'].iloc[i] / volume_avg.iloc[i], 2),
            'decline_days': DECLINE_DAYS,
            'subperiod': df.iloc[i].get('subperiod', 'unknown'),
        })
    
    return signals


def scan(data: dict, **kwargs) -> list:
    """Main scan function."""
    all_signals = []
    for ticker, df in data.items():
        signals = scan_ticker(df, ticker)
        all_signals.extend(signals)
    return all_signals


if __name__ == "__main__":
    import json as json_module
    import argparse
    
    parser = argparse.ArgumentParser(description="STR-M Selling Climax Reversal Scanner")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()
    
    sys.path.insert(0, str(pathlib.Path(__file__).parent))
    from universe import get_universe
    
    universe = get_universe()
    data = {}
    for ticker in universe:
        path = CACHE_DIR / f"{ticker}.parquet"
        if path.exists():
            data[ticker] = pd.read_parquet(path)
    
    print(f"Loaded {len(data)} tickers")
    
    signals = scan(data)
    
    if signals:
        df = pd.DataFrame(signals)
        total = len(df)
        dates = pd.to_datetime(df['date'])
        years = (dates.max() - dates.min()).days / 365.25
        sig_per_year = total / years if years > 0 else 0
        avg_r = df['r_multiple'].mean()
        win_rate = (df['r_multiple'] > 0).mean() * 100
        
        exit_counts = df['exit_reason'].value_counts()
        
        print(f"\n{'='*60}")
        print(f"STR-M Selling Climax Reversal — Phase 1A Results")
        print(f"{'='*60}")
        print(f"Total signals: {total}")
        print(f"Signals/year: {sig_per_year:.1f}")
        print(f"Avg R: {avg_r:.3f}")
        print(f"Win rate: {win_rate:.1f}%")
        print(f"\nSub-periods:")
        for sp in df['subperiod'].unique():
            sp_r = df[df['subperiod'] == sp]['r_multiple'].mean()
            sp_n = len(df[df['subperiod'] == sp])
            print(f"  {sp}: {sp_n} signals, avg R {sp_r:.3f}")
        print(f"\nExit breakdown:")
        for reason, count in exit_counts.items():
            print(f"  {reason}: {count} ({count/total*100:.1f}%)")
        
        if args.json:
            print(f"\n--- JSON ---")
            print(json_module.dumps({
                'signals_found': total,
                'signals_per_year': round(sig_per_year, 1),
                'avg_r': round(avg_r, 3),
                'win_rate': round(win_rate, 1),
                'exit_breakdown': exit_counts.to_dict(),
            }, indent=2))
    else:
        print("No signals found.")
        if args.json:
            print(f"\n--- JSON ---")
            print(json_module.dumps({'signals_found': 0}))
