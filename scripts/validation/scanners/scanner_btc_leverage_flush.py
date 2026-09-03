#!/usr/bin/env python3
"""
scanner_btc_leverage_flush.py — STR-BTC-FLUSH: BTC Leverage Flush Transition
================================================================================

Edge candidate: CAND-20260903-btc-leverage-flush-transition
Source hypothesis: "A leverage flush in BTC (5-15% drop) is the most probable
near-term resolution when F&G is in Greed territory (>65) and price action is
flat (no decisive breakout). The 'transition' state with competing forces
(institutional inflows + rising leverage + STH distribution) creates
vulnerability to a flush."

SIMPLIFIED TEST (Phase 1A proxy):
  Since we lack historical OI and funding rate data in our cache, this scanner
  tests the testable core: BTC short when F&G > FG_ENTRY (Greed) AND trailing
  7-day return is flat (BTC_FLAT_MIN .. BTC_FLAT_MAX percent). The idea is
  that "optimism without follow-through" (Greed + flat price) precedes a flush.

Signal Rules:
  - Load BTC OHLCV from crypto data dict + F&G from cached parquet
  - On any date where F&G > FG_ENTRY AND BTC 7d return ∈ [BTC_FLAT_MIN, BTC_FLAT_MAX]
    (flat/choppy price), generate SHORT on BTC.
  - Exit: stop = entry + ATR_STOP_MULT * ATR(14); target = entry - MIN_RR * risk;
    max hold = MAX_BARS_HELD. Forced close at end of data.
  - One signal record per completed trade with realised R-multiple.

Survivorship: N/A — single-ticker BTC, directly traded on Hyperliquid.
Transaction costs NOT modeled (Phase 1A is frictionless).
"""

import numpy as np
import pandas as pd
from pathlib import Path

STRATEGY_ID = "STR-20260903-BTC-LEVERAGE-FLUSH"

# ── Parameters (module-level; walk-forward can monkey-patch) ─────────────────
FG_ENTRY       = 65    # F&G must be > this (Greed zone)
BTC_FLAT_MIN   = -2.0  # 7d return lower bound (%) — not in large downtrend
BTC_FLAT_MAX   = 2.0   # 7d return upper bound (%) — not in strong breakout
TRAILING_DAYS  = 7     # lookback for flat price detection
ATR_PERIOD     = 14
ATR_STOP_MULT  = 1.0   # stop = entry + ATR_STOP_MULT * ATR(14)
MIN_RR         = 2.0   # target = entry - MIN_RR * risk
MAX_BARS_HELD  = 10    # time stop (max ~2 trading weeks)

_FG_CACHE = Path.home() / ".hermes" / "market_data" / "fear_greed.parquet"


def _subperiod(date) -> str:
    if pd.isna(date):
        return "unknown"
    d = date.date() if hasattr(date, "date") else date
    if d < pd.Timestamp("2020-08-19").date():
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


def _compute_atr(high: pd.Series, low: pd.Series, close: pd.Series,
                 period: int = ATR_PERIOD) -> pd.Series:
    prev_close = close.shift(1)
    tr = pd.concat([
        high - low,
        (high - prev_close).abs(),
        (low - prev_close).abs(),
    ], axis=1).max(axis=1)
    return tr.ewm(alpha=1.0 / period, adjust=False).mean()


def scan(data: dict[str, pd.DataFrame]) -> list[dict]:
    """
    Batch scanner: single-ticker BTC short on Greed+Flat regime.

    Args:
        data: dict of {ticker: OHLCV DataFrame} for the crypto universe.

    Returns:
        List of signal dicts with entry/exit details.
    """
    if not data:
        return []

    if "BTC" not in data:
        return []

    # Load F&G
    fg = _load_fg()
    if fg.empty:
        return []

    btc = data["BTC"].copy()
    btc.columns = [c.lower() for c in btc.columns]
    btc.sort_index(inplace=True)

    if len(btc) < TRAILING_DAYS + ATR_PERIOD + MAX_BARS_HELD + 5:
        return []

    close = btc["close"]
    high = btc["high"]
    low = btc["low"]

    # 7-day trailing return (pct)
    ret_7d = close.pct_change(periods=TRAILING_DAYS) * 100.0

    # ATR
    atr = _compute_atr(high, low, close, ATR_PERIOD)

    # Align F&G to BTC date index (forward-fill weekends/holidays)
    fg_idx = fg.set_index("date")["value"]
    fg_aligned = fg_idx.reindex(btc.index).ffill()

    signals = []
    dates = btc.index
    n = len(dates)

    min_start = max(TRAILING_DAYS, ATR_PERIOD) + 2

    for i in range(min_start, n):
        date = dates[i]
        fg_val = fg_aligned.iloc[i] if i < len(fg_aligned) else np.nan

        if np.isnan(fg_val) or fg_val <= FG_ENTRY:
            continue

        ret = ret_7d.iloc[i]
        if np.isnan(ret):
            continue

        # Flat/choppy price — not in downtrend, not breaking out
        if not (BTC_FLAT_MIN <= ret <= BTC_FLAT_MAX):
            continue

        entry_price = float(close.iloc[i])
        if entry_price <= 0 or np.isnan(entry_price):
            continue

        atr_val = float(atr.iloc[i])
        if atr_val <= 0 or np.isnan(atr_val):
            continue

        # Short BTC: optimism without follow-through → flush
        stop_price = entry_price + ATR_STOP_MULT * atr_val
        risk = stop_price - entry_price
        if risk <= 0:
            continue

        target_price = entry_price - MIN_RR * risk

        # Simulate exit
        close_arr = close.values.astype(float)
        ep, er, bh = _simulate_exit(close_arr, i, entry_price,
                                    stop_price, target_price, MAX_BARS_HELD)

        r_mult = (entry_price - ep) / risk
        ts = dates[i]

        signals.append({
            "ticker":       "BTC",
            "date":         ts.date() if hasattr(ts, "date") else str(ts)[:10],
            "entry_price":  round(float(entry_price), 2),
            "stop_price":   round(float(stop_price), 2),
            "target_price": round(float(target_price), 2),
            "direction":    "short",
            "exit_price":   round(float(ep), 2),
            "exit_reason":  er,
            "bars_held":    bh,
            "r_multiple":   round(float(r_mult), 4),
            "subperiod":    _subperiod(ts),
            "strategy_id":  STRATEGY_ID,
        })

    return signals


def _simulate_exit(
    closes: np.ndarray,
    entry_idx: int,
    entry_price: float,
    stop_price: float,
    target_price: float,
    max_bars: int,
) -> tuple:
    n = len(closes)
    for offset in range(1, max_bars + 1):
        idx = entry_idx + offset
        if idx >= n:
            last = min(n - 1, entry_idx + offset - 1)
            return closes[last], "end_of_data", offset
        c = closes[idx]
        if c <= target_price:
            return c, "target", offset
        if c >= stop_price:
            return c, "stop", offset
    exit_idx = min(entry_idx + max_bars, n - 1)
    return closes[exit_idx], "time", max_bars


# ── __main__ : quick smoke test ───────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "paper_trading"))
    from fetch_crypto_data import load_all as load_all_crypto

    print("Loading crypto data + F&G...")
    crypto = load_all_crypto()
    print(f"  {len(crypto)} symbols loaded, BTC present: {'BTC' in crypto}")

    sigs = scan(crypto)
    print(f"\nSTR-BTC-FLUSH signals: {len(sigs)}")
    if sigs:
        r_vals = [s["r_multiple"] for s in sigs]
        print(f"  Avg R: {np.mean(r_vals):+.4f}")
        print(f"  Win rate: {sum(1 for r in r_vals if r > 0) / len(r_vals):.1%}")
        print(f"  Total trades: {len(sigs)}")
        print("\nFirst 3 signals:")
        for s in sigs[:3]:
            print(f"  {s['date']} BTC SHORT @ {s['entry_price']} -> {s['exit_price']} "
                  f"({s['exit_reason']}), R={s['r_multiple']:+.4f}")
    else:
        print("  No signals generated (check F&G is cached and BTC data exists)")