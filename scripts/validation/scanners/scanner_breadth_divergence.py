#!/usr/bin/env python3
"""
scanner_breadth_divergence.py — STR-20261001-BREADTH-DIVERGENCE

Edge candidate: CAND-20261001-breadth-divergence
Source: breadth scanner — "Bearish divergence: price moving one way, breadth the other"

Hypothesis: Breadth divergences often precede reversals. When price and breadth
move in opposite directions, enter trades in the divergence direction.

Signal Rules (batch mode):
  1. Compute daily breadth: % of universe above 50d MA (reliable breadth proxy)
  2. Compute SPY price trend over DIVERGENCE_WINDOW days
  3. Divergence: price direction flips while breadth moves opposite direction
  4. Per-ticker: long when bullish divergence + stock showing stability/recovery
                     short when bearish divergence + stock showing rollover
  5. Exit: stop below entry low / above entry high, target MIN_RR
"""

import numpy as np
import pandas as pd
from pathlib import Path

STRATEGY_ID = "STR-20261001-BREADTH-DIVERGENCE"

# ── Parameters ────────────────────────────────────────────────────────────────
DIVERGENCE_WINDOW = 10          # Days for computing price/breadth trend
BREADTH_MA = 50                 # MA period for breadth signal
MIN_BREADTH_SHIFT = 0.03        # Minimum breadth change to register
MIN_PRICE_MOVE_PCT = 0.01       # Minimum price move to consider direction change
VOL_AVG_PERIOD = 20
VOL_MULT = 1.0                  # Volume must be at least average
MIN_RR = 2.0
STOP_BUFFER_ATR = 0.5
MAX_ATR_PCT = 0.10
ATR_PERIOD = 14
MAX_BARS_HELD = 12
COOLDOWN_BARS = 5
MIN_HISTORY = 60

_CACHE_DIR = Path.home() / ".hermes" / "market_data"
_SPY_CACHE = _CACHE_DIR / "SPY.parquet"


def _subperiod(date) -> str:
    if pd.isna(date):
        return "unknown"
    d = date.date() if hasattr(date, "date") else date
    if d < pd.Timestamp("2019-04-01").date():
        return "pre_warmup"
    if d <= pd.Timestamp("2021-12-31").date():
        return "period1_bull"
    if d <= pd.Timestamp("2023-12-31").date():
        return "period2_bear"
    return "period3_current"


def _compute_atr(high, low, close, period=ATR_PERIOD):
    prior_close = close.shift(1)
    tr = pd.concat([
        high - low,
        (high - prior_close).abs(),
        (low - prior_close).abs(),
    ], axis=1).max(axis=1)
    return tr.ewm(alpha=1.0 / period, adjust=False).mean()


def _load_spy_close():
    """Load SPY close series from cache."""
    spy = pd.read_parquet(_SPY_CACHE)
    spy.columns = [c.lower() for c in spy.columns]
    spy = spy.sort_index()
    return spy["close"]


def scan(data_dict: dict) -> list:
    """Batch-mode scanner: breadth divergence → reversal trades.

    Args:
        data_dict: {ticker: DataFrame} of stock OHLCV (daily).

    Returns:
        list of signal dicts.
    """
    if not data_dict or len(data_dict) < 20:
        return []

    # ── Step 1: Compute breadth signals ───────────────────────────────────
    all_closes = {}
    for ticker, df in data_dict.items():
        if len(df) < MIN_HISTORY:
            continue
        df2 = df.copy()
        df2.columns = [c.lower() for c in df2.columns]
        close_col = df2.get("close", df2.iloc[:, 3])
        if isinstance(close_col, pd.Series) and len(close_col) >= MIN_HISTORY:
            all_closes[ticker] = close_col

    if len(all_closes) < 20:
        return []

    closes_df = pd.DataFrame(all_closes)
    # Align all to common index
    closes_df = closes_df.dropna(axis=1, how="all")

    # % above BREADTH_MA moving average
    ma_broad = closes_df.rolling(window=BREADTH_MA, min_periods=int(BREADTH_MA * 0.3)).mean()
    pct_above_ma = (closes_df > ma_broad).sum(axis=1) / closes_df.shape[1]

    # Price trend proxy: SPY close
    try:
        spy_close = _load_spy_close()
    except Exception:
        spy_close = closes_df.mean(axis=1)  # fallback
    spy_close = spy_close.reindex(closes_df.index).ffill()

    # ── Step 2: Detect divergence regimes ─────────────────────────────────
    # Price trend over DIVERGENCE_WINDOW
    spy_move = spy_close.diff(DIVERGENCE_WINDOW)
    spy_move_pct = spy_move / spy_close.shift(DIVERGENCE_WINDOW)

    # Price direction changes: the 10d trend has FLIPPED compared to the
    # 10d trend DIVERGENCE_WINDOW days ago (changing direction)
    spy_trend_now = np.sign(spy_move_pct)
    spy_trend_before = np.sign(spy_move_pct.shift(DIVERGENCE_WINDOW))

    # Breadth trend
    breadth_change = pct_above_ma.diff(DIVERGENCE_WINDOW)

    # Bullish divergence: price was falling (negative trend), now rising (positive)
    # AND breadth was contracting but now expanding (reversal setup)
    # Or simpler: price has reversed from down to up while breadth is still contracting
    # → the breadth will catch up, providing upside for stocks showing relative strength

    # Bearish divergence: price was rising, now falling, breadth still elevated
    # → the breadth will contract further, providing downside for weak stocks

    # Detect: price moving UP and breadth contracting → BEARISH (shorts)
    # Detect: price moving DOWN and breadth expanding → BULLISH (longs)
    price_down_smooth = spy_move_pct.rolling(window=3, min_periods=1).mean() < -MIN_PRICE_MOVE_PCT
    price_up_smooth = spy_move_pct.rolling(window=3, min_periods=1).mean() > MIN_PRICE_MOVE_PCT
    breadth_contracting = breadth_change.rolling(window=3, min_periods=1).mean() < -MIN_BREADTH_SHIFT
    breadth_expanding = breadth_change.rolling(window=3, min_periods=1).mean() > MIN_BREADTH_SHIFT

    bearish_div = price_up_smooth & breadth_contracting
    bullish_div = price_down_smooth & breadth_expanding

    # Must have at least 2 consecutive divergence days for signal
    bearish_active = bearish_div.astype(int).rolling(2, min_periods=1).sum() >= 2
    bullish_active = bullish_div.astype(int).rolling(2, min_periods=1).sum() >= 2

    # ── Step 3: Per-ticker scanning ───────────────────────────────────────
    signals = []

    for ticker, df_raw in data_dict.items():
        if len(df_raw) < MIN_HISTORY:
            continue

        df = df_raw.copy()
        df.columns = [c.lower() for c in df.columns]
        df.sort_index(inplace=True)

        close = df.get("close", df.iloc[:, 3])
        high = df.get("high", df.iloc[:, 1])
        low = df.get("low", df.iloc[:, 2])
        volume = df.get("volume", df.get("vol", pd.Series(1.0, index=df.index)))
        if not isinstance(volume, pd.Series):
            volume = pd.Series(1.0, index=df.index)
        dates = df.index

        atr_series = _compute_atr(high, low, close)
        vol_avg = volume.rolling(window=VOL_AVG_PERIOD, min_periods=5).mean()

        # Align signals
        bearish_idx = bearish_active.reindex(dates).fillna(False).values
        bullish_idx = bullish_active.reindex(dates).fillna(False).values

        close_arr = close.values
        high_arr = high.values
        low_arr = low.values
        vol_arr = volume.values
        atr_arr = atr_series.values
        vol_avg_arr = vol_avg.values

        # Compute rolling min/max for entry criteria
        rolling_min5 = pd.Series(low_arr).rolling(5, min_periods=1).min().values
        rolling_max5 = pd.Series(high_arr).rolling(5, min_periods=1).max().values

        last_signal = -COOLDOWN_BARS

        for i in range(DIVERGENCE_WINDOW + BREADTH_MA + 10, len(dates) - 1):
            if i - last_signal < COOLDOWN_BARS:
                continue

            price = close_arr[i]

            if np.isnan(atr_arr[i]) or atr_arr[i] / price > MAX_ATR_PCT:
                continue

            # Volume check
            if vol_avg_arr[i] > 0 and vol_arr[i] < VOL_MULT * vol_avg_arr[i]:
                continue

            direction = None

            if bearish_idx[i]:
                # Bearish divergence: price up, breadth contracting
                # Look for stocks that are ROLLING OVER (relative weakness)
                # The stock's close should be dropping from prior days
                if close_arr[i] >= close_arr[i-1]:
                    continue  # not yet rolling over
                if close_arr[i] >= rolling_max5[i-1]:
                    continue  # still near highs

                direction = "short"
                entry_price = price
                # Stop above recent highs
                stop_price = max(high_arr[i-3:i+1].max() if i >= 3 else high_arr[i], high_arr[i])
                risk = stop_price - entry_price
                if risk <= 0 or risk / entry_price < 0.002:
                    continue
                target_price = entry_price - MIN_RR * risk

            elif bullish_idx[i]:
                # Bullish divergence: price down, breadth expanding
                # Look for stocks that are STABILIZING (relative strength)
                if low_arr[i] < rolling_min5[i-1]:
                    continue  # still making new lows
                if close_arr[i] <= close_arr[i-1]:
                    continue  # still dropping

                direction = "long"
                entry_price = price
                stop_price = min(low_arr[i-3:i+1].min() if i >= 3 else low_arr[i], low_arr[i])
                risk = entry_price - stop_price
                if risk <= 0 or risk / entry_price < 0.002:
                    continue
                target_price = entry_price + MIN_RR * risk

            else:
                continue

            # Simulate exit forward
            ep = float(close_arr[min(i + MAX_BARS_HELD, len(dates) - 1)])
            er = "time"
            bh = MAX_BARS_HELD
            for offset in range(1, MAX_BARS_HELD + 1):
                idx = i + offset
                if idx >= len(dates):
                    ep = float(close_arr[-1])
                    er = "time"
                    bh = offset - 1
                    break
                c = float(close_arr[idx])
                if direction == "long":
                    if c >= target_price:
                        ep, er, bh = c, "target", offset
                        break
                    if c <= stop_price:
                        ep, er, bh = c, "stop", offset
                        break
                else:
                    if c <= target_price:
                        ep, er, bh = c, "target", offset
                        break
                    if c >= stop_price:
                        ep, er, bh = c, "stop", offset
                        break

            if direction == "short":
                r_mult = (entry_price - ep) / risk
            else:
                r_mult = (ep - entry_price) / risk

            ts = pd.Timestamp(dates[i])
            signals.append({
                "ticker": ticker,
                "date": ts.date(),
                "direction": direction,
                "entry_price": round(float(entry_price), 4),
                "stop_price": round(float(stop_price), 4),
                "target_price": round(float(target_price), 4),
                "exit_price": round(float(ep), 4),
                "exit_reason": er,
                "r_multiple": round(float(r_mult), 4),
                "bars_held": int(bh),
                "subperiod": _subperiod(ts),
                "strategy_id": STRATEGY_ID,
                "divergence_type": "bearish" if direction == "short" else "bullish",
            })
            last_signal = i

    return signals


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from fetch_data import load_all
    data = load_all()
    sigs = scan(data)
    print(f"Breadth Divergence: {len(sigs)} signals")
    if sigs:
        r_vals = [s["r_multiple"] for s in sigs]
        wr = sum(1 for r in r_vals if r > 0) / len(r_vals)
        longs = sum(1 for s in sigs if s["direction"] == "long")
        shorts = sum(1 for s in sigs if s["direction"] == "short")
        print(f"  Mean R: {np.mean(r_vals):.4f}")
        print(f"  Win rate: {wr:.1%}")
        print(f"  Longs: {longs}, Shorts: {shorts}")