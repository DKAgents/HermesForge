#!/usr/bin/env python3
"""
scanner_k_breadth_gap.py — STR-K: Breadth-Gated Gap Reversal

Standalone scanner for Phase 1A validation. NOT added to live registry.

Entry: Gap-down opening + McClellan Oscillator < -50 (oversold breadth)
       + AD Line trending up (3-day) + price crosses gap midpoint
Exit: Stop at gap low, target at previous close (full gap fill), time stop 5 bars
Direction: Long-only
Regime: Transitional (gap exhaustion with breadth confirmation)

Usage: python3 scanner_k_breadth_gap.py [--json]
"""

import sys
import pathlib
import pandas as pd
import numpy as np

STRATEGY_ID = "STR-K-breadth-gated-gap-reversal"
MIN_GAP_ATR_MULT = 1.5
BREADTH_OVERSOLD = -50
GAP_MIDPOINT_PENETRATION = 0.50
TIME_STOP_BARS = 5
RISK_PER_TRADE = 0.01

CACHE_DIR = pathlib.Path.home() / ".hermes" / "market_data"


def compute_mcclellan_ema(series, fast=19, slow=39):
    """McClellan Oscillator: EMA(19) - EMA(39) of daily advances-declines."""
    ema_fast = series.ewm(span=fast, adjust=False).mean()
    ema_slow = series.ewm(span=slow, adjust=False).mean()
    return ema_fast - ema_slow


def compute_breadth_signals(all_data: dict) -> pd.DataFrame:
    """
    Compute daily breadth from the universe:
    - Advances: close > previous close
    - Declines: close < previous close
    - AD Line: cumulative sum of (advances - declines)
    - McClellan Oscillator: EMA(19) - EMA(39) of (adv - decl)
    
    Returns a DataFrame indexed by date with breadth indicators.
    """
    # Collect daily advances/declines across all tickers
    all_closes = {}
    for ticker, df in all_data.items():
        if 'close' in df.columns:
            all_closes[ticker] = df['close']
    
    closes_df = pd.DataFrame(all_closes)
    
    # Daily advances and declines
    daily_ret = closes_df.pct_change()
    advances = (daily_ret > 0).sum(axis=1)
    declines = (daily_ret < 0).sum(axis=1)
    net_advancing = advances - declines
    
    # AD Line (cumulative)
    ad_line = net_advancing.cumsum()
    
    # McClellan Oscillator
    mcclellan = compute_mcclellan_ema(net_advancing)
    
    # AD Line 3-day trend (is it going up?)
    ad_trend_up = ad_line.diff(3) > 0
    
    breadth = pd.DataFrame({
        'mcclellan': mcclellan,
        'ad_line': ad_line,
        'ad_trend_up': ad_trend_up,
        'advances': advances,
        'declines': declines,
    })
    
    return breadth


def compute_atr(df: pd.DataFrame, period=14) -> pd.Series:
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


def scan_ticker(df: pd.DataFrame, ticker: str, breadth: pd.DataFrame) -> list:
    """
    Scan a single ticker for gap-reversal signals.
    Returns list of signal dicts.
    """
    signals = []
    
    if len(df) < 60:
        return signals
    
    # Align breadth to this ticker's dates
    ticker_breadth = breadth.reindex(df.index)
    
    # Compute ATR
    atr = compute_atr(df)
    
    # Need open price for gap detection
    if 'open' not in df.columns:
        return signals
    
    for i in range(20, len(df) - TIME_STOP_BARS):
        date = df.index[i]
        
        # 1. Gap detection: open < previous close by at least 1.5 ATR
        prev_close = df['close'].iloc[i - 1]
        open_price = df['open'].iloc[i]
        gap_size = prev_close - open_price  # positive = gap down
        gap_threshold = MIN_GAP_ATR_MULT * atr.iloc[i - 1]
        
        if gap_size < gap_threshold or gap_threshold <= 0:
            continue
        
        gap_low = df['low'].iloc[i]
        gap_midpoint = (prev_close + open_price) / 2
        
        # 2. Breadth gate: McClellan < -50 AND AD Line trending up
        mcc = ticker_breadth['mcclellan'].get(date, 0)
        ad_up = ticker_breadth['ad_trend_up'].get(date, False)
        
        if pd.isna(mcc) or mcc > BREADTH_OVERSOLD:
            continue
        if not ad_up:
            continue
        
        # 3. Entry trigger: price crosses above gap midpoint on same day or next day
        entered = False
        entry_date = None
        entry_price = None
        
        for j in range(i, min(i + 3, len(df))):
            if df['high'].iloc[j] >= gap_midpoint:
                entered = True
                entry_date = df.index[j]
                entry_price = gap_midpoint
                break
        
        if not entered:
            continue
        
        # Simulate trade
        stop_price = gap_low
        target_price = prev_close  # full gap fill
        
        if stop_price >= entry_price:
            continue  # invalid setup
        
        risk = entry_price - stop_price
        reward = target_price - entry_price
        rr = reward / risk if risk > 0 else 0
        
        if rr < 1.0:
            continue  # need at least 1:1 R:R
        
        # Simulate exit
        exit_price = None
        exit_reason = None
        exit_date = None
        hold_bars = 0
        
        for j in range(df.index.get_loc(entry_date) + 1, min(df.index.get_loc(entry_date) + TIME_STOP_BARS + 1, len(df))):
            hold_bars += 1
            bar = df.iloc[j]
            
            # Check stop first
            if bar['low'] <= stop_price:
                exit_price = stop_price
                exit_reason = 'stop'
                exit_date = df.index[j]
                break
            
            # Check target
            if bar['high'] >= target_price:
                exit_price = target_price
                exit_reason = 'target'
                exit_date = df.index[j]
                break
        
        if exit_price is None:
            # Time stop: exit at close of last bar
            last_idx = min(df.index.get_loc(entry_date) + TIME_STOP_BARS, len(df) - 1)
            exit_price = df['close'].iloc[last_idx]
            exit_reason = 'time'
            exit_date = df.index[last_idx]
            hold_bars = TIME_STOP_BARS
        
        r_multiple = (exit_price - entry_price) / risk
        
        signals.append({
            'ticker': ticker,
            'date': date.strftime('%Y-%m-%d'),
            'entry_date': entry_date.strftime('%Y-%m-%d'),
            'entry_price': round(entry_price, 2),
            'stop_price': round(stop_price, 2),
            'target_price': round(target_price, 2),
            'exit_price': round(exit_price, 2),
            'exit_reason': exit_reason,
            'r_multiple': round(r_multiple, 3),
            'hold_bars': hold_bars,
            'gap_size': round(gap_size, 2),
            'mcclellan': round(mcc, 2),
            'rr': round(rr, 2),
            'subperiod': df.iloc[i].get('subperiod', 'unknown'),
        })
    
    return signals


def scan(data: dict, **kwargs) -> list:
    """
    Main scan function. data is a dict of {ticker: DataFrame}.
    Returns list of signal dicts.
    """
    # Compute breadth from the full universe
    breadth = compute_breadth_signals(data)
    
    all_signals = []
    for ticker, df in data.items():
        signals = scan_ticker(df, ticker, breadth)
        all_signals.extend(signals)
    
    return all_signals


if __name__ == "__main__":
    import json as json_module
    import argparse
    
    parser = argparse.ArgumentParser(description="STR-K Breadth-Gated Gap Reversal Scanner")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()
    
    # Load cached data
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
    
    # Summary
    if signals:
        df = pd.DataFrame(signals)
        total = len(df)
        years = (pd.to_datetime(df['date']).max() - pd.to_datetime(df['date']).min()).days / 365.25
        sig_per_year = total / years if years > 0 else 0
        avg_r = df['r_multiple'].mean()
        win_rate = (df['r_multiple'] > 0).mean() * 100
        
        exit_counts = df['exit_reason'].value_counts()
        
        print(f"\n{'='*60}")
        print(f"STR-K Breadth-Gated Gap Reversal — Phase 1A Results")
        print(f"{'='*60}")
        print(f"Total signals: {total}")
        print(f"Signals/year: {sig_per_year:.1f}")
        print(f"Avg R: {avg_r:.3f}")
        print(f"Win rate: {win_rate:.1f}%")
        print(f"Sub-periods positive:")
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
                'signals': signals[:50],  # first 50 for inspection
            }, indent=2))
    else:
        print("No signals found.")
        if args.json:
            print(f"\n--- JSON ---")
            print(json_module.dumps({'signals_found': 0}))
