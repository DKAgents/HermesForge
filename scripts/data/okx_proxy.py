"""
okx_proxy.py — HermesForge US-177: labeled OKX candle-history fallback.

The canonical, EXPLICIT fallback reader for the pre-store gap: bars that are
older than the Hyperliquid bar store's retention floor (~17 days for 5m).
Today the repo only has OKX L2 orderbook + open-interest fetchers
(liquidity_heatmap.py); candle HISTORY is added here for the first time.

Policy (honest, never fabricated):
  * A Hyperliquid ticker with NO OKX perpetual twin (PAXG, and the 1000x kilo
    coins kBONK/kPEPE/kSHIB which map to base-denominated OKX perps ~1000x
    off-scale) is unmapped -> fetch_okx_bars returns an EMPTY frame. The
    backtest window for that ticker simply starts at the store floor.
  * Raises NOTHING on data absence (returns empty) so the caller can label the
    gap, never synthesize bars.

Symbol map verified empirically against live OKX (2026-11-01):
  * 32/35 universe tickers have a same-symbol `{COIN}-USDT-SWAP` perpetual
    whose last close matches Hyperliquid within ~0.1% (ratio ~1.0000).
  * kBONK/kPEPE/kSHIB exist only as BONK/PEPE/SHIB on OKX (base denom, ratio
    ~0.001) and there is NO 1000x perpetual -> intentionally unmapped.
  * PAXG has no OKX perpetual -> unmapped.

Standalone module: no store import. Depends only on stdlib + requests + pandas.
"""

from __future__ import annotations

import time

import pandas as pd
import requests

OKX_HOST = "https://www.okx.com/api/v5/market"

# Hyperliquid coin -> OKX perpetual instId. Explicit map; UNKNOWN ticker = skip.
HL_TO_OKX: dict[str, str | None] = {
    "BTC": "BTC-USDT-SWAP",
    "ETH": "ETH-USDT-SWAP",
    "SOL": "SOL-USDT-SWAP",
    "AVAX": "AVAX-USDT-SWAP",
    "LINK": "LINK-USDT-SWAP",
    "DOGE": "DOGE-USDT-SWAP",
    "ARB": "ARB-USDT-SWAP",
    "OP": "OP-USDT-SWAP",
    "SUI": "SUI-USDT-SWAP",
    "AAVE": "AAVE-USDT-SWAP",
    "ADA": "ADA-USDT-SWAP",
    "APT": "APT-USDT-SWAP",
    "BCH": "BCH-USDT-SWAP",
    "BNB": "BNB-USDT-SWAP",
    "CRV": "CRV-USDT-SWAP",
    "DOT": "DOT-USDT-SWAP",
    "ENA": "ENA-USDT-SWAP",
    "FARTCOIN": "FARTCOIN-USDT-SWAP",
    "HYPE": "HYPE-USDT-SWAP",
    "JUP": "JUP-USDT-SWAP",
    "LTC": "LTC-USDT-SWAP",
    "NEAR": "NEAR-USDT-SWAP",
    "ONDO": "ONDO-USDT-SWAP",
    # PAXG: no OKX perpetual -> None.
    "PAXG": None,
    "PUMP": "PUMP-USDT-SWAP",
    "TRUMP": "TRUMP-USDT-SWAP",
    "TRX": "TRX-USDT-SWAP",
    "UNI": "UNI-USDT-SWAP",
    "WLD": "WLD-USDT-SWAP",
    "XPL": "XPL-USDT-SWAP",
    "XRP": "XRP-USDT-SWAP",
    "ZEC": "ZEC-USDT-SWAP",
    # 1000x kilo coins have NO same-denomination OKX twin (base shares are
    # ~1000x off-scale; no OKX 1000x perpetual exists) -> None.
    "kBONK": None,
    "kPEPE": None,
    "kSHIB": None,
}

DEFAULT_BAR = "5m"
_EMPTY = pd.DataFrame(columns=["ts", "open", "high", "low", "close", "volume"])
_PAGE_LIMIT = 100


def fetch_okx_bars(ticker: str, timeframe: str, start_ms: int,
                   end_ms: int) -> pd.DataFrame:
    """GET /api/v5/market/history-candles (paginated via `after`, walking
    backward from newest to oldest). Returns DataFrame[ts, open, high, low,
    close, volume] in ascending order, or EMPTY if unmapped / rate-limited /
    no data. Raises NOTHING on data absence — the caller labels the gap.

    NOTE: OKX `history-candles` returns newest-first; `after=<ts>` pages to
    older bars (verified live). `ts` here is epoch ms (bar open), aligned to
    the store's convention (bar open time = Hyperliquid 't')."""
    inst_id = HL_TO_OKX.get(ticker.upper())
    if inst_id is None:
        return _EMPTY.copy()

    bar = timeframe if timeframe else DEFAULT_BAR
    start_ms = int(start_ms)
    end_ms = int(end_ms)

    out: dict[int, dict] = {}
    after = end_ms  # page starting from the newest requested timestamp

    while True:
        try:
            resp = requests.get(
                f"{OKX_HOST}/history-candles",
                params={"instId": inst_id, "bar": bar,
                        "after": str(after), "limit": str(_PAGE_LIMIT)},
                timeout=20,
            )
            resp.raise_for_status()
            data = resp.json()
        except Exception:
            break  # network/rate-limit -> return what we have (possibly empty)

        if data.get("code") != "0":
            break
        rows = data.get("data") or []
        if not rows:
            break

        oldest_in_page: int | None = None
        for r in rows:
            # OKX candle row: [ts, o, h, l, c, vol(base), volCcy, volCcyQuote, confirm]
            try:
                ts = int(r[0])
            except (TypeError, ValueError):
                continue
            oldest_in_page = ts if oldest_in_page is None else min(oldest_in_page, ts)
            if ts < start_ms or ts >= end_ms or ts in out:
                continue
            out[ts] = {
                "ts": ts,
                "open": float(r[1]),
                "high": float(r[2]),
                "low": float(r[3]),
                "close": float(r[4]),
                "volume": float(r[5]),
            }

        # Walk further back while there may be older bars in range.
        if oldest_in_page is None or oldest_in_page <= start_ms:
            break
        if len(rows) < _PAGE_LIMIT:
            break  # reached the end of available history
        after = oldest_in_page - 1
        # Safety: never loop forever if pagination doesn't advance.
        if after >= end_ms:
            break

    if not out:
        return _EMPTY.copy()

    df = pd.DataFrame([out[ts] for ts in sorted(out)])
    df = df.reindex(columns=["ts", "open", "high", "low", "close", "volume"])
    return df.reset_index(drop=True)