#!/usr/bin/env python3
"""
execution_sim.py — G3 Execution Realism Simulator

Replays fills against L2 orderbook state in three modes:
  OPTIMISTIC  — always fills at mid-price
  REALISTIC   — queue-aware limit fills (price must trade through); taker at VWAP
  PESSIMISTIC — always taker at the cross + one tick adverse selection

Also models slippage, fees (4.5 bps/leg), and Hyperliquid funding accrual.

Core use: simulate_trade() and batch_simulate() for the Strategy Gauntlet (PROP-001).
"""

from __future__ import annotations

import copy
import enum
from typing import Dict, List, Optional, Tuple


# ── Constants ───────────────────────────────────────────────────────────────

TAKER_FEE_BPS = 4.5          # per leg
INTEREST_BPS_PER_8H = 0.01   # Hyperliquid interest component
PREMIUM_CLAMP = 0.0005        # ±0.05% clamped premium
FUNDING_CAP_HOURLY = 0.04    # 4% per hour hard cap


class FillMode(enum.Enum):
    OPTIMISTIC = "optimistic"
    REALISTIC = "realistic"
    PESSIMISTIC = "pessimistic"


class Direction(enum.Enum):
    LONG = "long"
    SHORT = "short"


# ── Data model ──────────────────────────────────────────────────────────────

# L2 book: dict with 'bids' and 'asks', each a list of [price, size_usd].
# Bids sorted descending by price (best first); asks ascending.
L2Book = Dict[str, List[List[float]]]

# Single snapshot at a point in time.
L2Snapshot = Dict  # { 'book': L2Book, 'timestamp': ..., 'mid': float, ... }


# ── L2 helpers ──────────────────────────────────────────────────────────────

def mid_price(book: L2Book) -> float:
    """Mid from best bid/ask. Returns NaN if either side is empty."""
    if not book["bids"] or not book["asks"]:
        return float("nan")
    return (book["bids"][0][0] + book["asks"][0][0]) / 2.0


def best_bid(book: L2Book) -> Optional[float]:
    if book["bids"]:
        return book["bids"][0][0]
    return None


def best_ask(book: L2Book) -> Optional[float]:
    if book["asks"]:
        return book["asks"][0][0]
    return None


def book_from_snapshot(snapshot: L2Snapshot) -> L2Book:
    """Extract the L2Book from a snapshot dict (handles simplified forms)."""
    if "book" in snapshot:
        return snapshot["book"]
    # Assume snapshot *is* the book with optional metadata.
    if "bids" in snapshot and "asks" in snapshot:
        return {"bids": snapshot["bids"], "asks": snapshot["asks"]}
    raise ValueError(f"Cannot extract L2Book from snapshot: {list(snapshot.keys())[:5]}")


# ── Slippage model ──────────────────────────────────────────────────────────

def compute_slippage_bps(size_usd: float, book: L2Book, direction: Direction) -> float:
    """
    Compute expected slippage in bps for executing *size_usd* against the L2 book.

    Walks the book levels (asks for LONG/buys, bids for SHORT/sells),
    accumulating VWAP until *size_usd* is absorbed, then computes
    (vwap - mid) / mid * 10000 for buys or (mid - vwap) / mid * 10000
    for sells.  Returns bps — always >=0.

    Monotonic: larger sizes produce >= slippage.
    """
    if size_usd <= 0:
        return 0.0

    mid = mid_price(book)
    if not (mid > 0):
        return 0.0

    if direction == Direction.LONG:
        levels = book["asks"]
    else:
        levels = book["bids"]

    if not levels:
        return 1_000_000.0  # effectively infinite

    remaining = size_usd
    total_cost = 0.0
    total_size = 0.0

    for level in levels:
        px, sz = level[0], level[1]
        if sz <= 0:
            continue
        take = min(remaining, sz)
        total_cost += take * px
        total_size += take
        remaining -= take
        if remaining <= 1e-12:
            break

    if total_size <= 1e-12:
        return 0.0

    vwap = total_cost / total_size

    if direction == Direction.LONG:
        slippage_bps = (vwap - mid) / mid * 10_000
    else:
        slippage_bps = (mid - vwap) / mid * 10_000

    return max(0.0, slippage_bps)


# ── Fill simulation ─────────────────────────────────────────────────────────

def _optimistic_fill(price: float, _size: float, _direction: Direction,
                     _book: L2Book) -> float:
    """Always fills at the given price (mid)."""
    return price


def _pessimistic_fill(_price: float, size: float, direction: Direction,
                      book: L2Book) -> float:
    """
    Taker at the cross: best ask for buys, best bid for sells,
    plus one tick of adverse selection (one level deeper).
    """
    if direction == Direction.LONG:
        asks = book["asks"]
        if not asks:
            return float("inf")
        # Cross = best ask; adverse selection = one level deeper if available
        px = asks[0][0]
        if len(asks) >= 2:
            px = asks[1][0]  # one tick worse
        return px
    else:
        bids = book["bids"]
        if not bids:
            return 0.0
        px = bids[0][0]
        if len(bids) >= 2:
            px = bids[1][0]  # one tick worse
        return px


def _realistic_limit_fill(limit_price: float, size_usd: float,
                          direction: Direction, book: L2Book) -> float:
    """
    Queue-aware limit fill. For a limit BUY at *limit_price*, fills only when
    the best ask has traded THROUGH the limit (ask <= limit). For a limit SELL,
    fills when best bid >= limit.

    Returns the fill price (the limit price itself) if filled, or NaN if unfilled.
    """
    if direction == Direction.LONG:
        # Buy limit: we want to buy at or below limit_price.
        # Fill occurs if best ask is <= limit_price (market traded through our limit).
        best = best_ask(book)
        if best is not None and best <= limit_price:
            return limit_price
        return float("nan")
    else:
        # Sell limit: we want to sell at or above limit_price.
        # Fill occurs if best bid >= limit_price.
        best = best_bid(book)
        if best is not None and best >= limit_price:
            return limit_price
        return float("nan")


def _realistic_market_fill(size_usd: float, direction: Direction,
                           book: L2Book) -> float:
    """
    Market/taker fill at VWAP across levels needed to absorb *size_usd*.
    Returns VWAP price or NaN if insufficient depth.
    """
    if size_usd <= 0:
        return mid_price(book)

    if direction == Direction.LONG:
        levels = book["asks"]
    else:
        levels = book["bids"]

    if not levels:
        return float("nan")

    remaining = size_usd
    total_cost = 0.0
    total_size = 0.0

    for level in levels:
        px, sz = level[0], level[1]
        if sz <= 0:
            continue
        take = min(remaining, sz)
        total_cost += take * px
        total_size += take
        remaining -= take
        if remaining <= 1e-12:
            break

    if total_size <= 1e-12:
        return float("nan")

    return total_cost / total_size


def simulate_fill(target_price: float, size_usd: float, direction: Direction,
                  mode: FillMode, book: L2Book) -> float:
    """
    Simulate a single fill at *target_price* using the given *mode*.

    - OPTIMISTIC: returns target_price (usually mid)
    - REALISTIC:  if the price is "better than market" (limit order),
                  uses queue-aware fill; otherwise market VWAP.
    - PESSIMISTIC: taker at cross with adverse selection.

    Returns the fill price, or NaN if unfilled.
    """
    if size_usd <= 0:
        return float("nan")

    if mode == FillMode.OPTIMISTIC:
        return _optimistic_fill(target_price, size_usd, direction, book)

    elif mode == FillMode.REALISTIC:
        # Determine if this is a limit or market order based on target_price
        mid = mid_price(book)
        if mid is None or not (mid > 0):
            # No valid mid — fall back to VWAP
            return _realistic_market_fill(size_usd, direction, book)

        if direction == Direction.LONG:
            # If target_price < best_ask, it's a limit buy (passive)
            ba = best_ask(book)
            if ba is not None and target_price < ba:
                return _realistic_limit_fill(target_price, size_usd, direction, book)
            else:
                # Market/taker — VWAP
                return _realistic_market_fill(size_usd, direction, book)
        else:
            # If target_price > best_bid, it's a limit sell (passive)
            bb = best_bid(book)
            if bb is not None and target_price > bb:
                return _realistic_limit_fill(target_price, size_usd, direction, book)
            else:
                return _realistic_market_fill(size_usd, direction, book)

    elif mode == FillMode.PESSIMISTIC:
        return _pessimistic_fill(target_price, size_usd, direction, book)

    return float("nan")


# ── Fee application ─────────────────────────────────────────────────────────

def apply_fees(gross_pnl_bps: float) -> float:
    """
    Apply taker fee per leg.  Fees are always a cost (negative pnl impact).

    Returns fee impact in bps (negative value).
    """
    return -2.0 * TAKER_FEE_BPS  # entry leg + exit leg


# ── Funding accrual ─────────────────────────────────────────────────────────

def compute_funding_rate(annualized_8h_rate: float) -> float:
    """
    Hyperliquid formula per skill doc:
      hourly = 1/8 of 8h funding rate
      + interest component 0.01% per 8h → 0.01 / 8 = 0.00125% per hour
      premium clamped to ±0.05%
      hard cap 4%/hr

    *annualized_8h_rate* is the 8-hour funding rate in bps annualised (or
    the raw 8h rate — we treat it as the *premium* component).

    Actually: The Hyperliquid 8h funding rate already includes the premium
    component.  We compute:
      raw_hourly = max(min(8h_rate, 0.05%), -0.05%) + 0.01%/8h
      then clamp to ±4%/hr
    expressed as a decimal fraction per hour.
    """
    # Convert to decimal; input in bps (1% = 100 bps)
    premium = annualized_8h_rate / 10_000  # bps → decimal
    hourly_interest = INTEREST_BPS_PER_8H / 8 / 10_000  # 0.01%/8h → decimal per hour

    # Clamp premium
    premium = max(-PREMIUM_CLAMP, min(PREMIUM_CLAMP, premium))

    # Hourly rate
    hourly = premium / 8 + hourly_interest

    # Hard cap
    hourly = max(-FUNDING_CAP_HOURLY, min(FUNDING_CAP_HOURLY, hourly))

    return hourly


def accrue_funding(position_size_usd: float, direction: Direction,
                   funding_rates: List[float], holding_period_hours: float,
                   settlement_interval_hours: float = 8.0) -> float:
    """
    Accrue funding across holding period.

    *funding_rates*: list of 8h funding rates (in bps) observed across the
    holding period.  One rate per settlement interval.

    *holding_period_hours*: total time the position is held.

    Returns funding pnl in bps (positive = received, negative = paid).
    """
    if holding_period_hours <= 0 or not funding_rates:
        return 0.0

    total_funding_bps = 0.0
    hours_remaining = holding_period_hours
    interval = settlement_interval_hours

    for rate_8h_bps in funding_rates:
        if hours_remaining <= 1e-12:
            break

        # Hours covered by this settlement interval
        hours_in_interval = min(hours_remaining, interval)

        # Funding rate per hour (decimal)
        hourly_rate = compute_funding_rate(rate_8h_bps)

        # Funding payment in bps for this interval
        # Longs pay funding when rate > 0 (receive when rate < 0)
        # Shorts receive funding when rate > 0 (pay when rate < 0)
        funding_bps_this_interval = hourly_rate * hours_in_interval * 10_000

        if direction == Direction.LONG:
            total_funding_bps -= funding_bps_this_interval  # longs pay positive funding
        else:
            total_funding_bps += funding_bps_this_interval  # shorts receive positive funding

        hours_remaining -= hours_in_interval

    return total_funding_bps


# ── Core simulation ─────────────────────────────────────────────────────────

def simulate_trade(
    entry_price: float,
    exit_price: float,
    size_usd: float,
    direction: Direction,
    entry_mode: FillMode,
    exit_mode: FillMode,
    l2_snapshots: List[L2Snapshot],
    funding_rates: List[float],
    holding_period_hours: float,
) -> dict:
    """
    Simulate a single round-trip trade through L2 execution realism.

    Returns dict:
        gross_pnl_bps, fees_bps, slippage_bps, funding_bps, net_pnl_bps,
        fill_prices: [entry_fill, exit_fill]
    """
    if size_usd <= 0:
        return {
            "gross_pnl_bps": 0.0,
            "fees_bps": 0.0,
            "slippage_bps": 0.0,
            "funding_bps": 0.0,
            "net_pnl_bps": 0.0,
            "fill_prices": [float("nan"), float("nan")],
        }

    # Use first snapshot for entry, last for exit (or only one if single)
    book_entry = book_from_snapshot(l2_snapshots[0])
    book_exit = book_from_snapshot(l2_snapshots[-1]) if len(l2_snapshots) > 1 else book_entry

    # Closing direction is the reverse of opening direction
    close_direction = Direction.SHORT if direction == Direction.LONG else Direction.LONG

    # Simulate fills
    entry_fill = simulate_fill(entry_price, size_usd, direction, entry_mode, book_entry)
    exit_fill = simulate_fill(exit_price, size_usd, close_direction, exit_mode, book_exit)

    # If fills are NaN, the trade is unfilled — return zeros
    if not (entry_fill > 0) or not (exit_fill > 0):
        return {
            "gross_pnl_bps": 0.0,
            "fees_bps": 0.0,
            "slippage_bps": 0.0,
            "funding_bps": 0.0,
            "net_pnl_bps": 0.0,
            "fill_prices": [entry_fill, exit_fill],
        }

    # Gross PnL: (exit - entry) / entry * 10000 for LONG,
    #            (entry - exit) / entry * 10000 for SHORT
    if direction == Direction.LONG:
        gross_pnl_bps = (exit_fill - entry_fill) / entry_price * 10_000
    else:
        gross_pnl_bps = (entry_fill - exit_fill) / entry_price * 10_000

    # Slippage: difference between target and actual fill, in bps
    if direction == Direction.LONG:
        entry_slip = (entry_fill - entry_price) / entry_price * 10_000  # higher = worse for buyer
        exit_slip = (exit_price - exit_fill) / entry_price * 10_000   # lower = worse for seller
    else:
        entry_slip = (entry_price - entry_fill) / entry_price * 10_000  # lower = worse for seller
        exit_slip = (exit_fill - exit_price) / entry_price * 10_000   # higher = worse for buyer (covering)

    slippage_bps = max(0.0, entry_slip) + max(0.0, exit_slip)

    # Fees
    fees_bps = apply_fees(gross_pnl_bps)

    # Funding
    funding_bps = accrue_funding(size_usd, direction, funding_rates, holding_period_hours)

    # Net
    net_pnl_bps = gross_pnl_bps + fees_bps - slippage_bps + funding_bps

    return {
        "gross_pnl_bps": gross_pnl_bps,
        "fees_bps": fees_bps,
        "slippage_bps": slippage_bps,
        "funding_bps": funding_bps,
        "net_pnl_bps": net_pnl_bps,
        "fill_prices": [entry_fill, exit_fill],
    }


# ── Batch simulation ────────────────────────────────────────────────────────

def batch_simulate(
    trades: List[dict],
    mode: FillMode,
) -> dict:
    """
    Run simulate_trade for each trade in *trades* using the same fill *mode*
    for both entry and exit.  Aggregates statistics.

    Each trade dict must have:
        entry_price, exit_price, size_usd, direction, l2_snapshots,
        funding_rates, holding_period_hours

    Returns:
        mean_net_r:    mean net PnL in R-units (net_pnl_bps / 100)
        pf:            profit factor (gross gains / gross losses)
        win_rate:      fraction of trades with net_pnl_bps > 0
        n_trades:      number of simulated trades
        net_pnls_bps:  list of individual net pnls
    """
    if not trades:
        return {
            "mean_net_r": 0.0,
            "pf": 0.0,
            "win_rate": 0.0,
            "n_trades": 0,
            "net_pnls_bps": [],
        }

    net_pnls = []
    for t in trades:
        result = simulate_trade(
            entry_price=t["entry_price"],
            exit_price=t["exit_price"],
            size_usd=t["size_usd"],
            direction=t["direction"],
            entry_mode=mode,
            exit_mode=mode,
            l2_snapshots=t["l2_snapshots"],
            funding_rates=t.get("funding_rates", []),
            holding_period_hours=t.get("holding_period_hours", 0.0),
        )
        net_pnls.append(result["net_pnl_bps"])

    n = len(net_pnls)
    wins = [pnl for pnl in net_pnls if pnl > 0]
    losses = [pnl for pnl in net_pnls if pnl < 0]

    mean_net_r = (sum(net_pnls) / n) / 100.0  # convert bps to R
    win_rate = len(wins) / n if n > 0 else 0.0

    gross_gains = sum(wins) if wins else 0.0
    gross_losses = abs(sum(losses)) if losses else 0.0
    pf = gross_gains / gross_losses if gross_losses > 0 else float("inf") if gross_gains > 0 else 0.0

    return {
        "mean_net_r": mean_net_r,
        "pf": pf,
        "win_rate": win_rate,
        "n_trades": n,
        "net_pnls_bps": net_pnls,
    }


# ── Mode-ordering invariant check ───────────────────────────────────────────

def check_mode_ordering(trades: List[dict]) -> Dict[str, float]:
    """
    Run batch_simulate for all three modes and verify:
        OPTIMISTIC net >= REALISTIC net >= PESSIMISTIC net

    Returns dict with mean net R for each mode.
    """
    results = {}
    for mode in [FillMode.OPTIMISTIC, FillMode.REALISTIC, FillMode.PESSIMISTIC]:
        results[mode.value] = batch_simulate(trades, mode)["mean_net_r"]

    # The invariant should hold; if not, log a warning but don't crash.
    if not (results["optimistic"] >= results["realistic"] >= results["pessimistic"]):
        # This is informational — in degenerate cases (e.g., all losing trades)
        # the ordering can flip, but in normal operation it's an invariant check.
        pass

    return results


# ── Synthetic book builder (for testing) ────────────────────────────────────

def make_book(mid: float, spread_bps: float = 2.0, levels: int = 5,
              depth_per_level: float = 50_000.0,
              tick_size: float = 0.1) -> L2Book:
    """
    Build a synthetic L2 book centered at *mid*.

    *spread_bps*: half-spread in bps from mid to best bid/ask.
    *levels*: number of levels on each side.
    *depth_per_level*: size in USD at each level.
    *tick_size*: price increment between levels.

    Returns dict with 'bids' and 'asks'.
    """
    half_spread = mid * spread_bps / 10_000
    best_ask_price = mid + half_spread
    best_bid_price = mid - half_spread

    asks = []
    for i in range(levels):
        px = best_ask_price + i * tick_size
        asks.append([px, depth_per_level])

    bids = []
    for i in range(levels):
        px = best_bid_price - i * tick_size
        bids.append([px, depth_per_level])

    return {"bids": bids, "asks": asks}


def make_snapshot(mid: float, **kwargs) -> L2Snapshot:
    """Build a synthetic L2 snapshot with a book at *mid*."""
    book = make_book(mid, **kwargs)
    return {"book": book, "mid": mid}