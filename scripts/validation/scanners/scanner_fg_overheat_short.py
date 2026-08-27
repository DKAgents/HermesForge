#!/usr/bin/env python3
"""
scanner_fg_overheat_short.py — HermesForge Phase 1A / Walk-Forward

Edge candidate: CAND-20260827-crypto-fg80-contrarian-warning
Source hypothesis: Extreme Crypto Fear & Greed readings (>75, "Extreme Greed")
have been reliable contrarian short-term warning signals for BTC. When the
crowd is excessively greedy, mean-reversion follows within 1-4 weeks.

Signal Rules (BTC-only, batch mode):
  1. Load Crypto Fear & Greed Index (cached parquet, forward-filled).
  2. On any day where F&G > FG_ENTRY (>75), enter SHORT BTC at close.
  3. Exit on the first subsequent day where ANY of:
       * F&G <= FG_EXIT (<50)      — sentiment normalisation
       * price hits stop           — 1.5x ATR below entry (for shorts: above)
       * price hits target         — 2.0x risk (MIN_RR)
       * MAX_BARS_HELD reached     — 20 bars (~4 weeks)
  4. One signal record per completed trade with realised R-multiple.

Dependencies: pandas, numpy. BTC from crypto parquet cache; F&G from
~/.hermes/market_data/fear_greed.parquet. Funding-rate confirmation (VanEck
99th %ile) is NOT included because historical funding-rate cache only holds
7 days — see "funding confirmation" as a post-deployment enhancement.

Survivorship caveat (ADR-004): BTC is the dominant crypto and is unlikely
to be delisted, so survivorship bias is negligible for a single-ticker test.
"""

import numpy as np
import pandas as pd
from pathlib import Path

STRATEGY_ID = "STR-20260827-FG-OVERHEAT-SHORT"

# ── Parameters (module-level; walk-forward monkey-patches) ─────────────
FG_ENTRY = 75           # Enter short when F&G > this (Extreme Greed)
FG_EXIT = 50            # Exit short when F&G <= this (back to Fear/Neutral)
ATR_PERIOD = 14
ATR_STOP_MULT = 1.5     # Stop = entry + ATR_STOP_MULT * ATR (short: above entry)
MIN_RR = 2.0            # Target = entry - MIN_RR * risk
MAX_BARS_HELD = 20      # ~4 weeks time stop
MIN_HISTORY = 60        # Need >= this many BTC bars

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


def _compute_atr(df, period=ATR_PERIOD):
    """Compute ATR for a ticker DataFrame (must have high/low/close)."""
    close = df["close"]
    high = df["high"]
    low = df["low"]
    prior_close = close.shift(1)
    tr = pd.concat([
        high - low,
        (high - prior_close).abs(),
        (low - prior_close).abs(),
    ], axis=1).max(axis=1)
    return tr.ewm(alpha=1.0 / period, adjust=False).mean()


def scan(data: dict, latest_only: bool = False) -> list:
    """
    Batch scan: short BTC when Crypto F&G is in Extreme Greed (>75).

    Args:
        data: {ticker: DataFrame} crypto OHLCV dict from load_all().
              Must contain "BTC".
        latest_only: If True, only return signals from the most recent bar.

    Returns:
        List of signal dicts with keys: ticker, date, direction, entry_price,
        stop_price, target_price, exit_price, exit_reason, r_multiple,
        bars_held, subperiod, strategy_id.
    """
    if "BTC" not in data:
        return []

    btc_df = data["BTC"].copy().sort_index()
    if len(btc_df) < max(ATR_PERIOD, MIN_HISTORY):
        return []

    fg = _load_fg()
    if fg.empty:
        return []

    # Align F&G to BTC daily dates (forward-fill)
    fg_idx = fg.set_index("date")["value"]
    fg_aligned = fg_idx.reindex(btc_df.index, method="ffill")

    # Compute ATR on BTC
    atr_series = _compute_atr(btc_df)
    atr_arr = atr_series.values

    close = btc_df["close"]
    close_arr = close.values
    high = btc_df["high"].values
    low = btc_df["low"].values
    dates = btc_df.index
    n = len(btc_df)

    signals = []
    open_pos = {}  # ticker -> dict(entry_idx, entry_price, stop, target, entry_date)

    for i in range(len(btc_df)):
        date = dates[i]
        fg_val = fg_aligned.iloc[i] if i < len(fg_aligned) else np.nan

        # ── Check exits on currently open positions ──────────────
        for ticker in list(open_pos.keys()):
            # We only trade BTC, but keep the dict pattern for consistency
            pos = open_pos[ticker]
            # Use this BTC bar's close for exit simulation
            current_price = close_arr[i]
            entry_price = pos["entry_price"]
            stop_price = pos["stop_price"]
            target_price = pos["target_price"]
            bars_held = i - pos["entry_idx"]

            exit_reason = None
            exit_price = current_price

            # F&G exit (sentiment normalisation)
            if not np.isnan(fg_val) and fg_val <= FG_EXIT:
                exit_reason = "fg_exit"
            # Stop loss (short: stop is above entry, price rises to hit it)
            elif current_price >= stop_price:
                exit_reason = "stop"
            # Target (short: target below entry, price falls to hit it)
            elif current_price <= target_price:
                exit_reason = "target"
            # Time stop
            elif bars_held >= MAX_BARS_HELD:
                exit_reason = "time"

            if exit_reason is not None:
                risk = stop_price - entry_price  # positive for shorts
                realised_r = (entry_price - current_price) / risk if risk > 0 else 0.0
                signals.append({
                    "ticker": ticker,
                    "date": pos["entry_date"],
                    "direction": "short",
                    "entry_price": round(float(entry_price), 2),
                    "stop_price": round(float(stop_price), 2),
                    "target_price": round(float(target_price), 2),
                    "exit_price": round(float(current_price), 2),
                    "exit_reason": exit_reason,
                    "r_multiple": round(float(realised_r), 4),
                    "bars_held": int(bars_held),
                    "subperiod": _subperiod(pos["entry_date"]),
                    "strategy_id": STRATEGY_ID,
                })
                del open_pos[ticker]

        # ── Entries: only when F&G > FG_ENTRY (Extreme Greed) ────
        if np.isnan(fg_val) or fg_val <= FG_ENTRY:
            continue

        # Skip if we already have an open position on BTC
        if "BTC" in open_pos:
            continue

        # Need ATR for stop placement
        if i < ATR_PERIOD or np.isnan(atr_arr[i]) or atr_arr[i] <= 0:
            continue

        entry_price = close_arr[i]
        atr_val = atr_arr[i]

        # Short: stop above entry (1.5x ATR), target below entry (2x risk)
        stop_price = entry_price + ATR_STOP_MULT * atr_val
        risk = stop_price - entry_price  # positive for shorts
        if risk <= 0 or risk / entry_price < 0.002:
            continue
        target_price = entry_price - MIN_RR * risk

        open_pos["BTC"] = {
            "entry_idx": i,
            "entry_price": entry_price,
            "stop_price": stop_price,
            "target_price": target_price,
            "entry_date": date,
        }

    # ── Force-close any still-open positions at last close ─────────
    for ticker, pos in list(open_pos.items()):
        j = n - 1
        price = close_arr[j]
        risk = pos["stop_price"] - pos["entry_price"]
        realised_r = (pos["entry_price"] - price) / risk if risk > 0 else 0.0
        signals.append({
            "ticker": ticker,
            "date": pos["entry_date"],
            "direction": "short",
            "entry_price": round(float(pos["entry_price"]), 2),
            "stop_price": round(float(pos["stop_price"]), 2),
            "target_price": round(float(pos["target_price"]), 2),
            "exit_price": round(float(price), 2),
            "exit_reason": "end_of_data",
            "r_multiple": round(float(realised_r), 4),
            "bars_held": int(j - pos["entry_idx"]),
            "subperiod": _subperiod(pos["entry_date"]),
            "strategy_id": STRATEGY_ID,
        })

    # Filter for latest_only (paper trading daily capture)
    if latest_only and signals:
        latest_date = max(s["date"] for s in signals)
        signals = [s for s in signals if s["date"] == latest_date]

    return signals


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent.parent / "paper_trading"))
    try:
        from fetch_crypto_data import load_all
    except Exception as e:
        print(f"[ERROR] cannot import crypto loader: {e}")
        sys.exit(1)
    data = load_all()
    print(f"Loaded {len(data)} crypto tickers")
    sigs = scan(data)
    print(f"Signals: {len(sigs)}")
    if sigs:
        df = pd.DataFrame(sigs)
        print(f"  R-multiple stats:")
        print(df["r_multiple"].describe())
        win_rate = (df["r_multiple"] > 0).mean()
        print(f"  Win rate: {win_rate:.1%}")
        mean_r = df["r_multiple"].mean()
        print(f"  Mean R: {mean_r:.4f}")
        # By subperiod
        for sp in sorted(df["subperiod"].unique()):
            sub = df[df["subperiod"] == sp]
            print(f"  {sp}: {len(sub)} sigs, mean R = {sub['r_multiple'].mean():+.4f}")