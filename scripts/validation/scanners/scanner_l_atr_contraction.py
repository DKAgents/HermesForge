#!/usr/bin/env python3
"""
scanner_l_atr_contraction.py — STR-L: ATR Contraction Breakout

Standalone scanner for Phase 1A validation. NOT added to live registry.

Entry: ATR at 120-bar low + ADX < 18 (low-vol regime) + breakout above
       20-bar high with volume > 1.5x average + price above SMA200
Exit: Stop at breakout day low, trailing stop at 2x ATR, time stop 20 bars
Direction: Long-only
Regime: Low-volatility (contraction -> expansion inflection)

Usage: python3 scanner_l_atr_contraction.py [--json]
"""

import sys
import pathlib
import pandas as pd
import numpy as np

STRATEGY_ID = "STR-L-atr-contraction-breakout"
ATR_PERIOD = 14
ATR_LOOKBACK = 120
ADX_THRESHOLD = 18
RANGE_LOOKBACK = 20
VOLUME_MULT = 1.5
SMA_PERIOD = 200
TRAILING_ATR_MULT = 2.0
TIME_STOP_BARS = 20
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


def compute_adx(df: pd.DataFrame, period=14) -> pd.Series:
    """Compute ADX (Average Directional Index)."""
    high = df['high']
    low = df['low']
    close = df['close']
    
    # Directional Movement
    up_move = high.diff()
    down_move = -low.diff()
    
    plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0)
    minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0)
    
    plus_dm = pd.Series(plus_dm, index=df.index)
    minus_dm = pd.Series(minus_dm, index=df.index)
    
    atr = compute_atr(df, period)
    
    plus_di = 100 * (plus_dm.rolling(window=period, min_periods=1).mean() / atr)
    minus_di = 100 * (minus_dm.rolling(window=period, min_periods=1).mean() / atr)
    
    dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan)
    adx = dx.rolling(window=period, min_periods=1).mean()
    
    return adx


def scan_ticker(df: pd.DataFrame, ticker: str) -> list:
    """Scan a single ticker for ATR contraction breakout signals."""
    signals = []
    
    if len(df) < max(SMA_PERIOD, ATR_LOOKBACK) + 10:
        return signals
    
    atr = compute_atr(df)
    adx = compute_adx(df)
    sma = df['close'].rolling(window=SMA_PERIOD).mean()
    volume_avg = df['volume'].rolling(window=20).mean()
    
    for i in range(ATR_LOOKBACK, len(df) - TIME_STOP_BARS):
        # 1. ATR at 120-bar low (prolonged low-volatility)
        atr_window = atr.iloc[i - ATR_LOOKBACK:i]
        if atr.iloc[i] > atr_window.min():
            continue
        
        # 2. ADX < 18 (confirmed non-trending regime)
        if pd.isna(adx.iloc[i]) or adx.iloc[i] > ADX_THRESHOLD:
            continue
        
        # 3. Price above SMA200 (long-only filter)
        if pd.isna(sma.iloc[i]) or df['close'].iloc[i] < sma.iloc[i]:
            continue
        
        # 4. Breakout above 20-bar high
        range_high = df['high'].iloc[i - RANGE_LOOKBACK:i].max()
        if df['close'].iloc[i] <= range_high:
            continue
        
        # 5. Volume confirmation
        if pd.isna(volume_avg.iloc[i]) or df['volume'].iloc[i] < VOLUME_MULT * volume_avg.iloc[i]:
            continue
        
        # Entry confirmed — simulate trade
        entry_price = df['close'].iloc[i]
        stop_price = df['low'].iloc[i]
        
        if stop_price >= entry_price:
            continue
        
        risk = entry_price - stop_price
        if risk <= 0:
            continue
        
        # Simulate with trailing stop
        exit_price = None
        exit_reason = None
        exit_date = None
        highest_close = entry_price
        
        entry_idx = i
        
        for j in range(i + 1, min(i + TIME_STOP_BARS + 1, len(df))):
            bar = df.iloc[j]
            
            # Update highest close
            if bar['close'] > highest_close:
                highest_close = bar['close']
            
            # Compute trailing stop
            current_atr = atr.iloc[j]
            trailing_stop = highest_close - TRAILING_ATR_MULT * current_atr
            
            # Check stop (use max of initial stop and trailing stop)
            effective_stop = max(stop_price, trailing_stop)
            
            if bar['low'] <= effective_stop:
                exit_price = effective_stop
                exit_reason = 'trailing_stop' if effective_stop > stop_price else 'stop'
                exit_date = df.index[j]
                break
            
            # Check if we should update trailing stop to be above initial stop
            if trailing_stop > stop_price:
                stop_price = trailing_stop
        
        if exit_price is None:
            # Time stop
            last_idx = min(i + TIME_STOP_BARS, len(df) - 1)
            exit_price = df['close'].iloc[last_idx]
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
            'atr_at_entry': round(atr.iloc[i], 4),
            'adx_at_entry': round(adx.iloc[i], 1),
            'volume_ratio': round(df['volume'].iloc[i] / volume_avg.iloc[i], 2),
            'range_high': round(range_high, 2),
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
    
    parser = argparse.ArgumentParser(description="STR-L ATR Contraction Breakout Scanner")
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
        print(f"STR-L ATR Contraction Breakout — Phase 1A Results")
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
