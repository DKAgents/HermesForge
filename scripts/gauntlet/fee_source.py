#!/usr/bin/env python3
"""
fee_source.py — dynamic venue-cost source (US-165). C-6: spot + HIP-3.

Single owner of venue fee magnitudes. Fetches the Hyperliquid base-tier fee
schedule (the MOST expensive tier = the correct fail-closed anchor) from the
live info endpoint, caches with a 6-hour TTL, and falls back to a conservative
static constant on any failure. Both the gauntlet G3 path
(cost_adjuster.compute_cost_drag) and the hostile/live PnL path (pnl_accounting
call sites in hostile_fills*.py) derive their bps from here — exactly one fee
table exists.

C-6 (base-tier schedule, VERIFIED against the live `userFees` endpoint
2026-11-09 — see the per-venue comments below for the on-chain values):
  * PERP  ("crypto" asset class)  — maker 0.015% / taker 0.045% (1.5 / 4.5 bps).
  * SPOT  ("spot" asset class)    — maker 0.040% / taker 0.070% (4.0 / 7.0 bps).
  * HIP-3 builder/index perps (the "xyz:" namespace) charge 2x the base PERP
    schedule (maker 0.03% / taker 0.09%); SPOT is unaffected.

The spot leg of the delta-neutral funding carry (short perp + long spot) MUST
charge the SPOT schedule, NOT the perp schedule — this is the single most
costly correction the critical review surfaced (the prior model charged the
spot hedge at 1.5 bps maker where it actually costs 4.0 bps maker).

Tier notes (no code required — documented for the fee-model record): spot
volume counts 2x toward HL's VIP tier progression, and staking/referral
discounts (0-40%) exist — but both are immaterial at the current account size
and are DELIBERATELY ignored so the base (most-expensive) tier remains the
fail-closed anchor.

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

# HIP-3 builder/index (index/marketcap perpetual) markets — the "xyz:" namespace
# — charge 2x the base perp fee schedule. SPOT (and non-HIP-3 perps) are
# unaffected. Applied by the hip3= keyword on the perp getters.
HIP3_FEE_MULTIPLIER = 2.0

# Fail-closed fallback = the base-tier schedule values (MOST expensive tier).
# Same cost as the prior assumption, so a fetch failure can never make fees
# look cheaper. crypto all-in round-trip = 2*4.5 taker + 2.5 slip + 0.5 funding.
# C-6: "spot" is Hyperliquid SPOT base tier — spotAdd 0.0004 (4.0 bps maker) /
# spotCross 0.0007 (7.0 bps taker), NO funding (spot is not a perp). "option"
# = Deribit options (US-181 F4): taker ~0.03% of underlying, ~1bp straddle
# bid-ask slip, NO maker rebate credited (fail-closed: taker) and NO funding.
# Static (not HL-fetched) exactly like "stock" — a venue assumption, not a
# schedule read.
FAIL_CLOSED_FALLBACK = {
    "crypto": {"taker_bps": 4.5, "maker_bps": 1.5,
               "slippage_bps": 2.5, "funding_bps": 0.5},
    "spot":   {"taker_bps": 7.0, "maker_bps": 4.0,
               "slippage_bps": 2.5, "funding_bps": 0.0},
    "stock":  {"taker_bps": 1.0, "maker_bps": 0.0,
               "slippage_bps": 1.0, "funding_bps": 0.0},
    "option": {"taker_bps": 3.0, "maker_bps": 0.0,
               "slippage_bps": 1.0, "funding_bps": 0.0},
}

_cache_state = {"ts": 0.0, "fees": None}


def _parse_base_fees(data: dict) -> dict | None:
    """Parse ONLY the perp schedule base tier (feeSchedule.cross/.add).

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


def _parse_spot_fees(data: dict) -> dict | None:
    """Parse ONLY the spot schedule base tier (feeSchedule.spotCross/.spotAdd).

    C-6: the spot tier is a DISTINCT, more-expensive schedule than the perp
    tier — spotAdd 0.0004 (4.0 bps maker) / spotCross 0.0007 (7.0 bps taker).
    Fails closed (returns None) if the schedule is absent or malformed.
    """
    fs = data.get("feeSchedule")
    if not isinstance(fs, dict):
        return None
    try:
        taker = round(float(fs["spotCross"]) * 10000, 6)   # 0.0007 -> 7.0
        maker = round(float(fs["spotAdd"]) * 10000, 6)     # 0.0004 -> 4.0
    except (KeyError, TypeError, ValueError):
        return None
    if not (maker >= 0 and taker > 0 and math.isfinite(taker) and math.isfinite(maker)):
        return None
    return {"taker_bps": taker, "maker_bps": maker}


def _fetch_info(timeout: float) -> dict | None:
    """POST the info endpoint; return parsed JSON dict, or None (never raise)."""
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
    return data


def fetch_hyperliquid_schedule(timeout: float = 10.0) -> dict | None:
    """Return {"perp": {...}, "spot": {...}} base-tier fees, or None.

    ONE POST for both schedules. Returns None unless BOTH perp and spot parse
    (fail-closed: a missing spot schedule must not silently fall back to the
    perp rate for the hedge leg).
    """
    data = _fetch_info(timeout)
    if data is None:
        return None
    perp = _parse_base_fees(data)
    spot = _parse_spot_fees(data)
    if perp is None or spot is None:
        return None
    return {"perp": perp, "spot": spot}


def fetch_hyperliquid_base_fees(timeout: float = 10.0) -> dict | None:
    """Backward-compatible: return ONLY the perp base tier {taker_bps, maker_bps}.

    (No caller outside the tests uses this directly; it is kept so the perp-only
    fetch remains a named, stable entry point.)
    """
    sched = fetch_hyperliquid_schedule(timeout)
    return sched["perp"] if sched else None


def get_venue_costs() -> dict:
    """Return {'crypto', 'spot', 'stock', 'option'}.

    Cached for FEE_CACHE_TTL_SECONDS. On fetch failure returns FAIL_CLOSED_FALLBACK
    (never caches the fallback as live). Live crypto/spot taker/maker are clamped
    UP to the fallback floor so a (hypothetically cheaper) schedule can never make
    fees look more favorable than the base tier.
    """
    now = time.time()
    if (_cache_state["fees"] is not None
            and now - _cache_state["ts"] < FEE_CACHE_TTL_SECONDS):
        return _cache_state["fees"]

    sched = fetch_hyperliquid_schedule()
    if sched is None:
        # Do NOT update _cache_state — the fallback is never cached as live.
        return FAIL_CLOSED_FALLBACK

    crypto_floor = FAIL_CLOSED_FALLBACK["crypto"]
    spot_floor = FAIL_CLOSED_FALLBACK["spot"]
    crypto = {
        "taker_bps": max(sched["perp"]["taker_bps"], crypto_floor["taker_bps"]),
        "maker_bps": max(sched["perp"]["maker_bps"], crypto_floor["maker_bps"]),
        "slippage_bps": crypto_floor["slippage_bps"],
        "funding_bps": crypto_floor["funding_bps"],
    }
    spot = {
        "taker_bps": max(sched["spot"]["taker_bps"], spot_floor["taker_bps"]),
        "maker_bps": max(sched["spot"]["maker_bps"], spot_floor["maker_bps"]),
        "slippage_bps": spot_floor["slippage_bps"],
        "funding_bps": spot_floor["funding_bps"],
    }
    # Stock commission is a broker assumption (IBKR Pro tiered), not a
    # Hyperliquid value — always static. "option" (Deribit) is likewise a
    # static venue assumption, never HL-fetched (US-181 F4).
    costs = {"crypto": crypto, "spot": spot,
             "stock": dict(FAIL_CLOSED_FALLBACK["stock"]),
             "option": dict(FAIL_CLOSED_FALLBACK["option"])}
    _cache_state["fees"] = costs
    _cache_state["ts"] = now
    return costs


def _costs_for(asset_class: str) -> dict:
    costs = get_venue_costs()
    if asset_class == "option":
        return costs["option"]
    if asset_class == "stock":
        return costs["stock"]
    if asset_class == "spot":
        return costs["spot"]
    return costs["crypto"]   # crypto (perp) is the conservative default


def get_taker_bps(asset_class: str, hip3: bool = False) -> float:
    """Per-side taker fee in bps. hip3=True applies HIP3_FEE_MULTIPLIER to the
    perp (crypto) schedule only (spot/stock/option are never HIP-3)."""
    bps = _costs_for(asset_class)["taker_bps"]
    if hip3 and asset_class in ("crypto",):
        return bps * HIP3_FEE_MULTIPLIER
    return bps


def get_maker_bps(asset_class: str, hip3: bool = False) -> float:
    """Per-side maker fee in bps. hip3=True applies HIP3_FEE_MULTIPLIER to the
    perp (crypto) schedule only (spot/stock/option are never HIP-3)."""
    bps = _costs_for(asset_class)["maker_bps"]
    if hip3 and asset_class in ("crypto",):
        return bps * HIP3_FEE_MULTIPLIER
    return bps


def get_round_trip_bps(asset_class: str) -> float:
    """All-in round-trip bps = taker*2 + slippage + funding."""
    c = _costs_for(asset_class)
    return c["taker_bps"] * 2 + c["slippage_bps"] + c["funding_bps"]


def carry_round_trip_fee_bps(execution_type: str, hip3: bool = False) -> float:
    """Delta-neutral funding-carry round-trip FEE (entry + exit, both legs).

    Leg 1 = short PERP (perp schedule), leg 2 = long SPOT (spot schedule):
        round_trip = 2 * (perp_fee + spot_fee).

    C-6 correction: the spot hedge leg charges the SPOT base tier (maker 4.0 /
    taker 7.0 bps), NOT the perp tier (maker 1.5 / taker 4.5). Result:
        maker -> 2*(1.5 + 4.0) = 11.0 bps   (was 6.0 under the buggy model)
        taker -> 2*(4.5 + 7.0) = 23.0 bps   (was 18.0)

    `hip3=True` doubles the perp leg only (a HIP-3 index-perp carry would pay
    2x on the short perp side). FEE ONLY — no slippage/funding folded in; those
    are separate G3 / runtime concerns (HYP-29 spot-spread assumption).
    """
    if execution_type == "maker":
        perp = get_maker_bps("crypto", hip3=hip3)
        spot = get_maker_bps("spot")
    elif execution_type == "taker":
        perp = get_taker_bps("crypto", hip3=hip3)
        spot = get_taker_bps("spot")
    else:
        raise ValueError(f"unknown execution_type={execution_type!r}")
    return 2.0 * (perp + spot)