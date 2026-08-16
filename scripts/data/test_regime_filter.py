#!/usr/bin/env python3
"""
test_regime_filter.py — Tests for the real regime_filter module.

Run:
    cd ~/HermesForge/scripts/data && python3 test_regime_filter.py

Tests cover:
  1. get_regime() returns a valid dict with all required fields
  2. tag_signal() mutates signal dict correctly
  3. Graceful degradation (missing data)
  4. Look-ahead-free (as_of parameter)
  5. Integration with real cached data (offline)
  6. Performance (<1s)
"""

import sys
import os
import time
import pathlib
import shutil

# Ensure scripts/data is on the path
HERE = pathlib.Path(__file__).parent.resolve()
sys.path.insert(0, str(HERE))

from regime_filter import (
    get_regime,
    tag_signal,
    MARKET_DATA_DIR,
    _check_freshness,
    _compute_vix,
    _compute_dxy,
    _compute_yields,
    _compute_fear_greed,
    _compute_spy_trend,
    _compute_breadth,
    _compute_correlation,
    _get_close,
)

PASS = 0
FAIL = 0
FAILURES = []


def check(name, condition, detail=""):
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  PASS: {name}")
    else:
        FAIL += 1
        FAILURES.append((name, detail))
        print(f"  FAIL: {name} — {detail}")


def test_get_regime_structure():
    print("\n[1] get_regime() returns valid dict with all required fields")
    r = get_regime()
    check("returns dict", isinstance(r, dict))
    check("has overall", "overall" in r, f"keys: {list(r.keys())}")
    check("has stock_regime", "stock_regime" in r)
    check("has crypto_regime", "crypto_regime" in r)
    check("has confidence", "confidence" in r)
    check("has data_freshness", "data_freshness" in r)
    check("has timestamp", "timestamp" in r)
    check("has components", "components" in r)
    # confidence in [0,1]
    conf = r.get("confidence", -1)
    check("confidence in [0,1]", 0.0 <= conf <= 1.0, f"conf={conf}")
    # overall is a known regime
    valid_regimes = {"risk_on", "risk_off", "neutral", "caution",
                     "unified", "diversified", "unknown"}
    check("overall is valid regime", r.get("overall") in valid_regimes,
          f"overall={r.get('overall')}")
    # sub-component dicts
    for key in ("vix", "dxy", "yields", "fear_greed", "breadth",
                "spy_trend", "correlation", "vol_risk_premium",
                "put_call", "tvl", "stablecoin", "rotation", "funding",
                "economic_events"):
        check(f"has {key}", key in r)
    # vix.current is numeric
    check("vix.current is numeric", isinstance(r.get("vix", {}).get("current"), (int, float)))
    # legacy fields expected by regime_strategy_selector
    check("vix has regime", "regime" in r.get("vix", {}))
    check("dxy has trend", "trend" in r.get("dxy", {}))
    check("fear_greed has value", "value" in r.get("fear_greed", {}))
    check("breadth has pct_above_50ma", "pct_above_50ma" in r.get("breadth", {}))
    check("correlation has correlation_regime", "correlation_regime" in r.get("correlation", {}))


def test_tag_signal_mutation():
    print("\n[2] tag_signal() mutates signal dict correctly")
    r = get_regime()
    sig = {"strategy_id": "STR-I-AAPL-20260814", "asset_class": "stock"}
    sig_id = id(sig)
    ret = tag_signal(sig, r)
    check("returns same object", id(ret) == id(sig))
    check("mutates in place", id(sig) == sig_id)
    required_keys = ("regime", "regime_confidence", "regime_compatible",
                     "regime_action", "regime_risk_multiplier", "regime_tagged_at")
    for k in required_keys:
        check(f"has {k}", k in sig, f"missing {k}")
    check("regime is str", isinstance(sig.get("regime"), str))
    check("regime_confidence is float", isinstance(sig.get("regime_confidence"), (int, float)))
    check("regime_compatible is bool", isinstance(sig.get("regime_compatible"), bool))
    check("regime_action in valid set",
          sig.get("regime_action") in {"boost", "run", "reduce", "suppress"},
          f"action={sig.get('regime_action')}")
    check("regime_risk_multiplier in [0,2]",
          0.0 <= sig.get("regime_risk_multiplier", -1) <= 2.0)
    check("regime_tagged_at is str", isinstance(sig.get("regime_tagged_at"), str))


def test_tag_signal_no_regime():
    print("\n[2b] tag_signal() with regime=None calls get_regime() internally")
    sig = {"strategy_id": "STR-B-AAPL-20260814"}
    ret = tag_signal(sig, None)
    check("returns signal", isinstance(ret, dict))
    check("has regime key", "regime" in ret)


def test_tag_signal_unknown_strat():
    print("\n[2c] tag_signal() with unknown strategy_id -> action=run (no block)")
    r = get_regime()
    sig = {"strategy_id": "STR-ZZZ-FAKE-20260814"}
    tag_signal(sig, r)
    check("unknown strat not suppressed",
          sig.get("regime_action") in ("run", "reduce"),
          f"action={sig.get('regime_action')}")
    check("unknown strat risk_mult > 0", sig.get("regime_risk_multiplier", 0) > 0)


def test_tag_signal_confidence_zero():
    print("\n[2d] tag_signal() with confidence=0 regime -> unknown tags")
    fake_regime = {"overall": "neutral", "confidence": 0.0}
    sig = {"strategy_id": "STR-I-AAPL-20260814"}
    tag_signal(sig, fake_regime)
    check("regime = unknown", sig.get("regime") == "unknown")
    check("action = run", sig.get("regime_action") == "run")
    check("risk_mult = 1.0", sig.get("regime_risk_multiplier") == 1.0)


def test_graceful_degradation():
    print("\n[3] Graceful degradation (missing data)")
    # Point MARKET_DATA_DIR to a temp empty dir
    import regime_filter as rf
    orig_dir = rf.MARKET_DATA_DIR
    # Clear the breadth cache so the previous real-data call doesn't bleed through
    rf._breadth_cache["value"] = None
    rf._breadth_cache["timestamp"] = 0.0
    rf._breadth_cache["as_of_key"] = None
    tmp = pathlib.Path("/tmp/regime_test_empty_dir")
    if tmp.exists():
        shutil.rmtree(tmp)
    tmp.mkdir()
    rf.MARKET_DATA_DIR = tmp
    try:
        r = get_regime()
        check("never raises", isinstance(r, dict))
        check("overall = neutral on total failure",
              r.get("overall") == "neutral", f"overall={r.get('overall')}")
        check("confidence = 0 on total failure",
              r.get("confidence") == 0.0, f"conf={r.get('confidence')}")
        check("data_freshness = unavailable",
              r.get("data_freshness") == "unavailable")
        check("has reason or error field",
              "reason" in r or "error" in r)
    finally:
        rf.MARKET_DATA_DIR = orig_dir
        shutil.rmtree(tmp, ignore_errors=True)


def test_look_ahead_free():
    print("\n[4] Look-ahead-free (as_of parameter)")
    # Use a date well before the latest data
    r_now = get_regime()
    r_old = get_regime(as_of="2026-01-15")
    check("as_of returns dict", isinstance(r_old, dict))
    check("as_of stored", r_old.get("as_of") == "2026-01-15")
    # VIX should differ between dates (unless identical by coincidence)
    vix_now = r_now.get("vix", {}).get("current", 0)
    vix_old = r_old.get("vix", {}).get("current", 0)
    check("as_of truncates VIX data", vix_old > 0,
          f"vix_old={vix_old}")
    # as_of Jan vs Aug should produce different VIX (look-ahead-free)
    check("VIX differs across dates", vix_now != vix_old,
          f"now={vix_now} old={vix_old}")
    # SPY data truncated
    spy_old = r_old.get("spy_trend", {})
    check("as_of SPY has close", "close" in spy_old)
    check("as_of SPY close < now SPY close (older date)",
          spy_old.get("close", 0) < r_now.get("spy_trend", {}).get("close", 1e9),
          f"old={spy_old.get('close')} now={r_now.get('spy_trend',{}).get('close')}")


def test_real_data_integration():
    print("\n[5] Integration with real cached data (offline)")
    if not MARKET_DATA_DIR.exists():
        check("market_data dir exists", False, str(MARKET_DATA_DIR))
        return
    r = get_regime()
    check("returns regime", isinstance(r, dict))
    # VIX should be available and a sane value
    vix = r.get("vix", {})
    check("VIX available", vix.get("available", False))
    check("VIX in sane range", 5 < vix.get("current", 0) < 100,
          f"vix={vix.get('current')}")
    # SPY should be available
    spy = r.get("spy_trend", {})
    check("SPY available", spy.get("available", False))
    check("SPY close > 0", spy.get("close", 0) > 0)
    # Breadth should sample ~100 stocks
    br = r.get("breadth", {})
    check("breadth sample_size > 0", br.get("sample_size", 0) > 0,
          f"n={br.get('sample_size')}")
    check("breadth pct in [0,100]",
          0 <= br.get("pct_above_50ma", -1) <= 100)
    # components should have 7 entries
    comps = r.get("components", {})
    check("7 components", len(comps) == 7, f"got {len(comps)}")
    # at least VIX and SPY should be available
    check("vix component available",
          comps.get("vix", {}).get("available", False))
    check("spy component available",
          comps.get("spy_trend", {}).get("available", False))


def test_performance():
    print("\n[6] Performance (<1s)")
    t0 = time.time()
    get_regime()
    elapsed = time.time() - t0
    check("get_regime < 1.0s", elapsed < 1.0, f"elapsed={elapsed:.3f}s")
    check("get_regime < 0.7s (headroom)", elapsed < 0.7, f"elapsed={elapsed:.3f}s")
    # second call should use breadth cache
    t0 = time.time()
    get_regime()
    elapsed2 = time.time() - t0
    check("second call faster (cache)", elapsed2 <= elapsed + 0.1,
          f"call1={elapsed:.3f}s call2={elapsed2:.3f}s")


def test_component_functions():
    print("\n[7] Component functions return sane values")
    vix = _compute_vix()
    check("vix has regime", "regime" in vix)
    check("vix has score", "score" in vix)
    check("vix score in [0,1]", 0.0 <= vix.get("score", -1) <= 1.0)
    dxy = _compute_dxy()
    check("dxy has trend", "trend" in dxy)
    yld = _compute_yields()
    check("yields has t10y", "t10y" in yld)
    fg = _compute_fear_greed()
    check("fear_greed has value", "value" in fg)
    spy = _compute_spy_trend()
    check("spy has trend", "trend" in spy)
    br = _compute_breadth()
    check("breadth has sample_size", "sample_size" in br)
    corr = _compute_correlation()
    check("correlation has regime", "correlation_regime" in corr)


def test_strategy_selector_integration():
    print("\n[8] regime_strategy_selector integration")
    repo_root = pathlib.Path(HERE).parent.parent
    sys.path.insert(0, str(repo_root / "scripts" / "research"))
    sys.path.insert(0, str(repo_root / "scripts" / "paper_trading"))
    try:
        from regime_strategy_selector import get_strategy_directives
        d = get_strategy_directives()
        check("directives is dict", isinstance(d, dict))
        check("has directives key", "directives" in d)
        directives = d.get("directives", {})
        check("has >0 strategies", len(directives) > 0, f"n={len(directives)}")
        # each directive should have an action
        for sid, dd in list(directives.items())[:3]:
            check(f"{sid} has action", "action" in dd, f"keys={list(dd.keys())}")
    except Exception as e:
        check("strategy selector import works", False, str(e))


def main():
    print("=" * 60)
    print("regime_filter test suite — US-116")
    print("=" * 60)
    test_get_regime_structure()
    test_tag_signal_mutation()
    test_tag_signal_no_regime()
    test_tag_signal_unknown_strat()
    test_tag_signal_confidence_zero()
    test_graceful_degradation()
    test_look_ahead_free()
    test_real_data_integration()
    test_performance()
    test_component_functions()
    test_strategy_selector_integration()
    print("\n" + "=" * 60)
    print(f"RESULTS: {PASS} passed, {FAIL} failed")
    print("=" * 60)
    if FAIL:
        print("\nFailures:")
        for name, detail in FAILURES:
            print(f"  - {name}: {detail}")
        sys.exit(1)
    print("ALL TESTS PASSED")
    sys.exit(0)


if __name__ == "__main__":
    main()
