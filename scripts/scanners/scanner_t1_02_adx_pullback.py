#!/usr/bin/env python3
"""
scanner_t1_02_adx_pullback.py — STR-T1-02: ADX Trend Continuation Pullback (Daily)

Matches the T1 discovery spec exactly:
  Long:  ADX(14) > 25, +DI > -DI, today's low within 0.3 ATR(14) of 20-EMA,
         close > open (bullish candle), volume < prior 5-bar avg (declining vol)
  Short: ADX(14) > 25, -DI > +DI, today's high within 0.3 ATR(14) of 20-EMA,
         close < open (bearish candle), volume < prior 5-bar avg
  Entry: t+1 open (next bar open)
  Stop:  Long: pullback bar low - 0.2 ATR(14); Short: pullback bar high + 0.2 ATR(14)
         Min: 1.5 ATR(14)
  Target T1 (50%): Prior 20-bar swing extreme
  Target T2 (50%): Trail with 20-EMA exit
  Time stop: 15 trading days
"""

import sys
import pathlib
import pandas as pd
import numpy as np

STRATEGY_ID = "STR-T1-02-adx-trend-pullback"
ATR_PERIOD = 14
ADX_PERIOD = 14
EMA_PERIOD = 20
EMA_PULLBACK_ATR = 0.3      # within 0.3 ATR of EMA
STOP_ATR_BUFFER = 0.2
MIN_STOP_ATR = 1.5           # minimum stop distance
TIME_STOP_BARS = 15
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


def compute_adx(df: pd.DataFrame, period: int = ADX_PERIOD) -> tuple:
    """Returns (ADX, +DI, -DI) as pd.Series."""
    high, low, close = df['high'], df['low'], df['close']
    prev_close = close.shift(1)

    tr = pd.concat([
        high - low,
        (high - prev_close).abs(),
        (low - prev_close).abs(),
    ], axis=1).max(axis=1)
    atr = tr.ewm(alpha=1.0/period, adjust=False).mean()

    up_move = high - high.shift(1)
    down_move = low.shift(1) - low

    plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0.0)
    minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0.0)

    plus_dm_s = pd.Series(plus_dm, index=df.index).ewm(alpha=1.0/period, adjust=False).mean()
    minus_dm_s = pd.Series(minus_dm, index=df.index).ewm(alpha=1.0/period, adjust=False).mean()

    plus_di = 100 * (plus_dm_s / atr.replace(0, np.nan))
    minus_di = 100 * (minus_dm_s / atr.replace(0, np.nan))

    dx = 100 * (abs(plus_di - minus_di) / (plus_di + minus_di).replace(0, np.nan))
    adx = dx.ewm(alpha=1.0/period, adjust=False).mean()

    return adx, plus_di, minus_di


def compute_ema(series: pd.Series, period: int) -> pd.Series:
    return series.ewm(span=period, adjust=False).mean()


def scan_ticker(df: pd.DataFrame, ticker: str) -> list:
    signals = []
    min_len = max(ADX_PERIOD, ATR_PERIOD, EMA_PERIOD, SWING_LOOKBACK) + TIME_STOP_BARS + 10
    if 'volume' not in df.columns:
        return signals
    if len(df) < min_len:
        return signals

    atr = compute_atr(df)
    adx, plus_di, minus_di = compute_adx(df)
    ema20 = compute_ema(df['close'], EMA_PERIOD)
    vol_avg_5 = df['volume'].rolling(window=5).mean()

    for i in range(min_len - TIME_STOP_BARS, len(df) - TIME_STOP_BARS):
        atr_i = atr.iloc[i]
        if pd.isna(atr_i) or atr_i <= 0:
            continue
        adx_i = adx.iloc[i]
        if pd.isna(adx_i):
            continue

        plus_i = plus_di.iloc[i]
        minus_i = minus_di.iloc[i]
        close_i = df['close'].iloc[i]
        open_i = df['open'].iloc[i]
        high_i = df['high'].iloc[i]
        low_i = df['low'].iloc[i]
        ema_i = ema20.iloc[i]
        vol_i = df['volume'].iloc[i]
        vol_avg_i = vol_avg_5.iloc[i]

        if pd.isna(ema_i) or pd.isna(vol_avg_i) or vol_avg_i <= 0:
            continue

        direction = None

        # ── Long signal ──
        if (adx_i > 25
                and plus_i > minus_i                        # +DI > -DI
                and abs(low_i - ema_i) <= EMA_PULLBACK_ATR * atr_i  # pullback to EMA
                and low_i <= ema_i + EMA_PULLBACK_ATR * atr_i       # touches or near EMA
                and close_i > open_i                        # bullish candle
                and vol_i < vol_avg_i):                     # declining volume
            direction = 'long'

            raw_stop = low_i - STOP_ATR_BUFFER * atr_i
            min_stop = close_i - MIN_STOP_ATR * atr_i
            stop_price = min(raw_stop, min_stop)

            if stop_price >= close_i:
                continue

            risk = close_i - stop_price
            recent_swing_high = df['high'].iloc[i-SWING_LOOKBACK:i].max()
            target_t1 = recent_swing_high if recent_swing_high > close_i else close_i + 2 * risk
            target_t2 = None  # trail with EMA

        # ── Short signal ──
        elif (adx_i > 25
                and minus_i > plus_i                        # -DI > +DI
                and abs(high_i - ema_i) <= EMA_PULLBACK_ATR * atr_i  # rally to EMA
                and high_i >= ema_i - EMA_PULLBACK_ATR * atr_i
                and close_i < open_i                        # bearish candle
                and vol_i < vol_avg_i):                     # declining volume
            direction = 'short'

            raw_stop = high_i + STOP_ATR_BUFFER * atr_i
            min_stop = close_i + MIN_STOP_ATR * atr_i
            stop_price = max(raw_stop, min_stop)

            if stop_price <= close_i:
                continue

            risk = stop_price - close_i
            recent_swing_low = df['low'].iloc[i-SWING_LOOKBACK:i].min()
            target_t1 = recent_swing_low if recent_swing_low < close_i else close_i - 2 * risk
            target_t2 = None
        else:
            continue

        # ── Entry at t+1 open ──
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
            ema_j = ema20.iloc[j]

            if direction == 'long':
                # Stop check
                if bar['low'] <= stop_price:
                    exit_price = stop_price
                    exit_reason = 'stop'
                    exit_date = df.index[j]
                    break
                # T1 (50% at swing high)
                if not t1_exited and bar['high'] >= target_t1:
                    t1_exited = True
                # T2 trail: close crosses below 20-EMA
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
            'subperiod': df.iloc[i].get('subperiod', 'unknown') if 'subperiod' in df.columns else 'unknown',
        })

    return signals


def scan(df: pd.DataFrame, ticker: str, **kwargs) -> list:
    return scan_ticker(df, ticker)


if __name__ == "__main__":
    import json as json_module
    import argparse

    parser = argparse.ArgumentParser(description="STR-T1-02 ADX Trend Pullback Scanner")
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
        print(f"STR-T1-02 ADX Trend Pullback — Results")
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