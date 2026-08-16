#!/usr/bin/env python3
"""
scanner_crypto_fg_contrarian.py
================================
HermesForge Phase 1A — Crypto Fear-&-Greed Contrarian Basket (long only).

Edge candidate: CAND-20260816-cross-asset-sentiment-divergence
Source hypothesis: "When crypto F&G is in Fear (<40) while equities are Greedy,
crypto tends to mean-revert upward within 2-4 weeks. Low funding confirms no
overcrowded longs — contrarian bullish."

NOTE on scope / data limitation: the full cross-asset divergence requires
historical *equity* Fear & Greed (CNN), which is not historically cached in
this repo. This scanner therefore tests the testable core of the hypothesis —
Strategy C from the candidate: "Long top-N crypto by 30d momentum when crypto
F&G < 35 (Fear). Exit when F&G > 55 or individual stop at -8%." This is a
crypto-F&G-gated contrarian basket. The cross-asset divergence overlay is
documented as a future enhancement once equity F&G history is available. The
candidate's own "Recommended Pipeline Action" flags this as PROMISING with
medium confidence; we test the proxy and tag accordingly.

Signal Rules (batch / cross-sectional):
  - Crypto F&G (alternative.me, daily, cached) is aligned to each crypto's
    trading dates (forward-fill; crypto trades 24/7 but F&G updates daily).
  - On any day where F&G < FG_ENTRY (Fear zone), rank the crypto universe by
    30-day return and select the top N momentum names that are NOT already in
    an open position. Enter LONG on the close of that day.
  - No new entries while F&G >= FG_ENTRY.
  - Exit an open position on the first subsequent day where ANY of:
      * F&G >= FG_EXIT          (sentiment regime exit, candidate: 55)
      * price hits the -8% stop  (candidate: individual stop at -8%)
      * price hits the +MIN_RR target
      * MAX_BARS_HELD reached    (time stop, candidate says "2-4 weeks")
  - One signal record is emitted per completed trade, with realised R-multiple.

Dependencies: pandas, numpy. Crypto OHLCV from the cached crypto parquet dir
(passed in as `data_dict` by the runner); F&G loaded from
~/.hermes/market_data/fear_greed.parquet.

Survivorship caveat (ADR-004): the crypto universe is current Hyperliquid
markets; delisted coins (e.g., MATIC, FTM) were already filtered by the
loader, which can flatter the cross-sectional momentum signal.
Transaction costs are NOT modeled here — Phase 1A is frictionless; walk-forward
applies spread+commission+gap costs.
"""

import numpy as np
import pandas as pd
from pathlib import Path

STRATEGY_ID = "STR-20260816-CRYPTO-FG-CONTRARIAN"

# ── Parameters (module-level; walk-forward monkey-patches these) ─────────────
FG_ENTRY = 35          # enter only when F&G < this (Fear zone)
FG_EXIT = 55           # regime exit when F&G rises above this
MOMENTUM_LOOKBACK = 30 # 30-day return rank
TOP_N = 5              # top-N momentum names to hold
STOP_PCT = 0.08        # -8% individual stop
MIN_RR = 2.0           # target = entry + MIN_RR * risk (risk = 8% stop distance)
MAX_BARS_HELD = 21     # ~3-week time stop (candidate: 2-4 weeks)
MIN_HISTORY = 60       # need >= this many bars of history to compute momentum

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
        # some caches index by date
        fg = fg.reset_index()
    fg["date"] = pd.to_datetime(fg["date"])
    fg = fg.sort_values("date").drop_duplicates("date", keep="last")
    return fg


def scan(data_dict: dict) -> list:
    """Batch scan: contrarian crypto-basket longs gated by Fear & Greed.

    Args:
        data_dict: {ticker: DataFrame} of crypto OHLCV (daily). Pass-through
        argument from the runner (run_phase1a --crypto passes the crypto
        universe; walk-forward passes a sliced crypto dict).
    """
    if not data_dict:
        return []

    fg = _load_fg()
    if fg.empty:
        return []

    # Build a unified daily close grid across the crypto universe
    closes = {}
    for ticker, df in data_dict.items():
        d = df.copy()
        d.sort_index(inplace=True)
        if len(d) < MIN_HISTORY:
            continue
        c = d["close"] if "close" in d.columns else d.iloc[:, 0]
        closes[ticker] = c

    if not closes:
        return []

    close_grid = pd.DataFrame(closes).sort_index()
    # 30d momentum (pct change)
    mom = close_grid.pct_change(MOMENTUM_LOOKBACK)

    # Align F&G to the crypto trading dates (forward-fill)
    fg_idx = fg.set_index("date")["value"]
    fg_aligned = fg_idx.reindex(close_grid.index).ffill()

    signals = []
    # Track open positions: ticker -> dict(entry_idx, entry_price, stop, target, entry_date)
    open_pos = {}
    dates = close_grid.index
    n = len(dates)

    for i in range(n):
        date = dates[i]
        fg_val = fg_aligned.iloc[i] if i < len(fg_aligned) else np.nan

        # ── Manage open positions first (exits checked at today's close) ──
        for ticker in list(open_pos.keys()):
            pos = open_pos[ticker]
            # exit_idx is index of this date in THIS ticker's own series
            tdf = data_dict.get(ticker)
            if tdf is None:
                del open_pos[ticker]
                continue
            tclose = tdf["close"] if "close" in tdf.columns else tdf.iloc[:, 0]
            # map date -> position in ticker series
            if date not in tclose.index:
                continue
            j = tclose.index.get_loc(date)
            price = float(tclose.iloc[j])
            entry_price = pos["entry_price"]
            stop = pos["stop_price"]
            target = pos["target_price"]
            bars_held = j - pos["entry_idx"]

            exit_reason = None
            exit_price = price
            if not np.isnan(fg_val) and fg_val >= FG_EXIT:
                exit_reason = "fg_exit"
            elif price <= stop:
                exit_reason = "stop"
            elif price >= target:
                exit_reason = "target"
            elif bars_held >= MAX_BARS_HELD:
                exit_reason = "time"

            if exit_reason is not None:
                risk = entry_price - stop
                realised_r = (price - entry_price) / risk if risk > 0 else 0.0
                signals.append({
                    "ticker": ticker,
                    "date": pos["entry_date"],
                    "direction": "long",
                    "entry_price": round(float(entry_price), 6),
                    "stop_price": round(float(stop), 6),
                    "target_price": round(float(target), 6),
                    "exit_price": round(float(price), 6),
                    "exit_reason": exit_reason,
                    "r_multiple": round(float(realised_r), 4),
                    "bars_held": int(bars_held),
                    "subperiod": _subperiod(pos["entry_date"]),
                    "strategy_id": STRATEGY_ID,
                })
                del open_pos[ticker]

        # ── Entries: only when F&G < FG_ENTRY ──────────────────────────────
        if np.isnan(fg_val) or fg_val >= FG_ENTRY:
            continue

        row = mom.iloc[i]
        # Rank by 30d momentum, exclude names already held or with NaN momentum
        ranked = []
        for ticker in close_grid.columns:
            if ticker in open_pos:
                continue
            m = row.get(ticker, np.nan)
            if pd.isna(m):
                continue
            ranked.append((ticker, float(m)))
        ranked.sort(key=lambda x: x[1], reverse=True)

        for ticker, _m in ranked[:TOP_N]:
            tdf = data_dict.get(ticker)
            if tdf is None:
                continue
            tclose = tdf["close"] if "close" in tdf.columns else tdf.iloc[:, 0]
            if date not in tclose.index:
                continue
            j = tclose.index.get_loc(date)
            entry_price = float(tclose.iloc[j])
            stop = entry_price * (1 - STOP_PCT)
            risk = entry_price - stop
            if risk <= 0:
                continue
            target = entry_price + MIN_RR * risk
            open_pos[ticker] = {
                "entry_idx": j,
                "entry_price": entry_price,
                "stop_price": stop,
                "target_price": target,
                "entry_date": date,
            }

    # ── Force-close any still-open positions at the last available close ───
    for ticker, pos in list(open_pos.items()):
        tdf = data_dict.get(ticker)
        if tdf is None:
            continue
        tclose = tdf["close"] if "close" in tdf.columns else tdf.iloc[:, 0]
        if len(tclose) == 0:
            continue
        j = len(tclose) - 1
        price = float(tclose.iloc[j])
        risk = pos["entry_price"] - pos["stop_price"]
        realised_r = (price - pos["entry_price"]) / risk if risk > 0 else 0.0
        signals.append({
            "ticker": ticker,
            "date": pos["entry_date"],
            "direction": "long",
            "entry_price": round(float(pos["entry_price"]), 6),
            "stop_price": round(float(pos["stop_price"]), 6),
            "target_price": round(float(pos["target_price"]), 6),
            "exit_price": round(float(price), 6),
            "exit_reason": "end_of_data",
            "r_multiple": round(float(realised_r), 4),
            "bars_held": int(j - pos["entry_idx"]),
            "subperiod": _subperiod(pos["entry_date"]),
            "strategy_id": STRATEGY_ID,
        })

    return signals


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(Path.home() / "HermesForge" / "scripts" / "paper_trading"))
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
        print(pd.DataFrame(sigs)["r_multiple"].describe())
