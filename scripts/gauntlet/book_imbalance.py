"""
Book imbalance module for G0 cost pre-screening (PROP-001 Strategy Gauntlet).

Handles Hyperliquid l2Book format and computes imbalance, depth, and slippage
estimates for cost screening.
"""
from __future__ import annotations

import json
from collections import deque
from typing import Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Persistence sampling — smooth book snapshots to filter spoofed size
# ---------------------------------------------------------------------------
_persistence_buffers: Dict[str, deque] = {}
_PERSISTENCE_WINDOW = 3


def _sample_persistence(key: str, imbalance: float) -> float:
    """Average the last _PERSISTENCE_WINDOW imbalance values for the given key."""
    if key not in _persistence_buffers:
        _persistence_buffers[key] = deque(maxlen=_PERSISTENCE_WINDOW)
    buf = _persistence_buffers[key]
    buf.append(imbalance)
    return sum(buf) / len(buf)


def clear_persistence():
    """Clear all persistence buffers (used in tests)."""
    _persistence_buffers.clear()


# ---------------------------------------------------------------------------
# L2 book parsing
# ---------------------------------------------------------------------------
def parse_l2_book(l2_data) -> Dict[str, List[Tuple[float, float]]]:
    """
    Parse Hyperliquid l2Book format into {bids, asks}.

    Expected input: dict or JSON string with keys 'levels', where each level
    is a list of two lists: [[bid_levels], [ask_levels]]. Each level entry
    is {px, sz} in Hyperliquid format.

    Returns:
        {'bids': [(price, size_usd), ...], 'asks': [(price, size_usd), ...]}
        Bids sorted descending (highest first), asks sorted ascending (lowest first).
    """
    if isinstance(l2_data, str):
        l2_data = json.loads(l2_data)

    bids = []
    asks = []

    levels = l2_data.get("levels", [])
    if not levels:
        return {"bids": [], "asks": []}

    # levels[0] = bid levels list, levels[1] = ask levels list
    bid_levels = levels[0] if len(levels) > 0 else []
    ask_levels = levels[1] if len(levels) > 1 else []

    for level in bid_levels:
        px = float(level.get("px", 0))
        sz = float(level.get("sz", 0))
        size_usd = px * sz
        bids.append((px, size_usd))

    for level in ask_levels:
        px = float(level.get("px", 0))
        sz = float(level.get("sz", 0))
        size_usd = px * sz
        asks.append((px, size_usd))

    # Bids already come in descending order from Hyperliquid
    # Asks already come in ascending order
    return {"bids": bids, "asks": asks}


def _book_to_dict(book, depth_levels: int = 5) -> Dict:
    """Normalize book to dict with bids/asks, ensuring depth_levels is applied."""
    if isinstance(book, dict):
        bids = book.get("bids", [])[:depth_levels]
        asks = book.get("asks", [])[:depth_levels]
        return {"bids": bids, "asks": asks}
    return {"bids": [], "asks": []}


# ---------------------------------------------------------------------------
# Imbalance computation
# ---------------------------------------------------------------------------
def compute_imbalance(book, depth_levels: int = 5, persistence: bool = False,
                     persistence_key: Optional[str] = None) -> float:
    """
    Compute order book imbalance: (bid_usd - ask_usd) / (bid_usd + ask_usd).

    Returns float in [-1, 1]:
        +1.0 = all bids, no asks
        -1.0 = all asks, no bids
         0.0 = perfectly balanced

    If persistence=True, smooths the result over the last 3 samples for the
    same book state (keyed by persistence_key if provided, otherwise a hash of
    the book contents).
    """
    b = _book_to_dict(book, depth_levels)
    bids = b["bids"]
    asks = b["asks"]

    bid_usd = sum(sz for _, sz in bids)
    ask_usd = sum(sz for _, sz in asks)
    total = bid_usd + ask_usd

    if total == 0:
        return 0.0

    raw = (bid_usd - ask_usd) / total

    if persistence:
        key = persistence_key if persistence_key else str(hash((tuple(bids), tuple(asks))))
        return _sample_persistence(key, raw)

    return raw


# ---------------------------------------------------------------------------
# Depth computation
# ---------------------------------------------------------------------------
def compute_depth_usd(book, levels: int = 5) -> Dict[str, float]:
    """
    Compute total USD depth within the first `levels` on each side.

    Returns:
        {'bid_depth': float, 'ask_depth': float, 'total_depth': float}
    """
    b = _book_to_dict(book, levels)
    bids = b["bids"]
    asks = b["asks"]

    bid_depth = sum(sz for _, sz in bids)
    ask_depth = sum(sz for _, sz in asks)

    return {
        "bid_depth": bid_depth,
        "ask_depth": ask_depth,
        "total_depth": bid_depth + ask_depth,
    }


def get_top_n_depth(book, n: int = 5) -> float:
    """Return total USD within the top N levels on each side combined."""
    depth = compute_depth_usd(book, levels=n)
    return depth["total_depth"]


# ---------------------------------------------------------------------------
# Slippage estimation
# ---------------------------------------------------------------------------
def estimate_slippage(book, size_usd: float, side: str) -> float:
    """
    Estimate slippage in bps for executing `size_usd` on the given side.

    Walks the order book levels, computing VWAP, then returns the difference
    from mid-price in basis points (1 bp = 0.01%).

    Args:
        book: parsed book dict with bids/asks
        size_usd: intended order size in USD
        side: 'buy' or 'sell'

    Returns:
        Slippage in bps (non-negative). Returns 0.0 if size_usd <= 0.
    """
    if size_usd <= 0:
        return 0.0

    b = _book_to_dict(book, depth_levels=len(book.get("asks", [])) + len(book.get("bids", [])))
    bids = b["bids"]
    asks = b["asks"]

    if not bids or not asks:
        return 0.0

    best_bid = bids[0][0] if bids else 0
    best_ask = asks[0][0] if asks else 0
    mid = (best_bid + best_ask) / 2 if best_bid and best_ask else 0

    if mid == 0:
        return 0.0

    levels_to_walk = asks if side == "buy" else bids
    if not levels_to_walk:
        return 0.0

    remaining = size_usd
    total_cost = 0.0
    total_filled = 0.0

    for px, usd_available in levels_to_walk:
        if remaining <= 0:
            break
        fill = min(remaining, usd_available)
        total_cost += fill * px
        total_filled += fill
        remaining -= fill

    if total_filled == 0:
        return 0.0

    vwap = total_cost / total_filled

    if side == "buy":
        # VWAP above mid = slippage cost
        diff_bps = (vwap - best_ask) / best_ask * 10000
    else:
        # VWAP below mid = slippage cost
        diff_bps = (best_bid - vwap) / best_bid * 10000

    return max(0.0, abs(diff_bps))