"""Tests for horizon_policy.py — US-204 (5m seed gate / 4h–7d preference)."""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import horizon_policy as hp  # noqa: E402

# Fixed hurdle for deterministic offline tests (4x all-in taker ~ 46 bps).
_HURDLE = 46.0


def test_parse_horizon_max_minutes():
    assert hp.parse_horizon_max_minutes("5m") == 5
    assert hp.parse_horizon_max_minutes("1-5d") == 7200
    assert hp.parse_horizon_max_minutes("4-48h") == 2880
    assert hp.parse_horizon_max_minutes("5m-4h") == 240
    assert hp.parse_horizon_max_minutes("1h-6h") == 360
    assert hp.parse_horizon_max_minutes("daily") is None
    assert hp.parse_horizon_max_minutes("") is None


def test_is_5m_seed():
    assert hp.is_5m_seed("5m") is True
    assert hp.is_5m_seed("1m-5m") is True
    assert hp.is_5m_seed("5m-15m") is False   # holds up to 15m
    assert hp.is_5m_seed("4h-48h") is False
    assert hp.is_5m_seed("1-5d") is False


def test_horizon_tagging():
    assert hp.horizon_tag("5m") == "fast"
    assert hp.horizon_tag("4h-48h") == "preferred"
    assert hp.horizon_tag("1-5d") == "preferred"
    assert hp.horizon_tag("15m") == "other"


def test_non_5m_seed_admits():
    ok, errs = hp.validate_horizon(
        {"horizon": "4h-48h", "execution_mode": "taker",
         "expected_gross_edge_bps": 15}, hurdle_bps=_HURDLE)
    assert ok and errs == []


def test_5m_maker_seed_admits():
    ok, errs = hp.validate_horizon(
        {"horizon": "5m", "execution_mode": "maker",
         "expected_gross_edge_bps": 8}, hurdle_bps=_HURDLE)
    assert ok and errs == []


def test_5m_taker_seed_without_argument_rejected():
    ok, errs = hp.validate_horizon(
        {"horizon": "5m", "execution_mode": "taker",
         "expected_gross_edge_bps": 60}, hurdle_bps=_HURDLE)
    assert not ok
    assert any("fast_horizon_argument" in e for e in errs)


def test_5m_taker_seed_below_hurdle_rejected():
    ok, errs = hp.validate_horizon(
        {"horizon": "5m", "execution_mode": "taker",
         "expected_gross_edge_bps": 8,
         "fast_horizon_argument": "arg"}, hurdle_bps=_HURDLE)
    assert not ok
    assert any("hurdle" in e for e in errs)


def test_5m_taker_seed_with_argument_and_edge_admits():
    ok, errs = hp.validate_horizon(
        {"horizon": "5m", "execution_mode": "taker",
         "expected_gross_edge_bps": 60,
         "fast_horizon_argument": "gross edge 60bps clears 4x taker cost"},
        hurdle_bps=_HURDLE)
    assert ok and errs == []


if __name__ == "__main__":
    for name, fn in sorted(list(globals().items())):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"PASS {name}")
    print("all horizon_policy tests passed")