#!/usr/bin/env python3
"""
cost_adjuster.py — Gauntlet G3 cost adjustment utility.

Applies venue-correct cost drag to trade R-multiples.
Importable by pipeline modules (capture_signals, portfolio_publish, alert_publisher,
trade_monitor, performance_report).

Usage:
    from cost_adjuster import adjust_trade, VENUE_COSTS, compute_cost_drag

    result = adjust_trade(entry_price, stop_price, exit_price, direction, asset_class)
    # result['gauntlet_r'] is the cost-adjusted R-multiple
"""

from dataclasses import dataclass
from typing import Optional, Dict

# ── Venue cost models (PROP-001, validated via G0/G3) ──────────────────────

VENUE_COSTS: Dict[str, float] = {
    "stock": 2.0,    # zero commission + spread/slippage, no funding
    "crypto": 12.0,  # 9.0 taker fees (4.5+4.5) + 2.5 slippage + 0.5 funding
}

DEFAULT_COST = 12.0  # conservative: assume crypto perps if asset_class unknown


# ── Risk controls ────────────────────────────────────────────────────
MIN_RISK_PCT = 0.005          # 0.5% — trades with tighter stops are noise
MAX_R_MULTIPLE = 50.0         # cap outlier r_multiples from near-zero risk


def compute_cost_drag(entry_price: float, stop_price: float,
                      asset_class: Optional[str] = None) -> float:
    """
    Compute cost drag in R units for one round trip.

    cost_drag_R = venue_cost_bps / 10000 / risk_pct
    where risk_pct = |entry - stop| / entry

    Returns cost drag as a positive number (subtract from gross R).
    Returns float('inf') when risk_pct is below MIN_RISK_PCT — the trade
    is too noisy to cost-adjust meaningfully (degenerate stop distance).
    """
    if entry_price <= 0 or stop_price <= 0:
        return 0.0

    risk_pct = abs(entry_price - stop_price) / entry_price
    if risk_pct < MIN_RISK_PCT:
        return float('inf')

    venue_cost_bps = VENUE_COSTS.get(asset_class or "", DEFAULT_COST)
    return (venue_cost_bps / 10000.0) / risk_pct


@dataclass
class AdjustedTrade:
    """Result of applying G3 cost adjustment to a trade."""
    gross_r: float          # original r_multiple
    cost_drag_r: float      # R consumed by fees/slippage/funding
    gauntlet_r: float       # net R after costs
    risk_pct: float         # risk as fraction of price
    venue_cost_bps: float   # cost model used
    venue: str              # stock or crypto


def adjust_trade(entry_price: float, stop_price: float,
                 exit_price: Optional[float] = None,
                 direction: str = "long",
                 asset_class: Optional[str] = None,
                 gross_r: Optional[float] = None) -> AdjustedTrade:
    """
    Full G3 cost adjustment for a single trade.

    If gross_r is provided, uses it directly. Otherwise computes from prices.

    Args:
        entry_price: trade entry price
        stop_price: stop-loss price
        exit_price: trade exit price (optional if gross_r provided)
        direction: 'long'/'short' or 'bullish'/'bearish'
        asset_class: 'stock' or 'crypto'
        gross_r: pre-computed r_multiple (optional)

    Returns AdjustedTrade with gauntlet_r = gross_r - cost_drag_r.
    """
    venue = asset_class if asset_class in VENUE_COSTS else "crypto"
    venue_cost_bps = VENUE_COSTS.get(venue, DEFAULT_COST)

    risk_pct = abs(entry_price - stop_price) / entry_price if entry_price > 0 else 0
    cost_drag_r = compute_cost_drag(entry_price, stop_price, asset_class)

    if gross_r is not None:
        gr = gross_r
    elif exit_price is not None and entry_price > 0:
        if direction.lower() in ("long", "bullish"):
            gross_bps = (exit_price - entry_price) / entry_price * 10000
        else:
            gross_bps = (entry_price - exit_price) / entry_price * 10000
        gr = gross_bps / 10000 / risk_pct if risk_pct > 0 else 0
    else:
        gr = 0.0

    # Cap degenerate r_multiples from near-zero risk trades
    if abs(gr) > MAX_R_MULTIPLE:
        gr = MAX_R_MULTIPLE if gr > 0 else -MAX_R_MULTIPLE

    return AdjustedTrade(
        gross_r=gr,
        cost_drag_r=cost_drag_r,
        gauntlet_r=gr - cost_drag_r,
        risk_pct=risk_pct,
        venue_cost_bps=venue_cost_bps,
        venue=venue,
    )


def batch_adjust(trades: list) -> list:
    """
    Apply G3 adjustment to a list of trade dicts (from CSV or signal pipeline).

    Each trade dict should have: entry_price, stop_price, exit_price,
    direction, asset_class, r_multiple.

    Adds 'gauntlet_r' and 'cost_drag_r' fields to each dict.
    Returns the mutated list.
    """
    for t in trades:
        try:
            entry = float(t.get("entry_price", 0))
            stop = float(t.get("stop_price", 0))
            exit_p = float(t.get("exit_price", 0))
        except (ValueError, TypeError):
            t["gauntlet_r"] = t.get("r_multiple", 0)
            t["cost_drag_r"] = 0.0
            continue

        result = adjust_trade(
            entry_price=entry,
            stop_price=stop,
            exit_price=exit_p,
            direction=t.get("direction", "long"),
            asset_class=t.get("asset_class", "crypto"),
            gross_r=float(t.get("r_multiple", 0)) if t.get("r_multiple") else None,
        )
        t["gauntlet_r"] = result.gauntlet_r
        t["cost_drag_r"] = result.cost_drag_r

    return trades


def compute_gauntlet_stats(trades: list) -> dict:
    """
    Compute aggregate G3-adjusted statistics from a list of trades.

    Returns dict with lifetime and trailing stats.
    """
    if not trades:
        return {"trades": 0, "error": "no trades"}

    grs = []
    gross_rs = []
    for t in trades:
        val = t.get("gauntlet_r", None)
        if val is None or val == "" or val == '':
            val = t.get("r_multiple", 0)
        try:
            grs.append(float(val))
        except (ValueError, TypeError):
            grs.append(0.0)
        try:
            gross_rs.append(float(t.get("r_multiple", 0) or 0))
        except (ValueError, TypeError):
            gross_rs.append(0.0)

    # Lifetime
    total_r = sum(grs)
    avg_r = total_r / len(grs) if grs else 0
    wins = sum(1 for r in grs if r > 0)
    losses = sum(1 for r in grs if r < 0)
    win_rate = wins / len(grs) if grs else 0

    pos = sum(r for r in grs if r > 0)
    neg = abs(sum(r for r in grs if r < 0)) or 1e-9
    pf = pos / neg

    gross_total = sum(gross_rs)
    gross_avg = gross_total / len(gross_rs) if gross_rs else 0
    cost_drag = gross_avg - avg_r

    # Past 7 days
    from datetime import datetime, timedelta, timezone
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=7)

    recent = []
    for t in trades:
        exit_str = t.get("exit_date", "")
        if not exit_str:
            # Use entry_date if no exit
            exit_str = t.get("entry_date", "")
        try:
            # Try common formats
            for fmt in ["%Y-%m-%d %H:%M:%S%z", "%Y-%m-%d %H:%M:%S+00:00",
                        "%Y-%m-%d", "%Y-%m-%dT%H:%M:%S"]:
                try:
                    dt = datetime.strptime(exit_str, fmt)
                    if not dt.tzinfo:
                        dt = dt.replace(tzinfo=timezone.utc)
                    if dt > cutoff:
                        recent.append(t)
                    break
                except ValueError:
                    continue
        except Exception:
            pass

    recent_grs = []
    for t in recent:
        val = t.get("gauntlet_r", None)
        if val is None or val == "" or val == '':
            val = t.get("r_multiple", 0)
        try:
            recent_grs.append(float(val))
        except (ValueError, TypeError):
            recent_grs.append(0.0)
    recent_total = sum(recent_grs)
    recent_avg = recent_total / len(recent_grs) if recent_grs else 0
    recent_wins = sum(1 for r in recent_grs if r > 0)

    return {
        "trades": len(trades),
        "total_r": total_r,
        "avg_r": avg_r,
        "win_rate": win_rate,
        "profit_factor": pf,
        "cost_drag_per_trade": cost_drag,
        "gross_avg_r": gross_avg,
        "past_7d": {
            "trades": len(recent),
            "total_r": recent_total,
            "avg_r": recent_avg,
            "win_rate": recent_wins / len(recent) if recent else 0,
        },
    }


# ── CLI: standalone recalculation ──────────────────────────────────────────

if __name__ == "__main__":
    import sys, csv, os

    trades_path = sys.argv[1] if len(sys.argv) > 1 else \
        "/root/HermesForge/scripts/paper_trading/trades.csv"

    if not os.path.exists(trades_path):
        print(f"ERROR: {trades_path} not found")
        sys.exit(1)

    with open(trades_path) as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    batch_adjust(rows)
    stats = compute_gauntlet_stats(rows)

    print("=" * 60)
    print("GAUNTLET G3 RECALCULATION")
    print("=" * 60)
    print(f"Trades: {stats['trades']}")
    print(f"\nLifetime:")
    print(f"  Gross avg R:  {stats['gross_avg_r']:+.4f}")
    print(f"  Cost drag:    {stats['cost_drag_per_trade']:.4f} R/trade")
    print(f"  Gauntlet R:   {stats['avg_r']:+.4f}")
    print(f"  Win rate:     {stats['win_rate']:.1%}")
    print(f"  Profit factor:{stats['profit_factor']:.2f}")
    print(f"\nPast 7 days ({stats['past_7d']['trades']} trades):")
    print(f"  Gauntlet R:   {stats['past_7d']['avg_r']:+.4f}")
    print(f"  Win rate:     {stats['past_7d']['win_rate']:.1%}")

    # Show asset-class breakdown
    from collections import defaultdict
    by_venue = defaultdict(list)
    for r in rows:
        venue = r.get("asset_class", "crypto")
        val = r.get("gauntlet_r", None)
        if val is None or val == "" or val == '':
            val = r.get("r_multiple", 0)
        try:
            by_venue[venue].append(float(val))
        except (ValueError, TypeError):
            by_venue[venue].append(0.0)

    print(f"\nBy venue:")
    for venue, vals in sorted(by_venue.items()):
        avg = sum(vals) / len(vals)
        print(f"  {venue}: {len(vals)} trades, avg gauntlet R = {avg:+.4f}")