"""universe_filter.py — US-203 (EPIC-017 Phase 2) Hypherliquid-only intake router.

Only instruments tradeable on Hyperliquid (perps / spot) are allowed to run the
Gauntlet. Equities, FX, gold, and single-stock signals are PARKED in a separate
backlog instead of being run through the Gauntlet.

Ground truth for "tradeable" is Hyperliquid's OWN universe (perps + spot coin
names), because that is the venue the Gauntlet executes against (ADR-011:
venue = Hyperliquid). An equity/FX/gold/single-stock ticker is simply NOT in
that universe, so it can never be HL-tradeable regardless of any local naming
heuristic.

Design (fail-closed):
  * ``route_intake(entry)`` classifies a seed's ``instruments`` into
    ``gauntlet`` (every instrument HL-tradeable) or ``parked`` (>=1 instrument
    not HL-tradeable, with the offending instruments + detected asset class as
    the human-readable reason).
  * Instrument strings may be literal tickers (``"BTC"``, ``"NVDA"``) or
    universe selectors (``"universe:hl-perps"``, ``"universe:liq-filtered"``);
    a ``universe:`` selector is crypto-by-construction -> eligible.
  * ``load_hl_universe()`` fetches the live HL perps + spot name set (cached
    with a TTL). On ANY fetch failure it falls back to the curated
    ``hermes_config.universe.CRYPTO_UNIVERSE`` (the active HL perp universe) so
    the router never *mislabels a non-HL ticker as tradeable* — the fallback is
    the smaller, safe set.
  * ``park_seed(entry)`` appends the seed to the parked backlog
    (``data/gauntlet/parked_seeds.jsonl``) with the park reason + timestamp.

Sample: an equity seed ``["NVDA"]`` routes to ``parked``; ``["BTC", "ETH"]``
routes to ``gauntlet``.
"""

from __future__ import annotations

import json
import os
import time
from typing import Any, Dict, List, Optional, Tuple

try:
    import requests
except ImportError:  # pragma: no cover - isolation
    requests = None

PARKED_FILE = os.path.abspath(os.path.join(
    os.path.dirname(__file__), "..", "..", "data", "gauntlet", "parked_seeds.jsonl"
))

HYPERLIQUID_INFO_URL = "https://api.hyperliquid.xyz/info"
_HL_UNIVERSE_CACHE = {"ts": 0.0, "universe": None}
_CACHE_TTL_SECONDS = 6 * 3600  # 6 hours — listings change slowly

# Asset-class labels used only for the PARKED reason string (provenance). The
# gate itself is HL-universe membership, not these labels.
ASSET_CLASS_FX = "fx"
ASSET_CLASS_COMMODITY = "commodity"
ASSET_CLASS_INDEX = "index"
ASSET_CLASS_EQUITY = "equity"

# ISO currency codes for FX-pair detection (6-letter XXXYYY where both halves
# are fiat currencies). Crypto quote pairs like BTCUSD/ETHUSD are NOT FX —
# BTC/ETH are not in this set.
_FX_CURRENCIES = {
    "USD", "EUR", "GBP", "JPY", "AUD", "NZD", "CAD", "CHF", "CNY", "SEK",
    "NOK", "MXN", "SGD", "HKD", "TRY", "ZAR", "INR", "KRW", "BRL", "PLN",
}

_COMMODITY_TICKERS = {
    "XAU", "XAG", "XAUUSD", "XAGUSD", "GOLD", "SILVER", "PLATINUM",
    "XPT", "XPD", "WTI", "OIL", "CL", "BRENT", "NG", "COPPER", "HG",
}

_INDEX_ETFS = {
    "SPY", "QQQ", "DIA", "IWM", "VTI", "VOO", "SPX", "NDX", "IXIC", "DJI",
    "XLK", "XLF", "XLE", "XLU", "XLY", "XLI", "XLB", "XLV", "XLP", "XBI",
    "GLD", "SLV", "USO", "UNG",
}

# Curated single-stock equity names (provenance only — the gate does NOT require
# a complete list; any non-HL ticker parks via universe membership).
_EQUITY_TICKERS = {
    "NVDA", "AAPL", "TSLA", "MSFT", "AMZN", "META", "GOOGL", "GOOG", "NFLX",
    "JPM", "XOM", "V", "MA", "UNH", "HD", "COST", "AVGO", "LLY", "ORCL",
    "CRM", "AMD", "INTC", "QCOM", "TXN", "ADBE", "BA", "CAT", "GE", "WMT",
    "PG", "JNJ", "MRK", "KO", "PEP", "DIS", "IBM", "CSCO", "BAC", "C",
    "GS", "MS", "WFC", "PLTR", "MU", "SHOP", "UBER", "LYFT", "ABNB",
}


def normalize_ticker(ticker: str) -> str:
    """Upper-case and strip separators (``EUR/USD`` -> ``EURUSD``)."""
    return (ticker or "").strip().upper().replace("/", "").replace("-", "") \
        .replace("_", "").replace(" ", "")


def _is_fx_pair(t: str) -> bool:
    return (len(t) == 6 and t[:3] in _FX_CURRENCIES and t[3:] in _FX_CURRENCIES)


def detect_non_hl_class(ticker: str) -> Optional[str]:
    """Best-effort asset class for a non-HL ticker, for the PARK reason string.

    Returns one of ``fx`` / ``commodity`` / ``index`` / ``equity`` / ``None``.
    ``None`` means "no static class matched" (the caller falls back to
    'not-in-hyperliquid-universe', which is still a parked path).
    """
    t = normalize_ticker(ticker)
    if not t:
        return None
    if _is_fx_pair(t):
        return ASSET_CLASS_FX
    if t in _COMMODITY_TICKERS:
        return ASSET_CLASS_COMMODITY
    if t in _INDEX_ETFS:
        return ASSET_CLASS_INDEX
    if t in _EQUITY_TICKERS:
        return ASSET_CLASS_EQUITY
    return None


def _curated_universe() -> frozenset:
    """Fallback HL perp universe from the single source of truth."""
    try:
        from hermes_config.universe import CRYPTO_UNIVERSE
        return frozenset(normalize_ticker(c) for c in CRYPTO_UNIVERSE)
    except ImportError:  # pragma: no cover
        return frozenset()


def _fetch_hl_universe() -> Optional[frozenset]:
    """Fetch the live HL perp + spot coin name set. Returns None on failure."""
    if requests is None:
        return None
    names: set = set()
    try:
        # Perpetuals: meta.universe[].name
        resp = requests.post(HYPERLIQUID_INFO_URL, json={"type": "meta"},
                             timeout=15)
        resp.raise_for_status()
        data = resp.json()
        for u in data.get("universe", []) or []:
            n = u.get("name")
            if n:
                names.add(normalize_ticker(n))
        # Spot: data has a "universe" of spot assets too (spotMeta separate
        # endpoint); best-effort add via metaAndAssetCtxs is out of scope here.
        return frozenset(names)
    except Exception:
        return None


def load_hl_universe() -> frozenset:
    """Return the HL-tradeable universe (live fetch, cached; curated fallback).

    Fail-closed: on fetch failure the fallback is the *curated active perp set*
    (smaller, safe). It can never make a non-HL ticker look tradeable.
    """
    now = time.time()
    if _HL_UNIVERSE_CACHE["universe"] is not None \
            and now - _HL_UNIVERSE_CACHE["ts"] < _CACHE_TTL_SECONDS:
        return _HL_UNIVERSE_CACHE["universe"]
    live = _fetch_hl_universe()
    if live is not None and live:
        _HL_UNIVERSE_CACHE["universe"] = live
        _HL_UNIVERSE_CACHE["ts"] = now
        return live
    # Fallback (also cached) — do NOT cache the live miss as authoritative.
    return _curated_universe()


def is_hl_tradeable(ticker: str, universe: Optional[frozenset] = None) -> bool:
    """True if ``ticker`` is in the HL-tradeable universe (case/sep-normalized)."""
    if universe is None:
        universe = load_hl_universe()
    t = normalize_ticker(ticker)
    if not t:
        return False
    return t in universe


def route_intake(entry: Dict[str, Any],
                 universe: Optional[frozenset] = None) -> Dict[str, Any]:
    """Classify a seed's instruments: ``gauntlet`` or ``parked``.

    ``universe:`` selector strings are crypto-by-construction -> eligible.
    Every literal instrument must be HL-tradeable; otherwise the seed is parked
    and the reason names each offending instrument + its detected class.
    """
    instruments = entry.get("instruments", []) or []
    non_hl: List[Dict[str, str]] = []
    for inst in instruments:
        if isinstance(inst, str) and inst.lower().startswith("universe:"):
            continue
        if not is_hl_tradeable(inst, universe=universe):
            cls = detect_non_hl_class(inst) or "not-in-hyperliquid-universe"
            non_hl.append({"instrument": str(inst), "asset_class": cls})

    if non_hl:
        offenders = ", ".join(
            f"{n['instrument']}({n['asset_class']})" for n in non_hl
        )
        return {
            "route": "parked",
            "reason": f"non-Hyperliquid instrument(s): {offenders}",
            "non_hl": non_hl,
        }
    return {
        "route": "gauntlet",
        "reason": "all instruments are Hyperliquid-tradeable",
        "non_hl": [],
    }


def park_seed(entry: Dict[str, Any], reason: str,
              at: Optional[str] = None) -> Dict[str, Any]:
    """Append a seed to the parked backlog (append-only JSONL). Returns the
    parked record (with ``parked_at`` + ``parked_reason``)."""
    os.makedirs(os.path.dirname(PARKED_FILE), exist_ok=True)
    if at is None:
        at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    record = {
        "hypothesis_id": entry.get("hypothesis_id"),
        "source": entry.get("source"),
        "instruments": entry.get("instruments"),
        "horizon": entry.get("horizon"),
        "entry_logic": entry.get("entry_logic"),
        "parked_reason": reason,
        "parked_at": at,
    }
    with open(PARKED_FILE, "a") as f:
        f.write(json.dumps(record) + "\n")
    return record


def list_parked() -> List[Dict[str, Any]]:
    """Return all parked seeds (read-only)."""
    if not os.path.exists(PARKED_FILE):
        return []
    out = []
    with open(PARKED_FILE, "r") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    out.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return out


if __name__ == "__main__":
    cases = [
        {"instruments": ["BTC", "ETH"]},
        {"instruments": ["NVDA"]},
        {"instruments": ["EURUSD"]},
        {"instruments": ["XAUUSD"]},
        {"instruments": ["universe:hl-perps"]},
        {"instruments": ["SOL", "AAPL"]},
    ]
    for c in cases:
        print(c["instruments"], "->", route_intake(c)["route"])