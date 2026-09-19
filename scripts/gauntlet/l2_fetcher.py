#!/usr/bin/env python3
"""
l2_fetcher.py — Fetch live L2 orderbook snapshots from Hyperliquid REST API
and simulate realistic fills against real book depth.

Free, no auth required. Integrates with the G3 execution-realism pipeline
to get venue-accurate fill prices at signal time.

Usage:
    from l2_fetcher import fetch_l2_book, simulate_realistic_fill

    book = fetch_l2_book("BTC")
    result = simulate_realistic_fill(book, entry_price=61000, direction="long", size_usd=1000)
    # result: {"fill_price": 61005.50, "slippage_bps": 0.90, ...}
"""

import json
import urllib.request
from dataclasses import dataclass, field
from typing import List, Tuple, Optional


HYPERLIQUID_INFO_URL = "https://api.hyperliquid.xyz/info"


@dataclass
class L2Book:
    """Parsed L2 orderbook ready for fill simulation."""
    coin: str
    mid_price: float
    bids: List[Tuple[float, float]]  # (px, sz_usd) — sorted best first
    asks: List[Tuple[float, float]]  # (px, sz_usd) — sorted best first
    timestamp: float = 0.0


def fetch_l2_book(coin: str) -> L2Book:
    """
    Fetch current L2 orderbook from Hyperliquid's free REST API.
    
    Hyperliquid l2Book returns sizes in coin units per level.
    We convert to USD: sz_usd = sz_coins * px.
    """
    payload = json.dumps({"type": "l2Book", "coin": coin.upper()}).encode()
    req = urllib.request.Request(
        HYPERLIQUID_INFO_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        raw = json.loads(resp.read())

    levels = raw.get("levels", [[], []])
    
    bids_raw = []
    asks_raw = []
    
    # Hyperliquid l2Book format: levels[0]=bids, levels[1]=asks
    # Each level is {"px": ..., "sz": ..., "n": ...} or [px, sz, n]
    for side_idx, target in [(0, bids_raw), (1, asks_raw)]:
        if side_idx < len(levels) and levels[side_idx]:
            for level in levels[side_idx]:
                if isinstance(level, dict):
                    target.append((float(level["px"]), float(level["sz"])))
                elif isinstance(level, list) and len(level) >= 2:
                    target.append((float(level[0]), float(level[1])))

    # Convert coin units to USD
    bids = [(px, sz * px) for px, sz in bids_raw]
    asks = [(px, sz * px) for px, sz in asks_raw]

    # Bids already come sorted descending (best first), asks ascending
    mid = 0.0
    if bids and asks:
        mid = (bids[0][0] + asks[0][0]) / 2
    elif bids:
        mid = bids[0][0]
    elif asks:
        mid = asks[0][0]

    return L2Book(
        coin=coin,
        mid_price=mid,
        bids=bids,
        asks=asks,
        timestamp=raw.get("time", 0),
    )


def simulate_realistic_fill(
    book: L2Book,
    entry_price: float,
    direction: str,
    size_usd: float,
    mode: str = "realistic",
) -> dict:
    """
    Simulate a fill against real L2 depth.

    Args:
        book: live L2 orderbook
        entry_price: intended entry price (signal's limit price)
        direction: 'long' (buy) or 'short' (sell)
        size_usd: position size in USD
        mode: 'realistic' — limit fills only if price trades through;
              'pessimistic' — always market fill + adverse selection

    Returns:
        dict with fill_price, slippage_bps, fill_mode, levels_consumed, error
    """
    is_buy = direction.lower() in ("long", "bullish")
    levels = book.asks if is_buy else book.bids
    best = levels[0][0] if levels else book.mid_price

    result = {
        "fill_price": entry_price,
        "slippage_bps": 0.0,
        "fill_mode": mode,
        "levels_consumed": 0,
        "book_mid": book.mid_price,
        "best_quote": best,
        "error": None,
        "top5_depth_usd": sum(sz for _, sz in levels[:5]),
    }

    if not levels:
        result["error"] = "empty orderbook"
        return result

    if size_usd <= 0:
        return result

    if mode == "pessimistic":
        # Always cross the spread + add adverse selection
        remaining = size_usd
        total_cost = 0.0
        consumed = 0
        for px, sz in levels:
            take = min(remaining, sz)
            total_cost += take * px
            remaining -= take
            consumed += 1
            if remaining <= 0:
                break
        
        if remaining > 0:
            # Not enough depth — fill remainder at last price + 0.1% adverse
            last_px = levels[-1][0] if levels else best
            total_cost += remaining * last_px * 1.001
        
        fill_price = total_cost / size_usd if size_usd > 0 else entry_price
        # Add 1 tick adverse selection
        tick = 0.1  # Hyperliquid tick for most coins
        if is_buy:
            fill_price += tick
        else:
            fill_price -= tick
        
        result["fill_price"] = fill_price
        result["levels_consumed"] = consumed

    elif mode == "realistic":
        # Limit order: fills only if the price trades through the limit
        # For a buy: fill if best_ask <= entry_price (someone is selling at or below our limit)
        # For a sell: fill if best_bid >= entry_price (someone is buying at or above our limit)
        if is_buy:
            fills_at_limit = [l for l in levels if l[0] <= entry_price]
        else:
            fills_at_limit = [l for l in levels if l[0] >= entry_price]

        if not fills_at_limit:
            # Limit order not filled — book hasn't traded through
            result["fill_price"] = entry_price  # optimistic (resting order)
            result["fill_mode"] = "resting"
            result["slippage_bps"] = 0.0
            return result

        # Fill at VWAP of available levels at or better than limit
        remaining = size_usd
        total_cost = 0.0
        consumed = 0
        for px, sz in fills_at_limit:
            take = min(remaining, sz)
            total_cost += take * px
            remaining -= take
            consumed += 1
            if remaining <= 0:
                break

        if remaining > 0:
            # Partial fill — remainder rests (or we treat as filled at limit)
            total_cost += remaining * entry_price

        fill_price = total_cost / size_usd if size_usd > 0 else entry_price
        result["fill_price"] = fill_price
        result["levels_consumed"] = consumed

    # Compute slippage
    if entry_price > 0:
        if is_buy:
            result["slippage_bps"] = (fill_price - entry_price) / entry_price * 10000
        else:
            result["slippage_bps"] = (entry_price - fill_price) / entry_price * 10000

    return result


def get_gauntlet_entry(signal_dict: dict, size_usd: float = 1000) -> dict:
    """
    Full G3 pipeline for one signal: fetch L2, simulate fill, compute adjusted prices.

    Takes a signal dict (from scanner) and returns a dict with:
        optimistic_entry, realistic_entry, pessimistic_entry,
        realistic_slippage_bps, pessimistic_slippage_bps,
        book_mid, top5_depth, error
    """
    coin = signal_dict.get("ticker", "BTC").upper()
    entry_price = float(signal_dict.get("entry_price", 0))
    direction = signal_dict.get("direction", "long")
    asset_class = signal_dict.get("asset_class", "crypto")

    result = {
        "optimistic_entry": entry_price,
        "realistic_entry": entry_price,
        "pessimistic_entry": entry_price,
        "realistic_slippage_bps": 0.0,
        "pessimistic_slippage_bps": 0.0,
        "book_mid": entry_price,
        "top5_depth_usd": 0.0,
        "error": None,
    }

    # Only apply to crypto (stocks don't have Hyperliquid L2)
    if asset_class != "crypto":
        return result

    try:
        book = fetch_l2_book(coin)
    except Exception as e:
        result["error"] = f"L2 fetch failed: {e}"
        return result

    result["book_mid"] = book.mid_price

    # Simulate realistic fill
    realistic = simulate_realistic_fill(book, entry_price, direction, size_usd, "realistic")
    pessimistic = simulate_realistic_fill(book, entry_price, direction, size_usd, "pessimistic")

    result["realistic_entry"] = realistic["fill_price"]
    result["realistic_slippage_bps"] = realistic["slippage_bps"]
    result["pessimistic_entry"] = pessimistic["fill_price"]
    result["pessimistic_slippage_bps"] = pessimistic["slippage_bps"]
    result["top5_depth_usd"] = realistic["top5_depth_usd"]
    result["book_mid"] = book.mid_price
    result["error"] = realistic.get("error") or pessimistic.get("error")

    return result


# ── CLI test ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    coin = sys.argv[1] if len(sys.argv) > 1 else "BTC"

    print(f"=== L2 Book: {coin} ===\n")
    try:
        book = fetch_l2_book(coin)
        print(f"  Mid: ${book.mid_price:,.2f}")
        print(f"  Spread: ${book.asks[0][0] - book.bids[0][0]:.1f}" if book.bids and book.asks else "")
        print(f"  Bids: {len(book.bids)} levels, best: ${book.bids[0][0]:,.2f} ({book.bids[0][1]:,.0f} USD)")
        print(f"  Asks: {len(book.asks)} levels, best: ${book.asks[0][0]:,.2f} ({book.asks[0][1]:,.0f} USD)")
        print(f"  Top-5 bid depth: ${sum(sz for _, sz in book.bids[:5]):,.0f}")
        print(f"  Top-5 ask depth: ${sum(sz for _, sz in book.asks[:5]):,.0f}")

        # Test fills
        sizes = [100, 1000, 10000]
        for mode in ["realistic", "pessimistic"]:
            print(f"\n--- {mode.upper()} fills ---")
            for sz in sizes:
                # Test buy at mid
                r = simulate_realistic_fill(book, book.mid_price, "long", sz, mode)
                print(f"  Buy ${sz:,} @ mid: fill=${r['fill_price']:,.2f}, slip={r['slippage_bps']:.2f}bps, levels={r['levels_consumed']}")

    except Exception as e:
        print(f"ERROR: {e}")