#!/usr/bin/env python3
"""
scanner_t1_01_outside_day.py — STR-T1-01: Outside Day Key Reversal (Daily)

Matches the T1 discovery spec exactly:
  Long:  Prior trend (close < 20-SMA), signal bar low < prior 5-bar low,
         close > prior close, range > 1.2× prior 5-bar avg range, close > open
  Short: Prior trend (close > 20-SMA), signal bar high > prior 5-bar high,
         close < prior close, range > 1.2× prior 5-bar avg range, close < open
  Entry: t+1 open (next bar open)
  Stop:  Long: signal bar low - 0.2 ATR(14); Short: signal bar high + 0.2 ATR(14)
         Min distance: 1.0% (crypto) / 0.5% (stocks)
  Target T1 (50%): 1.5R; T2 (50%): 3.0R or prior swing, whichever wider
  Time stop: 10 trading days

Hostile-fill awareness: entry at t+1 open, stop at worst print, time stop enforced.
"""

import sys
import pathlib
import pandas as pd
import numpy as np

STRATEGY_ID = "STR-T1-01-outside-day-key-reversal"
ATR_PERIOD = 14
SMA_PERIOD = 20
RANGE_MULT = 1.2
STOP_ATR_BUFFER = 0.2
MIN_STOP_PCT_STOCK = 0.005   # 0.5%
MIN_STOP_PCT_CRYPTO = 0.01   # 1.0%
T1_R_MULT = 1.5
T2_R_MULT = 3.0
TIME_STOP_BARS = 10
PRIOR_BARS = 5
SWING_LOOKBACK = 20


def compute_atr(df: pd.DataFrame, period: int = ATR_PERIOD) -> pd.Series:
    high, low, close = df['high'], df['low'], df['close']
    prev_close = close.shift(1)
    tr = pd.concat([
        high - low,
        (high - prev_close).abs(),
        (low - prev_close).abs(),
    ], axis=1).max(axis=1)
    return tr.rolling(window=period, min_periods=1).mean()


def is_crypto(ticker: str) -> bool:
    crypto_tickers = {'BTC', 'ETH', 'SOL', 'XRP', 'ADA', 'DOGE', 'AVAX', 'DOT',
                      'MATIC', 'LINK', 'UNI', 'ATOM', 'LTC', 'ETC', 'XLM', 'BCH',
                      'ALGO', 'VET', 'ICP', 'FIL', 'APT', 'ARB', 'OP', 'NEAR',
                      'BTC-USD', 'ETH-USD', 'SOL-USD'}
    return ticker.upper() in crypto_tickers or '-USD' in ticker.upper()


def scan_ticker(df: pd.DataFrame, ticker: str) -> list:
    signals = []
    min_len = max(SMA_PERIOD, ATR_PERIOD, SWING_LOOKBACK, PRIOR_BARS) + TIME_STOP_BARS + 5
    if len(df) < min_len:
        return signals

    atr = compute_atr(df)
    sma20 = df['close'].rolling(window=SMA_PERIOD).mean()

    for i in range(min_len - TIME_STOP_BARS, len(df) - TIME_STOP_BARS):
        atr_i = atr.iloc[i]
        if pd.isna(atr_i) or atr_i <= 0:
            continue
        sma_i = sma20.iloc[i]
        if pd.isna(sma_i):
            continue

        close_i = df['close'].iloc[i]
        open_i = df['open'].iloc[i]
        high_i = df['high'].iloc[i]
        low_i = df['low'].iloc[i]
        prior_close = df['close'].iloc[i - 1]

        # Compute prior 5-bar avg range and extremes
        prior_5_range = (df['high'].iloc[i-5:i] - df['low'].iloc[i-5:i]).mean()
        if prior_5_range <= 0:
            continue
        range_i = high_i - low_i

        prior_5_low = df['low'].iloc[i-5:i].min()
        prior_5_high = df['high'].iloc[i-5:i].max()

        direction = None

        # ── Long signal ──
        if (close_i < sma_i                                    # prior trend: below 20-SMA
                and low_i < prior_5_low                         # new low vs 5-bar
                and close_i > prior_close                       # close above prior close
                and range_i > RANGE_MULT * prior_5_range        # wide range
                and close_i > open_i):                          # bullish close
            direction = 'long'

            min_stop_pct = MIN_STOP_PCT_CRYPTO if is_crypto(ticker) else MIN_STOP_PCT_STOCK
            raw_stop = low_i - STOP_ATR_BUFFER * atr_i
            min_stop_dist = close_i * min_stop_pct
            stop_price = min(raw_stop, close_i - min_stop_dist)

            if stop_price >= close_i:
                continue

            risk = close_i - stop_price
            target_t1 = close_i + T1_R_MULT * risk
            target_t2 = close_i + T2_R_MULT * risk

            # Determine prior swing high for wider T2
            prior_swing = df['high'].iloc[i-SWING_LOOKBACK:i].max()
            if prior_swing > target_t2:
                target_t2 = prior_swing

        # ── Short signal ──
        elif (close_i > sma_i                                   # prior trend: above 20-SMA
                and high_i > prior_5_high                        # new high vs 5-bar
                and close_i < prior_close                        # close below prior close
                and range_i > RANGE_MULT * prior_5_range         # wide range
                and close_i < open_i):                           # bearish close
            direction = 'short'

            min_stop_pct = MIN_STOP_PCT_CRYPTO if is_crypto(ticker) else MIN_STOP_PCT_STOCK
            raw_stop = high_i + STOP_ATR_BUFFER * atr_i
            min_stop_dist = close_i * min_stop_pct
            stop_price = max(raw_stop, close_i + min_stop_dist)

            if stop_price <= close_i:
                continue

            risk = stop_price - close_i
            target_t1 = close_i - T1_R_MULT * risk
            target_t2 = close_i - T2_R_MULT * risk

            prior_swing = df['low'].iloc[i-SWING_LOOKBACK:i].min()
            if prior_swing < target_t2:
                target_t2 = prior_swing
        else:
            continue

        # ── Entry at t+1 open (hostile-fill compatible) ──
        entry_idx = i + 1
        if entry_idx >= len(df):
            continue
        entry_price = df['open'].iloc[entry_idx]

        # Forward-scan for exit
        exit_price = None
        exit_reason = None
        exit_date = None
        t1_exited = False

        scan_end = min(entry_idx + TIME_STOP_BARS, len(df))
        for j in range(entry_idx, scan_end):
            bar = df.iloc[j]

            if direction == 'long':
                # Stop check (worst print = low)
                if bar['low'] <= stop_price:
                    exit_price = stop_price
                    exit_reason = 'stop'
                    exit_date = df.index[j]
                    break
                # T1 partial (50%)
                if not t1_exited and bar['high'] >= target_t1:
                    t1_exited = True
                # T2 (remaining 50%)
                if t1_exited and bar['high'] >= target_t2:
                    exit_price = (target_t1 + target_t2) / 2
                    exit_reason = 'target'
                    exit_date = df.index[j]
                    break
            else:  # short
                if bar['high'] >= stop_price:
                    exit_price = stop_price
                    exit_reason = 'stop'
                    exit_date = df.index[j]
                    break
                if not t1_exited and bar['low'] <= target_t1:
                    t1_exited = True
                if t1_exited and bar['low'] <= target_t2:
                    exit_price = (target_t1 + target_t2) / 2
                    exit_reason = 'target'
                    exit_date = df.index[j]
                    break

        if exit_price is None:
            # Time stop
            last_idx = scan_end - 1
            close_out = df['close'].iloc[last_idx]
            if t1_exited:
                exit_price = (target_t1 + close_out) / 2
            else:
                exit_price = close_out
            exit_reason = 'time'
            exit_date = df.index[last_idx]

        r_multiple = ((exit_price - entry_price) / risk) if direction == 'long' else ((entry_price - exit_price) / risk)

        signals.append({
            'ticker': ticker,
            'date': df.index[i].strftime('%Y-%m-%d'),
            'direction': direction,
            'entry_price': round(entry_price, 2),
            'stop_price': round(stop_price, 2),
            'target_price': round(target_t2, 2),
            'exit_price': round(exit_price, 2),
            'exit_reason': exit_reason,
            'r_multiple': round(r_multiple, 3),
            'subperiod': df.iloc[i].get('subperiod', 'unknown') if 'subperiod' in df.columns else 'unknown',
        })

    return signals


def scan(df: pd.DataFrame, ticker: str, **kwargs) -> list:
    """Main scan function — per-ticker interface matching Phase 1A convention."""
    return scan_ticker(df, ticker)


if __name__ == "__main__":
    import json as json_module
    import argparse

    parser = argparse.ArgumentParser(description="STR-T1-01 Outside Day Key Reversal Scanner")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / "validation"))
    from universe import get_universe

    CACHE_DIR = pathlib.Path.home() / ".hermes" / "market_data"
    universe = get_universe()
    data = {}
    for ticker in universe:
        path = CACHE_DIR / f"{ticker}.parquet"
        if path.exists():
            df = pd.read_parquet(path)
            if len(df) > 0:
                data[ticker] = df

    print(f"Loaded {len(data)} tickers")
    all_signals = []
    for ticker, df in data.items():
        sigs = scan_ticker(df, ticker)
        all_signals.extend(sigs)

    if all_signals:
        results = pd.DataFrame(all_signals)
        total = len(results)
        avg_r = results['r_multiple'].mean()
        win_rate = (results['r_multiple'] > 0).mean() * 100
        print(f"\n{'='*60}")
        print(f"STR-T1-01 Outside Day Key Reversal — Results")
        print(f"{'='*60}")
        print(f"Total signals: {total}")
        print(f"Avg R: {avg_r:.3f}")
        print(f"Win rate: {win_rate:.1f}%")
        print(f"Exit breakdown:")
        for reason, count in results['exit_reason'].value_counts().items():
            print(f"  {reason}: {count} ({count/total*100:.1f}%)")
        if args.json:
            print(f"\n--- JSON ---")
            print(json_module.dumps({
                'signals_found': total, 'avg_r': round(avg_r, 3),
                'win_rate': round(win_rate, 1),
            }, indent=2))
    else:
        print("No signals found.")