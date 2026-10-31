"""
Tests for fee_source.py — the dynamic venue-cost source (US-165).

Covers: fail-closed fallback (fetch failure -> FAIL_CLOSED_FALLBACK),
clamp-so-a-cheaper-live-schedule-never-drops-below-base, TTL caching,
_parse_base_fees base-tier parsing, and the stock non-zero-commission change.
"""

import sys
import os
import time
import urllib.error

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import fee_source
from fee_source import (
    FAIL_CLOSED_FALLBACK,
    _parse_base_fees,
    fetch_hyperliquid_base_fees,
    get_venue_costs,
    get_taker_bps,
    get_maker_bps,
    get_round_trip_bps,
)


def _reset_cache():
    fee_source._cache_state["ts"] = 0.0
    fee_source._cache_state["fees"] = None


def test_parse_base_fees_parses_schedule_base_tier():
    data = {"feeSchedule": {"cross": "0.00045", "add": "0.00015"}}
    out = _parse_base_fees(data)
    assert out == {"taker_bps": 4.5, "maker_bps": 1.5}


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
    finally:
        fee_source.urllib.request.urlopen = orig


def test_fail_closed_on_fetch_none():
    _reset_cache()
    orig = fee_source.fetch_hyperliquid_base_fees
    fee_source.fetch_hyperliquid_base_fees = lambda *a, **k: None
    try:
        assert get_venue_costs() == FAIL_CLOSED_FALLBACK
    finally:
        fee_source.fetch_hyperliquid_base_fees = orig


def test_cheaper_live_schedule_does_not_drop_below_base():
    _reset_cache()
    orig = fee_source.fetch_hyperliquid_base_fees
    # Hypothetically "cheaper" schedule — must be clamped UP to the base tier.
    fee_source.fetch_hyperliquid_base_fees = lambda *a, **k: {"taker_bps": 2.0, "maker_bps": 0.5}
    try:
        costs = get_venue_costs()
    finally:
        fee_source.fetch_hyperliquid_base_fees = orig
    assert costs["crypto"]["taker_bps"] == 4.5   # not 2.0
    assert costs["crypto"]["maker_bps"] == 1.5   # not 0.5


def test_ttl_caching_avoids_network():
    _reset_cache()
    calls = {"n": 0}
    orig = fee_source.fetch_hyperliquid_base_fees

    def _counting(*a, **k):
        calls["n"] += 1
        return {"taker_bps": 4.5, "maker_bps": 1.5}

    fee_source.fetch_hyperliquid_base_fees = _counting
    try:
        first = get_venue_costs()
        second = get_venue_costs()   # within TTL -> must not hit network again
    finally:
        fee_source.fetch_hyperliquid_base_fees = orig
    assert first == second
    assert calls["n"] == 1


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
    assert get_round_trip_bps("stock") != 2.0   # the deliberate behavior change


def test_unknown_asset_class_defaults_to_crypto():
    _reset_cache()
    assert get_round_trip_bps("") == 12.0
    assert get_taker_bps("") == 4.5


if __name__ == "__main__":
    import inspect
    for name, fn in sorted(list(globals().items())):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"PASS {name}")
    print("all fee_source tests passed")