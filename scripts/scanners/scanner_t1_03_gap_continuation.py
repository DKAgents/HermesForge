#!/usr/bin/env python3
"""
scanner_t1_03_gap_continuation.py — STR-T1-03: Gap Continuation (Daily)

Matches the T1 discovery spec exactly:
  Long:  50-SMA > 200-SMA (bull market), today's open > prior high by >= 0.5 ATR(14),
         close > open (continuation confirmed), volume > prior 5-bar avg × 1.2
  Short: 50-SMA < 200-SMA (bear market), today's open < prior low by >= 0.5 ATR(14),
         close < open (continuation confirmed), volume > prior 5-bar avg × 1.2
  Entry: t+0 — at the close of the same bar (gap day close)
  Stop:  Long: prior day's close; Short: prior day's close
         Min distance: 0.5 ATR(14)
  Target T1 (50%): 1.5 × gap size
  Target T2 (50%): Trail with 5-day EMA — exit on close against EMA
  Time stop: 5 trading days
"""

import sys
import pathlib
import pandas as pd
import numpy as np

STRATEGY_ID = "STR-T1-03-gap-continuation"
ATR_PERIOD = 14
GAP_ATR_MULT = 0.5
VOLUME_MULT = 1.2
SMA_FAST = 50
SMA_SLOW = 200
T1_GAP_MULT = 1.5
MIN_STOP_ATR = 0.5
EMA_TRAIL = 5
TIME_STOP_BARS = 5


def compute_atr(df: pd.DataFrame, period: int = ATR_PERIOD) -> pd.Series:
    high, low, close = df['high'], df['low'], df['close']
    prev_close = close.shift(1)
    tr = pd.concat([
        high - low,
        (high - prev_close).abs(),
        (low - prev_close).abs(),
    ], axis=1).max(axis=1)
    return tr.rolling(window=period, min_periods=1).mean()


def compute_ema(series: pd.Series, period: int) -> pd.Series:
    return series.ewm(span=period, adjust=False).mean()


def scan_ticker(df: pd.DataFrame, ticker: str) -> list:
    signals = []
    min_len = max(SMA_SLOW, ATR_PERIOD, 10) + TIME_STOP_BARS + 5
    if 'volume' not in df.columns:
        return signals
    if len(df) < min_len:
        return signals

    atr = compute_atr(df)
    sma50 = df['close'].rolling(window=SMA_FAST).mean()
    sma200 = df['close'].rolling(window=SMA_SLOW).mean()
    ema5 = compute_ema(df['close'], EMA_TRAIL)
    vol_avg_5 = df['volume'].rolling(window=5).mean()

    for i in range(min_len - TIME_STOP_BARS, len(df) - TIME_STOP_BARS):
        atr_i = atr.iloc[i]
        if pd.isna(atr_i) or atr_i <= 0:
            continue

        sma50_i = sma50.iloc[i]
        sma200_i = sma200.iloc[i]
        if pd.isna(sma50_i) or pd.isna(sma200_i):
            continue

        close_i = df['close'].iloc[i]
        open_i = df['open'].iloc[i]
        high_i = df['high'].iloc[i]
        low_i = df['low'].iloc[i]
        prior_high = df['high'].iloc[i - 1]
        prior_low = df['low'].iloc[i - 1]
        prior_close = df['close'].iloc[i - 1]
        vol_i = df['volume'].iloc[i]
        vol_avg_i = vol_avg_5.iloc[i]

        if pd.isna(vol_avg_i) or vol_avg_i <= 0:
            continue

        direction = None
        gap_size = 0.0

        # ── Long signal ──
        if (sma50_i > sma200_i                                # bull market
                and open_i > prior_high + GAP_ATR_MULT * atr_i  # upside gap
                and close_i > open_i                            # continuation confirmed
                and vol_i > VOLUME_MULT * vol_avg_i):           # elevated volume
            direction = 'long'
            gap_size = open_i - prior_high

            raw_stop = prior_close
            min_stop = close_i - MIN_STOP_ATR * atr_i
            stop_price = max(raw_stop, min_stop)

            if stop_price >= close_i:
                continue

            risk = close_i - stop_price
            target_t1 = close_i + T1_GAP_MULT * gap_size
            if target_t1 <= close_i:
                target_t1 = close_i + 2 * risk

        # ── Short signal ──
        elif (sma50_i < sma200_i                                # bear market
                and open_i < prior_low - GAP_ATR_MULT * atr_i    # downside gap
                and close_i < open_i                              # continuation confirmed
                and vol_i > VOLUME_MULT * vol_avg_i):             # elevated volume
            direction = 'short'
            gap_size = prior_low - open_i

            raw_stop = prior_close
            min_stop = close_i + MIN_STOP_ATR * atr_i
            stop_price = min(raw_stop, min_stop)

            if stop_price <= close_i:
                continue

            risk = stop_price - close_i
            target_t1 = close_i - T1_GAP_MULT * gap_size
            if target_t1 >= close_i:
                target_t1 = close_i - 2 * risk
        else:
            continue

        # ── Entry at t+0: close of gap day ──
        entry_price = close_i
        entry_idx = i + 1  # start scanning from next bar

        # Forward-scan for exit
        exit_price = None
        exit_reason = None
        exit_date = None
        t1_exited = False

        scan_end = min(entry_idx + TIME_STOP_BARS, len(df))
        for j in range(entry_idx, scan_end):
            bar = df.iloc[j]
            ema_j = ema5.iloc[j]

            if direction == 'long':
                if bar['low'] <= stop_price:
                    exit_price = stop_price
                    exit_reason = 'stop'
                    exit_date = df.index[j]
                    break
                if not t1_exited and bar['high'] >= target_t1:
                    t1_exited = True
                if t1_exited and not pd.isna(ema_j):
                    if bar['close'] < ema_j:
                        exit_price = (target_t1 + bar['close']) / 2
                        exit_reason = 'trail_ema'
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
                if t1_exited and not pd.isna(ema_j):
                    if bar['close'] > ema_j:
                        exit_price = (target_t1 + bar['close']) / 2
                        exit_reason = 'trail_ema'
                        exit_date = df.index[j]
                        break

        if exit_price is None:
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
            'target_price': round(target_t1, 2),
            'exit_price': round(exit_price, 2),
            'exit_reason': exit_reason,
            'r_multiple': round(r_multiple, 3),
            'gap_size_pct': round(gap_size / prior_close * 100, 2) if prior_close > 0 else 0,
            'subperiod': df.iloc[i].get('subperiod', 'unknown') if 'subperiod' in df.columns else 'unknown',
        })

    return signals


def scan(df: pd.DataFrame, ticker: str, **kwargs) -> list:
    return scan_ticker(df, ticker)


if __name__ == "__main__":
    import json as json_module
    import argparse

    parser = argparse.ArgumentParser(description="STR-T1-03 Gap Continuation Scanner")
    parser.add_argument("--json", action="store_true")
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
            if len(df) > 0 and 'volume' in df.columns:
                data[ticker] = df

    print(f"Loaded {len(data)} tickers with volume data")
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
        print(f"STR-T1-03 Gap Continuation — Results")
        print(f"{'='*60}")
        print(f"Total signals: {total}")
        print(f"Avg R: {avg_r:.3f}")
        print(f"Win rate: {win_rate:.1f}%")
        print(f"Exit breakdown:")
        for reason, count in results['exit_reason'].value_counts().items():
            print(f"  {reason}: {count} ({count/total*100:.1f}%)")
        if args.json:
            print(json_module.dumps({
                'signals_found': total, 'avg_r': round(avg_r, 3),
                'win_rate': round(win_rate, 1),
            }, indent=2))
    else:
        print("No signals found.")