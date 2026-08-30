"""
scanner_btc_dominance_inflection.py — STR-BTC-DOM: BTC Dominance Cycle Inflection

Built from CAND-20260830-btc-dominance-inflection.

Hypothesis (H2 — bearish):
  When BTC has strongly outperformed ETH over the trailing period (proxying
  BTC.D rising to extreme levels), the crypto market is near a cycle top.
  BTC dominance near cycle highs historically either signals:
    H1: Imminent rotation into alts (bullish for ETH/SOL)
    H2: Cycle top, everything falls (bearish for BTC)

  This scanner tests H2: BTC outperformance extreme → forward BTC weakness.

Signal Rules:
  1. Compute BTC/ETH ratio over trailing 30 days as proxy for BTC.D
  2. When BTC/ETH ratio is at 90th+ percentile of its 1-year history
     AND BTC has rallied > 15% over 30 days
  3. Generate SHORT signal on BTC
  4. Exit: target hit, stop hit, or max 10 bars

NOTE: This is a SPECULATIVE candidate. BTC.D data is not directly available
in our pipeline (requires CoinMarketCap total market cap). BTC/ETH ratio
is used as a proxy. Sample size is limited.

Dependencies: pandas, numpy only.
"""

import numpy as np
import pandas as pd

STRATEGY_ID = "STR-BTC-DOM"

# ── Parameters (parameterizable) ─────────────────────────────────────────────
BTC_RALLY_PCT = 15.0          # BTC must have rallied > this % over TRAILING days
TRAILING_DAYS = 30             # Trailing window for BTC return and ratio
RATIO_PERCENTILE = 90          # BTC/ETH ratio must be above this percentile of 1yr history
ATR_PERIOD = 14
ATR_STOP_MULT = 1.0
MIN_RR = 1.5
MAX_HOLD = 10
HISTORY_LOOKBACK = 365         # 1 year for ratio percentile


def _subperiod(date) -> str:
    """Classify a date into ADR-004 sub-periods using crypto dating."""
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


def _compute_atr(high: pd.Series, low: pd.Series, close: pd.Series,
                  period: int = ATR_PERIOD) -> pd.Series:
    """Average True Range (Wilder's smoothing)."""
    prev_close = close.shift(1)
    tr = pd.concat([
        high - low,
        (high - prev_close).abs(),
        (low - prev_close).abs(),
    ], axis=1).max(axis=1)
    return tr.ewm(alpha=1.0 / period, adjust=False).mean()


def _simulate_exit(
    closes: np.ndarray,
    entry_idx: int,
    entry_price: float,
    stop_price: float,
    target_price: float,
    direction: str,
    max_bars: int = MAX_HOLD,
) -> tuple:
    n = len(closes)
    for offset in range(1, max_bars + 1):
        idx = entry_idx + offset
        if idx >= n:
            last = min(entry_idx + offset - 1, n - 1)
            return closes[last], "time", offset
        c = closes[idx]
        if direction == "short":
            if c <= target_price:
                return c, "target", offset
            if c >= stop_price:
                return c, "stop", offset
        else:
            if c >= target_price:
                return c, "target", offset
            if c <= stop_price:
                return c, "stop", offset
    exit_idx = min(entry_idx + max_bars, n - 1)
    return closes[exit_idx], "time", max_bars


def scan(data: dict[str, pd.DataFrame]) -> list[dict]:
    """
    Batch scanner: checks BTC/ETH ratio extreme and generates BTC short signals.

    Parameters
    ----------
    data : dict[str, pd.DataFrame]
        Dict of {ticker: OHLCV DataFrame} for the crypto universe.

    Returns
    -------
    list of dict, one per signal
    """
    needed = {"BTC", "ETH"}
    available = set(data.keys())
    missing = needed - available
    if missing:
        raise ValueError(f"Missing tickers in data dict: {missing}")

    btc = data["BTC"].copy()
    eth = data["ETH"].copy()

    for df in [btc, eth]:
        df.columns = df.columns.str.lower()
        df.sort_index(inplace=True)

    btc_close = btc["close"]
    btc_high = btc["high"]
    eth_close = eth["close"]

    # BTC/ETH ratio
    ratio = btc_close / eth_close

    # BTC trailing return
    btc_ret = btc_close.pct_change(periods=TRAILING_DAYS) * 100

    # Ratio percentile: rolling 1-year rank
    ratio_rank = ratio.rolling(window=HISTORY_LOOKBACK).apply(
        lambda x: (x[-1] >= x).mean() * 100, raw=True
    )

    # ATR
    btc_atr = _compute_atr(btc["high"], btc["low"], btc_close, period=ATR_PERIOD)

    # Align
    common = btc_close.index.intersection(eth_close.index)
    btc_close_a = btc_close.loc[common]
    btc_high_a = btc_high.loc[common]
    btc_ret_a = btc_ret.loc[common]
    ratio_rank_a = ratio_rank.loc[common]
    btc_atr_a = btc_atr.loc[common]

    btc_close_arr = btc_close_a.values.astype(float)
    btc_high_arr = btc_high_a.values.astype(float)
    btc_ret_arr = btc_ret_a.values.astype(float)
    ratio_rank_arr = ratio_rank_a.values.astype(float)
    btc_atr_arr = btc_atr_a.values.astype(float)

    signals: list[dict] = []

    min_start = HISTORY_LOOKBACK + TRAILING_DAYS + ATR_PERIOD + 2

    for i in range(min_start, len(common)):
        if (np.isnan(btc_ret_arr[i]) or np.isnan(ratio_rank_arr[i]) or
                np.isnan(btc_atr_arr[i])):
            continue

        # Signal: BTC rallied > threshold AND BTC/ETH ratio at extreme percentile
        if btc_ret_arr[i] > BTC_RALLY_PCT and ratio_rank_arr[i] >= RATIO_PERCENTILE:
            entry_price = btc_close_arr[i]
            if entry_price == 0 or np.isnan(entry_price):
                continue

            atr_val = btc_atr_arr[i]
            if atr_val == 0 or np.isnan(atr_val):
                continue

            # Short BTC (H2: cycle top)
            stop_price = btc_high_arr[i] + ATR_STOP_MULT * atr_val
            risk = stop_price - entry_price
            if risk <= 0:
                continue

            reward = 2.0 * risk
            target_price = entry_price - reward
            rr = reward / risk
            if rr < MIN_RR:
                continue

            ep, er, bh = _simulate_exit(
                btc_close_arr, i, entry_price, stop_price, target_price, "short"
            )
            r_mult = (entry_price - ep) / risk
            ts = pd.Timestamp(str(common[i]))

            signals.append({
                "ticker":       "BTC",
                "date":         ts.date(),
                "entry_price":  round(entry_price, 4),
                "stop_price":   round(stop_price, 4),
                "target_price": round(target_price, 4),
                "direction":    "short",
                "exit_price":   round(ep, 4),
                "exit_reason":  er,
                "bars_held":    bh,
                "r_multiple":   round(r_mult, 4),
                "subperiod":    _subperiod(ts),
                "strategy_id":  STRATEGY_ID,
            })

    return signals


# --------------------------------------------------------------------------- #
# __main__ : quick smoke test
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "paper_trading"))
    from fetch_crypto_data import load_all
    print("Loading cached crypto data...")
    crypto_data = load_all()
    if not crypto_data:
        print("ERROR: No cached crypto data.", file=sys.stderr)
        sys.exit(1)
    print(f"Loaded {len(crypto_data)} crypto tickers.")

    results = scan(crypto_data)
    print(f"\nBTC Dominance signals found: {len(results)}")
    if results:
        print("\nFirst 3 signals:")
        for sig in results[:3]:
            for k, v in sig.items():
                print(f"  {k:25s}: {v}")
            print()