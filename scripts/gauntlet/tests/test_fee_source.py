"""
Tests for fee_source.py — the dynamic venue-cost source (US-165 + C-6).

Covers: fail-closed fallback (fetch failure -> FAIL_CLOSED_FALLBACK),
clamp-so-a-cheaper-live-schedule-never-drops-below-base, TTL caching,
_parse_base_fees perp parsing, _parse_spot_fees spot parsing, the stock
non-zero-commission change, the C-6 spot asset class (4.0/7.0 bps), the
HIP-3 2x multiplier (perp only), and carry_round_trip_fee_bps.
"""

import sys
import os
import time
import urllib.error

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import fee_source
from fee_source import (
    FAIL_CLOSED_FALLBACK,
    HIP3_FEE_MULTIPLIER,
    _parse_base_fees,
    _parse_spot_fees,
    fetch_hyperliquid_base_fees,
    fetch_hyperliquid_schedule,
    get_venue_costs,
    get_taker_bps,
    get_maker_bps,
    get_round_trip_bps,
    carry_round_trip_fee_bps,
)


def _reset_cache():
    fee_source._cache_state["ts"] = 0.0
    fee_source._cache_state["fees"] = None


# A live schedule with the verified base-tier values: perp cross/add 0.00045 /
# 0.00015, spot spotCross/spotAdd 0.0007 / 0.0004 (2026-11-09 userFees).
_LIVE_SCHED = {
    "perp": {"taker_bps": 4.5, "maker_bps": 1.5},
    "spot": {"taker_bps": 7.0, "maker_bps": 4.0},
}


def test_parse_base_fees_parses_schedule_base_tier():
    data = {"feeSchedule": {"cross": "0.00045", "add": "0.00015"}}
    out = _parse_base_fees(data)
    assert out == {"taker_bps": 4.5, "maker_bps": 1.5}


def test_parse_spot_fees_parses_spot_base_tier():
    data = {"feeSchedule": {"spotCross": "0.0007", "spotAdd": "0.0004"}}
    out = _parse_spot_fees(data)
    assert out == {"taker_bps": 7.0, "maker_bps": 4.0}


def test_parse_spot_fees_bad_input_returns_none():
    assert _parse_spot_fees({}) is None
    assert _parse_spot_fees({"feeSchedule": {"spotCross": "x", "spotAdd": "0.0004"}}) is None
    assert _parse_spot_fees({"feeSchedule": {"spotCross": "0.0", "spotAdd": "0.0004"}}) is None


def test_parse_base_fees_ignores_user_rate():
    # A (potentially discounted) per-account rate must NOT leak into the base.
    data = {
        "feeSchedule": {"cross": "0.00045", "add": "0.00015"},
        "userCrossRate": "0.00020", "userAddRate": "0.00010",
    }
    out = _parse_base_fees(data)
    assert out == {"taker_bps": 4.5, "maker_bps": 1.5}


def test_parse_base_fees_bad_input_returns_none():
    assert _parse_base_fees({}) is None
    assert _parse_base_fees({"feeSchedule": "not-a-dict"}) is None
    assert _parse_base_fees({"feeSchedule": {"cross": "x", "add": "0.00015"}}) is None
    assert _parse_base_fees({"feeSchedule": {"cross": "0.0", "add": "0.00015"}}) is None  # taker<=0


def test_fetch_returns_none_on_network_error():
    # The REAL fetch swallows any urllib exception and returns None (never raises).
    orig = fee_source.urllib.request.urlopen
    def _boom(*a, **k):
        raise urllib.error.URLError("unreachable")
    fee_source.urllib.request.urlopen = _boom
    try:
        assert fetch_hyperliquid_base_fees(timeout=1.0) is None
        assert fetch_hyperliquid_schedule(timeout=1.0) is None
    finally:
        fee_source.urllib.request.urlopen = orig


def test_fail_closed_on_fetch_none():
    _reset_cache()
    orig = fee_source.fetch_hyperliquid_schedule
    fee_source.fetch_hyperliquid_schedule = lambda *a, **k: None
    try:
        assert get_venue_costs() == FAIL_CLOSED_FALLBACK
    finally:
        fee_source.fetch_hyperliquid_schedule = orig


def test_cheaper_live_schedule_does_not_drop_below_base():
    _reset_cache()
    orig = fee_source.fetch_hyperliquid_schedule
    # Hypothetically "cheaper" schedule — must be clamped UP to the base tier.
    fee_source.fetch_hyperliquid_schedule = lambda *a, **k: {
        "perp": {"taker_bps": 2.0, "maker_bps": 0.5},
        "spot": {"taker_bps": 3.0, "maker_bps": 1.0},
    }
    try:
        costs = get_venue_costs()
    finally:
        fee_source.fetch_hyperliquid_schedule = orig
    assert costs["crypto"]["taker_bps"] == 4.5   # not 2.0
    assert costs["crypto"]["maker_bps"] == 1.5   # not 0.5
    assert costs["spot"]["taker_bps"] == 7.0     # not 3.0
    assert costs["spot"]["maker_bps"] == 4.0     # not 1.0


def test_ttl_caching_avoids_network():
    _reset_cache()
    calls = {"n": 0}
    orig = fee_source.fetch_hyperliquid_schedule

    def _counting(*a, **k):
        calls["n"] += 1
        return dict(_LIVE_SCHED)

    fee_source.fetch_hyperliquid_schedule = _counting
    try:
        first = get_venue_costs()
        second = get_venue_costs()   # within TTL -> must not hit network again
    finally:
        fee_source.fetch_hyperliquid_schedule = orig
    assert first == second
    assert calls["n"] == 1


def _with_live_schedule(fn):
    _reset_cache()
    orig = fee_source.fetch_hyperliquid_schedule
    fee_source.fetch_hyperliquid_schedule = lambda *a, **k: dict(_LIVE_SCHED)
    try:
        return fn()
    finally:
        fee_source.fetch_hyperliquid_schedule = orig


def test_fallback_numbers():
    _reset_cache()
    # crypto all-in round trip = 2*4.5 + 2.5 + 0.5 = 12.0
    assert get_round_trip_bps("crypto") == 12.0
    assert get_taker_bps("crypto") == 4.5
    assert get_maker_bps("crypto") == 1.5
    # stock: non-zero commission -> 2*1.0 + 1.0 + 0.0 = 3.0 (NOT the old 2.0)
    assert get_round_trip_bps("stock") == 3.0
    assert get_taker_bps("stock") == 1.0
    assert get_maker_bps("stock") == 0.0
    # spot (C-6): 2*7.0 + 2.5 + 0.0 = 16.5, maker 4.0, taker 7.0
    assert get_round_trip_bps("spot") == 16.5
    assert get_taker_bps("spot") == 7.0
    assert get_maker_bps("spot") == 4.0


def test_spot_is_distinct_from_perp():
    # The C-6 correction: the spot hedge leg must NOT reuse the perp maker/taker.
    assert get_maker_bps("spot") == 4.0
    assert get_maker_bps("crypto") == 1.5
    assert get_maker_bps("spot") != get_maker_bps("crypto")
    assert get_taker_bps("spot") == 7.0
    assert get_taker_bps("crypto") == 4.5


def test_hip3_doubles_perp_only():
    assert get_maker_bps("crypto", hip3=True) == 1.5 * HIP3_FEE_MULTIPLIER  # 3.0
    assert get_taker_bps("crypto", hip3=True) == 4.5 * HIP3_FEE_MULTIPLIER  # 9.0
    # Spot is NOT HIP-3: the multiplier must not touch the spot leg.
    assert get_maker_bps("spot", hip3=True) == 4.0
    assert get_taker_bps("spot", hip3=True) == 7.0
    assert get_maker_bps("stock", hip3=True) == 0.0


def test_carry_round_trip_fee_bps():
    # maker: 2*(perp 1.5 + spot 4.0) = 11.0  (was 6.0 buggy)
    assert carry_round_trip_fee_bps("maker") == 11.0
    # taker: 2*(perp 4.5 + spot 7.0) = 23.0  (was 18.0 buggy)
    assert carry_round_trip_fee_bps("taker") == 23.0
    # hip3 doubles the perp leg only: maker 2*(3.0 + 4.0) = 14.0
    assert carry_round_trip_fee_bps("maker", hip3=True) == 14.0


def test_carry_round_trip_fee_bps_rejects_unknown():
    try:
        carry_round_trip_fee_bps("bogus")
    except ValueError:
        return
    raise AssertionError("expected ValueError for unknown execution type")


def test_unknown_asset_class_defaults_to_crypto():
    _reset_cache()
    assert get_round_trip_bps("") == 12.0
    assert get_taker_bps("") == 4.5


def test_option_asset_class_us181_f4():
    # Deribit options (US-181 F4): taker 3bps, slip 1bp, no rebate, no funding.
    out = _with_live_schedule(lambda: get_venue_costs()["option"])
    assert out == {"taker_bps": 3.0, "maker_bps": 0.0,
                   "slippage_bps": 1.0, "funding_bps": 0.0}
    # option round-trip = 2*3 + 1 + 0 = 7.0 (distinct from crypto 12.0 / stock 3.0)
    assert get_round_trip_bps("option") == 7.0
    assert get_taker_bps("option") == 3.0


if __name__ == "__main__":
    import inspect
    for name, fn in sorted(list(globals().items())):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"PASS {name}")
    print("all fee_source tests passed")