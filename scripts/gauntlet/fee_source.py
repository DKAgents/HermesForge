#!/usr/bin/env python3
"""
fee_source.py — dynamic venue-cost source (US-165).

Single owner of venue fee magnitudes. Fetches the Hyperliquid base-tier fee
schedule (the MOST expensive tier = the correct fail-closed anchor) from the
live info endpoint, caches with a 6-hour TTL, and falls back to a conservative
static constant on any failure. Both the gauntlet G3 path
(cost_adjuster.compute_cost_drag) and the hostile/live PnL path (pnl_accounting
call sites in hostile_fills*.py) derive their bps from here — exactly one fee
table exists.

Pure HTTP + cache + math: zero coupling to trade_log / trade_journal /
detect_liquidity_sweeps, so it stays unit-testable without the pipeline.
"""

import json
import math
import time
import urllib.request
import urllib.error

HYPERLIQUID_INFO_URL = "https://api.hyperliquid.xyz/info"
BASE_ADDRESS = "0x0000000000000000000000000000000000000000"
FEE_CACHE_TTL_SECONDS = 6 * 3600        # 6 hours — schedule changes are rare

# Fail-closed fallback = the base-tier schedule values (MOST expensive tier).
# Same cost as the prior assumption, so a fetch failure can never make fees
# look cheaper. crypto all-in round-trip = 2*4.5 taker + 2.5 slip + 0.5 funding.
FAIL_CLOSED_FALLBACK = {
    "crypto": {"taker_bps": 4.5, "maker_bps": 1.5,
               "slippage_bps": 2.5, "funding_bps": 0.5},
    "stock":  {"taker_bps": 1.0, "maker_bps": 0.0,
               "slippage_bps": 1.0, "funding_bps": 0.0},
}

_cache_state = {"ts": 0.0, "fees": None}


def _parse_base_fees(data: dict) -> dict | None:
    """Parse ONLY the schedule base tier (feeSchedule.cross/.add).

    Deliberately ignores userCrossRate/userAddRate (the queried account's
    personal, possibly discounted rate) — reading them would let a favorable
    tier leak into the base assumption. The schedule's top-level cross/add IS
    the base tier and the most expensive tier, so it is the fail-closed anchor.
    """
    fs = data.get("feeSchedule")
    if not isinstance(fs, dict):
        return None
    try:
        taker = round(float(fs["cross"]) * 10000, 6)   # 0.00045 -> 4.5
        maker = round(float(fs["add"]) * 10000, 6)     # 0.00015 -> 1.5
    except (KeyError, TypeError, ValueError):
        return None
    if not (maker >= 0 and taker > 0 and math.isfinite(taker) and math.isfinite(maker)):
        return None
    return {"taker_bps": taker, "maker_bps": maker}


def fetch_hyperliquid_base_fees(timeout: float = 10.0) -> dict | None:
    """POST the info endpoint; on ANY exception / HTTP!=200 / non-JSON -> None
    (never raise)."""
    payload = json.dumps({"type": "userFees", "user": BASE_ADDRESS}).encode()
    req = urllib.request.Request(
        HYPERLIQUID_INFO_URL, data=payload,
        headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            if resp.status != 200:
                return None
            raw = resp.read()
    except Exception:
        return None
    try:
        data = json.loads(raw)
    except (ValueError, TypeError):
        return None
    return _parse_base_fees(data)


def get_venue_costs() -> dict:
    """Return {'crypto': {...}, 'stock': {...}}.

    Cached for FEE_CACHE_TTL_SECONDS. On fetch failure returns FAIL_CLOSED_FALLBACK
    (never caches the fallback as live). Live crypto taker/maker are clamped UP
    to the fallback floor so a (hypothetically cheaper) schedule can never make
    fees look more favorable than the base tier.
    """
    now = time.time()
    if (_cache_state["fees"] is not None
            and now - _cache_state["ts"] < FEE_CACHE_TTL_SECONDS):
        return _cache_state["fees"]

    base = fetch_hyperliquid_base_fees()
    if base is None:
        # Do NOT update _cache_state — the fallback is never cached as live.
        return FAIL_CLOSED_FALLBACK

    crypto_floor = FAIL_CLOSED_FALLBACK["crypto"]
    crypto = {
        "taker_bps": max(base["taker_bps"], crypto_floor["taker_bps"]),
        "maker_bps": max(base["maker_bps"], crypto_floor["maker_bps"]),
        "slippage_bps": crypto_floor["slippage_bps"],
        "funding_bps": crypto_floor["funding_bps"],
    }
    # Stock commission is a broker assumption (IBKR Pro tiered), not a
    # Hyperliquid value — always static.
    costs = {"crypto": crypto, "stock": dict(FAIL_CLOSED_FALLBACK["stock"])}
    _cache_state["fees"] = costs
    _cache_state["ts"] = now
    return costs


def _costs_for(asset_class: str) -> dict:
    costs = get_venue_costs()
    if asset_class == "stock":
        return costs["stock"]
    return costs["crypto"]   # crypto is the conservative default for unknown


def get_taker_bps(asset_class: str) -> float:
    """Per-side taker fee in bps."""
    return _costs_for(asset_class)["taker_bps"]


def get_maker_bps(asset_class: str) -> float:
    """Per-side maker fee in bps."""
    return _costs_for(asset_class)["maker_bps"]


def get_round_trip_bps(asset_class: str) -> float:
    """All-in round-trip bps = taker*2 + slippage + funding."""
    c = _costs_for(asset_class)
    return c["taker_bps"] * 2 + c["slippage_bps"] + c["funding_bps"]