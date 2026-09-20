#!/usr/bin/env python3
"""test_asset_eligibility.py — Unit tests for per-asset strategy eligibility."""

import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))
from asset_eligibility import (
    is_eligible, get_eligible, add_eligible,
    get_all_eligible_tickers, ELIGIBLE,
)

# ── T1: known eligible ticker ──
def test_known_eligible():
    assert is_eligible("STR-Q-liquidity-sweep", "NVDA")
    assert is_eligible("STR-Q-liquidity-sweep", "nvda")  # case-insensitive
    assert is_eligible("STR-B-macd-histogram-divergence", "DIA")  # DIA confirmed in backtest

# ── T2: known ineligible ticker ──
def test_known_ineligible():
    assert not is_eligible("STR-Q-liquidity-sweep", "PEPE")
    assert not is_eligible("STR-Q-liquidity-sweep", "BITCOIN")

# ── T3: unknown strategy returns False ──
def test_unknown_strategy():
    assert not is_eligible("NONEXISTENT-STRATEGY", "NVDA")
    assert get_eligible("NONEXISTENT") == set()

# ── T4: add_eligible works ──
def test_add_eligible():
    sid = "TEST-ADD-STRATEGY"
    assert not is_eligible(sid, "TESTCOIN")
    add_eligible(sid, "TESTCOIN")
    assert is_eligible(sid, "TESTCOIN")
    add_eligible(sid, "TESTCOIN2")
    assert "TESTCOIN2" in get_eligible(sid)
    # Cleanup
    del ELIGIBLE[sid]

# ── T5: all tickers aggregate correctly ──
def test_all_tickers():
    all_t = get_all_eligible_tickers()
    assert "NVDA" in all_t
    assert "AVAX" in all_t
    assert "BTC" in all_t
    assert "AAPL" in all_t
    assert len(all_t) > 10  # we have many

# ── T6: STR-QW only has AVAX and LINK ──
def test_str_qw_limited():
    tickers = get_eligible("STR-QW-liquidity-sweep-wide")
    assert tickers == {"AVAX", "LINK"}

# ── T7: empty string ticker ──
def test_empty_ticker():
    assert not is_eligible("STR-B-macd-histogram-divergence", "")
    assert not is_eligible("", "NVDA")

# ── Run ──
if __name__ == "__main__":
    tests = [
        test_known_eligible, test_known_ineligible, test_unknown_strategy,
        test_add_eligible, test_all_tickers, test_str_qw_limited,
        test_empty_ticker,
    ]
    passed = 0
    for t in tests:
        try:
            t()
            print(f"  ✅ {t.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"  ❌ {t.__name__}: {e}")
    
    print(f"\n{passed}/{len(tests)} passed")