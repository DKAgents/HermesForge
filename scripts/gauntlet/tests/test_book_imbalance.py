"""Tests for book_imbalance.py — B1 through B8."""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from book_imbalance import (
    parse_l2_book,
    compute_imbalance,
    compute_depth_usd,
    get_top_n_depth,
    estimate_slippage,
    clear_persistence,
)


# ---------------------------------------------------------------------------
# Helper: create a synthetic Hyperliquid l2Book
# ---------------------------------------------------------------------------
def _make_book(bids, asks):
    """bids/asks: list of (px, sz) tuples. Returns dict matching Hyperliquid format."""
    bid_levels = [{"px": str(px), "sz": str(sz)} for px, sz in bids]
    ask_levels = [{"px": str(px), "sz": str(sz)} for px, sz in asks]
    return {"levels": [bid_levels, ask_levels]}


def _book_from_pairs(bids, asks):
    """bids/asks: list of (px, sz). Returns parsed book dict."""
    return parse_l2_book(_make_book(bids, asks))


# ---------------------------------------------------------------------------
# B1: parse valid l2Book correctly
# ---------------------------------------------------------------------------
def test_parse_valid_book():
    book = _book_from_pairs(
        [(50000, 1.0), (49900, 2.0)],
        [(50100, 1.5), (50200, 3.0)],
    )
    assert len(book["bids"]) == 2
    assert len(book["asks"]) == 2
    # Bids: (price, size_usd = px * sz)
    assert book["bids"][0] == (50000, 50000.0)  # 50000 * 1.0
    assert book["bids"][1] == (49900, 99800.0)  # 49900 * 2.0
    assert book["asks"][0] == (50100, 75150.0)  # 50100 * 1.5
    assert book["asks"][1] == (50200, 150600.0)  # 50200 * 3.0


# ---------------------------------------------------------------------------
# B2: empty book returns neutral imbalance
# ---------------------------------------------------------------------------
def test_empty_book_neutral():
    book = _book_from_pairs([], [])
    imp = compute_imbalance(book)
    assert imp == 0.0


# ---------------------------------------------------------------------------
# B3: all-bids book returns 1.0
# ---------------------------------------------------------------------------
def test_all_bids_book():
    book = _book_from_pairs(
        [(50000, 1.0), (49900, 2.0)],
        [],
    )
    imp = compute_imbalance(book)
    assert imp == 1.0


# ---------------------------------------------------------------------------
# B4: all-asks book returns -1.0
# ---------------------------------------------------------------------------
def test_all_asks_book():
    book = _book_from_pairs(
        [],
        [(50100, 1.5), (50200, 3.0)],
    )
    imp = compute_imbalance(book)
    assert imp == -1.0


# ---------------------------------------------------------------------------
# B5: depth increases with more levels
# ---------------------------------------------------------------------------
def test_depth_increases_with_levels():
    book = _book_from_pairs(
        [(50000, 1.0), (49900, 1.0), (49800, 1.0), (49700, 1.0)],
        [(50100, 1.0), (50200, 1.0), (50300, 1.0), (50400, 1.0)],
    )
    d1 = compute_depth_usd(book, levels=1)["total_depth"]
    d2 = compute_depth_usd(book, levels=2)["total_depth"]
    d4 = compute_depth_usd(book, levels=4)["total_depth"]
    assert d1 > 0
    assert d2 > d1
    assert d4 > d2


# ---------------------------------------------------------------------------
# B6: slippage increases with size (monotonic)
# ---------------------------------------------------------------------------
def test_slippage_increases_with_size():
    # Book with thin depth so slippage is measurable
    book = _book_from_pairs(
        [(50000, 0.1), (49900, 0.5)],  # thin bids
        [(50100, 0.1), (50200, 0.5)],  # thin asks
    )
    slip_small = estimate_slippage(book, 500, "buy")  # ~0.1 BTC worth
    slip_large = estimate_slippage(book, 50000, "buy")  # larger
    # Slippage should be >= for larger size
    assert slip_large >= slip_small


# ---------------------------------------------------------------------------
# B7: slippage is zero for zero size
# ---------------------------------------------------------------------------
def test_slippage_zero_for_zero_size():
    book = _book_from_pairs(
        [(50000, 1.0)],
        [(50100, 1.0)],
    )
    assert estimate_slippage(book, 0, "buy") == 0.0
    assert estimate_slippage(book, -100, "buy") == 0.0


# ---------------------------------------------------------------------------
# B8: persistence sampling smooths spikes
# ---------------------------------------------------------------------------
def test_persistence_smooths_spikes():
    clear_persistence()

    book = _book_from_pairs(
        [(50000, 1.0), (49900, 1.0)],
        [(50100, 1.0), (50200, 1.0)],
    )

    # First call: normal imbalance with persistence key "test_symbol"
    imp1 = compute_imbalance(book, persistence=True, persistence_key="test_symbol")
    # bid_usd = 50000 + 99800 = 149800
    # ask_usd = 50100 + 150600 = 200700
    # imbalance = (149800 - 200700) / 350500 = -0.145...
    assert -0.2 < imp1 < 0.0

    # Second call: same key, slightly different book
    imp2 = compute_imbalance(book, persistence=True, persistence_key="test_symbol")
    assert -0.2 < imp2 < 0.0

    # Now a spike (huge bid appears) — raw should be very positive
    spike_book = _book_from_pairs(
        [(50000, 100.0), (49900, 1.0)],
        [(50100, 1.0), (50200, 1.0)],
    )
    imp_spike_raw = compute_imbalance(spike_book, persistence=False)
    # Raw spike: bid_usd = 50000*100 + 49900*1 = 5000000 + 49900 = 5049900
    # ask_usd = 50100 + 150600 = 200700
    # imbalance = (5049900 - 200700) / 5250600 ≈ 0.923...
    assert imp_spike_raw > 0.8

    # Persisted spike should be smoothed (averaged with prior two samples)
    imp_spike_smooth = compute_imbalance(spike_book, persistence=True, persistence_key="test_symbol")
    # Should be between the raw spike and the prior average
    # Prior average ≈ (imp1 + imp2) / 2 ≈ -0.145
    # With window=3, smoothed = (raw + imp1 + imp2) / 3
    # ≈ (0.923 + (-0.145) * 2) / 3 ≈ (0.923 - 0.29) / 3 ≈ 0.211
    assert imp_spike_smooth < imp_spike_raw, f"Expected smoothed {imp_spike_smooth} < raw {imp_spike_raw}"
    assert imp_spike_smooth < 0.5, f"Persistence should dampen spike, got {imp_spike_smooth}"

    clear_persistence()