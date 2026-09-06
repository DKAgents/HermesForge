#!/usr/bin/env python3
"""
scanner_equity_crypto_sentiment_divergence.py — STR-20260906-SENTIMENT-DIVERGENCE

Edge candidate: CAND-20260906-equity-crypto-sentiment-divergence
Source hypothesis: A near-record 38.5-point gap between equity Fear & Greed
(35.49 — Fear) and Crypto Fear & Greed (74 — Greed) is unsustainable and
historically resolves with equities catching up (Scenario A, 60% probability).

Signal Rules (batch / regime overlay):
  1. Compute equity fear proxy: VIX level above FEAR_VIX_THRESHOLD (fear regime)
     AND/OR S&P 500 below its 50-day MA (equity weakness).
  2. Compute crypto greed: crypto F&G index from alternative.me cache
     above FG_GREED_THRESHOLD.
  3. When divergence is active (equity_fear AND crypto_greed), generate a
     regime signal. No direct trade entry — this is a regime overlay.
  4. Test: forward 2-week SPY and BTC performance after divergence signals.

NOTE: This scanner cannot directly trade the divergence — it tests whether
the divergence signal predicts future equity/crypto returns. If Phase 1A
shows positive mean R, the signal can be deployed as a regime overlay
(e.g., reduce equity shorts when divergence fires).

Data sources:
  - Equity data (SPY, VIX) from main stock data dict
  - Crypto F&G from ~/.hermes/market_data/fear_greed.parquet
  - Crypto prices from crypto data dict

Dependencies: pandas, numpy.
"""

import numpy as np
import pandas as pd
from pathlib import Path

STRATEGY_ID = "STR-20260906-SENTIMENT-DIVERGENCE"

# ── Parameters ────────────────────────────────────────────────────────────────
FEAR_VIX_THRESHOLD = 20.0      # VIX above this = equity fear
FG_GREED_THRESHOLD = 65         # Crypto F&G above this = greed
SPY_MA_PERIOD = 50              # SPY below this = equity weakness
DIVERGENCE_SPREAD_MIN = 25      # Min point spread between equity fear & crypto greed
LOOKBACK_FWD = 10               # Forward test window (trading days)
ATR_PERIOD = 14
MIN_HISTORY = 60

_FG_CACHE = Path.home() / ".hermes" / "market_data" / "fear_greed.parquet"


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


def _load_fg() -> pd.DataFrame:
    if not _FG_CACHE.exists():
        return pd.DataFrame(columns=["date", "value"])
    fg = pd.read_parquet(_FG_CACHE)
    if "date" not in fg.columns:
        fg = fg.reset_index()
    fg["date"] = pd.to_datetime(fg["date"])
    fg = fg.sort_values("date").drop_duplicates("date", keep="last")
    return fg


def scan(data_dict: dict) -> list:
    """Batch scanner for equity-crypto sentiment divergence regime overlay.

    Args:
        data_dict: {ticker: DataFrame} of stock OHLCV.

    Returns:
        list of signal dicts measuring forward SPY/BTC performance after
        divergence signals.
    """
    if not data_dict:
        return []

    # Required tickers
    needed = {"SPY"}
    available = set(data_dict.keys())
    missing = needed - available
    if missing:
        return []

    # Load SPY data
    spy = data_dict["SPY"].copy()
    spy.columns = [c.lower() for c in spy.columns]
    spy.sort_index(inplace=True)

    spy_close = spy["close"] if "close" in spy.columns else spy.iloc[:, 3]
    spy_high = spy["high"] if "high" in spy.columns else spy.iloc[:, 1]
    spy_low = spy["low"] if "low" in spy.columns else spy.iloc[:, 2]
    spy_close_arr = spy_close.values.astype(float)
    spy_high_arr = spy_high.values.astype(float)

    # Try VIX from data dict or cache
    vix = None
    if "^VIX" in data_dict or "VIX" in data_dict:
        vix_key = "^VIX" if "^VIX" in data_dict else "VIX"
        vix_df = data_dict[vix_key].copy()
        vix_df.columns = [c.lower() for c in vix_df.columns]
        vix_df.sort_index(inplace=True)
        vix_close = vix_df["close"] if "close" in vix_df.columns else vix_df.iloc[:, 3]
        vix = vix_close
    else:
        # Try loading VIX from cache
        vix_path = Path.home() / ".hermes" / "market_data" / "^VIX.parquet"
        if vix_path.exists():
            vix_df = pd.read_parquet(vix_path)
            vix_df.columns = [c.lower() for c in vix_df.columns]
            vix_df.sort_index(inplace=True)
            vix = vix_df["close"] if "close" in vix_df.columns else vix_df.iloc[:, 3]

    # Load crypto F&G
    fg = _load_fg()
    if fg.empty:
        return []

    # ── Align all data ─────────────────────────────────────────────────────
    # SPY 50-day SMA
    spy_sma50 = spy_close.rolling(SPY_MA_PERIOD, min_periods=SPY_MA_PERIOD).mean()

    # ATR for exit simulation
    spy_atr = None
    if "high" in spy.columns and "low" in spy.columns:
        prior_close = spy_close.shift(1)
        tr = pd.concat([
            spy_high - spy_low,
            (spy_high - prior_close).abs(),
            (spy_low - prior_close).abs(),
        ], axis=1).max(axis=1)
        spy_atr = tr.ewm(alpha=1.0 / ATR_PERIOD, adjust=False).mean()

    # Build aligned index
    fg_idx = fg.set_index("date")["value"]

    signals = []
    n = len(spy_close)
    min_start = SPY_MA_PERIOD + 5

    for i in range(min_start, n):
        date = spy_close.index[i]

        # Equity fear conditions
        spy_below_sma = spy_close_arr[i] < (spy_sma50.iloc[i] if not pd.isna(spy_sma50.iloc[i]) else float('inf'))

        vix_fear = False
        if vix is not None and date in vix.index:
            vix_idx = vix.index.get_loc(date)
            vix_val = float(vix.iloc[vix_idx])
            if not pd.isna(vix_val) and vix_val >= FEAR_VIX_THRESHOLD:
                vix_fear = True

        equity_fear = spy_below_sma or vix_fear

        # Crypto greed
        fg_val = fg_idx.reindex([date]).iloc[0] if date in fg_idx.index else (
            fg_idx[fg_idx.index <= date].iloc[-1] if len(fg_idx[fg_idx.index <= date]) > 0 else np.nan
        )
        crypto_greed = not np.isnan(fg_val) and fg_val >= FG_GREED_THRESHOLD
        equity_fear_val = 100 - fg_val  # rough proxy: equity fear ~100 - crypto F&G
        spread = abs(fg_val - equity_fear_val) if not np.isnan(fg_val) else 0

        # Divergence signal: equity fear AND crypto greed AND significant spread
        if not (equity_fear and crypto_greed and spread >= DIVERGENCE_SPREAD_MIN):
            continue

        # Generate signal — test forward SPY performance
        entry_price = spy_close_arr[i]
        if entry_price == 0 or np.isnan(entry_price):
            continue

        # Compute forward return over LOOKBACK_FWD days
        fwd_end = min(i + LOOKBACK_FWD, n - 1)
        fwd_return = (spy_close_arr[fwd_end] - entry_price) / entry_price

        # R-multiple approximation: risk = ATR at entry
        atr_val = float(spy_atr.iloc[i]) if spy_atr is not None and i < len(spy_atr) and not pd.isna(spy_atr.iloc[i]) else entry_price * 0.02
        if atr_val <= 0:
            continue
        r_mult = fwd_return / (atr_val / entry_price)  # normalize returns by ATR%

        ts = pd.Timestamp(date)
        signals.append({
            "ticker": "SPY",
            "date": ts.date(),
            "direction": "long",
            "entry_price": round(float(entry_price), 2),
            "stop_price": round(float(entry_price * 0.95), 2),  # rough stop
            "target_price": round(float(entry_price * 1.03), 2),
            "exit_price": round(float(spy_close_arr[fwd_end]), 2),
            "exit_reason": "forward_window",
            "r_multiple": round(float(r_mult), 4),
            "bars_held": int(fwd_end - i),
            "subperiod": _subperiod(ts),
            "strategy_id": STRATEGY_ID,
            "regime": "sentiment_divergence",
            "entry_type": "divergence_signal",
            "fg_value": int(fg_val) if not np.isnan(fg_val) else 0,
            "vix_value": round(float(vix.iloc[vix.index.get_loc(date)]), 2) if vix is not None and date in vix.index else None,
            "spread": round(spread, 1),
        })

    return signals


# ── Smoke test ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    from pathlib import Path as _P

    sys.path.insert(0, str(_P(__file__).parent.parent))
    from fetch_data import load_all

    print("Loading stock data...")
    data = load_all()
    print(f"  {len(data)} tickers loaded")

    sigs = scan(data)
    print(f"\nEquity-Crypto Sentiment Divergence signals: {len(sigs)}")
    if sigs:
        r_vals = [s["r_multiple"] for s in sigs]
        wins = [s for s in sigs if s["r_multiple"] > 0]
        print(f"  Avg R: {np.mean(r_vals):+.4f}")
        print(f"  Win rate: {len(wins) / len(sigs):.1%}" if sigs else "  No signals")
        print(f"  Median R: {np.median(r_vals):+.4f}")
        print(f"\nFirst 3 signals:")
        for sig in sigs[:3]:
            print(f"  {sig['date']} | SPY ${sig['entry_price']:.2f} → ${sig['exit_price']:.2f} | "
                  f"R={sig['r_multiple']:+.4f} | F&G={sig['fg_value']} Spread={sig['spread']}")
    else:
        print("No signals generated. Check that SPY, VIX, and F&G cache are available.")