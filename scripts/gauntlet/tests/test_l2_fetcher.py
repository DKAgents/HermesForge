#!/usr/bin/env python3
"""test_l2_fetcher.py — Unit tests for L2 orderbook fill simulation (mocked)."""

import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))
from l2_fetcher import simulate_realistic_fill

# ── Mock L2Book object (TypedDict with dot-access attributes) ──
class MockL2Book:
    """Mock L2Book that supports both dict and attribute access."""
    def __init__(self, bids, asks, mid_price):
        self.bids = bids
        self.asks = asks
        self.mid_price = mid_price
    
    def get(self, key):
        return getattr(self, key, None)

BTC_BOOK = MockL2Book(
    bids=[[81230.0, 0.5], [81229.5, 1.2], [81229.0, 0.8]],
    asks=[[81231.0, 0.3], [81231.5, 1.5], [81232.0, 0.7], [81233.0, 3.0]],
    mid_price=81230.5,
)

# ── T1: realistic long fill at mid (limit rests) ──
def test_realistic_long_at_mid():
    result = simulate_realistic_fill(BTC_BOOK, 81230.5, "long", 1000, "realistic")
    assert result["fill_price"] == 81230.5, f"Expected mid fill, got {result}"
    assert result["slippage_bps"] == 0, f"Expected 0 slip"

# ── T2: realistic long above best ask (aggressive, walks book) ──
def test_realistic_long_aggressive():
    result = simulate_realistic_fill(BTC_BOOK, 81232.0, "long", 2000, "realistic")
    assert result["fill_price"] >= 81231.0, f"Expected above best ask"
    assert result["fill_price"] <= 81232.0, f"Expected below entry"

# ── T3: pessimistic long — VWAP through book + 1 tick adverse ──
def test_pessimistic_long():
    result = simulate_realistic_fill(BTC_BOOK, 81230.5, "long", 1000, "pessimistic")
    # Pessimistic walks all ask levels, VWAP + 1 tick
    assert result["fill_price"] > 81231.0, f"Expected above best ask (fills across book), got {result}"
    assert result["levels_consumed"] >= 1, f"Expected multi-level fill, got {result}"
    assert result["slippage_bps"] > 0, f"Expected positive slippage on aggressive long"

# ── T4: short realistic at mid ──
def test_realistic_short_at_mid():
    result = simulate_realistic_fill(BTC_BOOK, 81230.5, "short", 1000, "realistic")
    assert result["fill_price"] == 81230.5

# ── T5: short pessimistic — VWAP through bid book - 1 tick ──
def test_pessimistic_short():
    result = simulate_realistic_fill(BTC_BOOK, 81230.5, "short", 100, "pessimistic")
    # Pessimistic walks bid levels for $100 — should fill near best bid
    assert result["levels_consumed"] >= 1, f"Expected fills, got {result}"
    assert result["slippage_bps"] < 0, f"Expected negative slippage on short, got {result['slippage_bps']}"

# ── T6: large size walks multiple levels ──
def test_large_size_multilevel():
    thin = MockL2Book(
        bids=[[80000.0, 0.01]],
        asks=[[80100.0, 0.01], [80200.0, 0.02], [80300.0, 10.0]],
        mid_price=80050.0,
    )
    result = simulate_realistic_fill(thin, 80200.0, "long", 2000, "realistic")
    assert result["fill_price"] > 80100.0, f"Expected above first ask, got {result}"
    assert result["levels_consumed"] >= 1, f"Expected multi-level, got {result['levels_consumed']}"

# ── T7: empty book → falls back to mid ──
def test_empty_book():
    empty = MockL2Book(bids=[], asks=[], mid_price=50000.0)
    result = simulate_realistic_fill(empty, 50000.0, "long", 1000, "realistic")
    assert result["fill_price"] == 50000.0

# ── T8: zero size → returns entry price ──
def test_zero_size():
    result = simulate_realistic_fill(BTC_BOOK, 81230.5, "long", 0, "realistic")
    assert result["fill_price"] == 81230.5

# ── T9: mode defaults to realistic ──
def test_default_mode():
    result = simulate_realistic_fill(BTC_BOOK, 81230.5, "long", 1000)
    assert "fill_price" in result

# ── Run ──
if __name__ == "__main__":
    tests = [
        test_realistic_long_at_mid, test_realistic_long_aggressive,
        test_pessimistic_long, test_realistic_short_at_mid,
        test_pessimistic_short, test_large_size_multilevel,
        test_empty_book, test_zero_size, test_default_mode,
    ]
    passed = 0
    for t in tests:
        try:
            t()
            print(f"  ✅ {t.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"  ❌ {t.__name__}: {e}")
        except Exception as e:
            print(f"  💥 {t.__name__}: {type(e).__name__}: {e}")
    
    print(f"\n{passed}/{len(tests)} passed")