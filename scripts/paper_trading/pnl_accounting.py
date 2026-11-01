#!/usr/bin/env python3
"""
pnl_accounting.py — shared PnL-accounting primitives for the hostile paper fill
models (swing, STR-Q).

Single source of truth for taker-fee application, R-multiple computation,
adversarial cost drag, paper-R fallback, and STR-Q signal-dedup / journal
reconciliation. The hostile_fills*.py files import from here (no local
duplicated definitions).

Consolidated from hostile_fills.py / hostile_fills_strq.py (US-164).
Behavior-preserving except the deliberate
DEGENERATE_RISK_FLOOR reconciliation (swing 0.5% -> 0.10%) flagged in the
round-4 architect spec §5.
"""

import math
import json
import pathlib
import sys

# trade_journal lives in the same directory; make it importable regardless of
# the caller's sys.path setup (no hard coupling to a hostile file's path init).
_THIS_DIR = pathlib.Path(__file__).resolve().parent
if str(_THIS_DIR) not in sys.path:
    sys.path.insert(0, str(_THIS_DIR))

import trade_journal  # noqa: E402  (for _authoritative_close)


# ── Constants (single source) ──────────────────────────────────────────────

# Degenerate-risk floor: risk_pct below this marks the stop distance as a
# near-zero-risk artifact (unscoreable). 0.10% — replaces the old split of
# swing=0.5% / strq=0.1% (round-4 reconciliation, spec §5).
DEGENERATE_RISK_FLOOR = 0.001     # 0.10%

# Default adversarial round-trip bps used when a caller does not pass an
# explicit fee value. US-164 placeholder only (matches the former 20 bps);
# US-165 call sites pass the dynamic fee_source value through.
DEFAULT_ROUND_TRIP_BPS = 20.0

# US-180: default stop-widening factor. Widening the stop lowers fee-per-R
# WITHOUT increasing notional risk (the dollar-risk cap lives in the sizer,
# outside this module). Sensitivity set for validation = {1.5, 2.0, 3.0}.
STOP_WIDEN_FACTOR = 2.0


# ── Core helpers ────────────────────────────────────────────────────────────

def _apply_taker_fee(price: float, direction: str, is_entry: bool,
                     taker_bps: float) -> float:
    """Adverse per-leg taker fee. buy leg: price*(1+fee) (costs more to buy);
    sell leg: price*(1-fee) (nets less to sell). US-166 fix.
    side = 'buy' iff (direction == 'long') == is_entry  (entry<>exit flips the side).
    """
    side = "buy" if (direction == "long") == is_entry else "sell"
    fee_rate = taker_bps / 10_000
    if side == "buy":
        return round(price * (1 + fee_rate), 6)
    return round(price * (1 - fee_rate), 6)


def _worst_print(bar, direction: str) -> float:
    """Return worst bar print for the given direction (simulates stop slippage).

    For a long (stop = sell): worst = low of bar.
    For a short (stop = buy to cover): worst = high of bar.
    """
    if direction == "long":
        return float(bar["low"])
    return float(bar["high"])


def _trades_through(bar, level: float, side: str) -> bool:
    """Check if bar trades THROUGH a level (not just touches).

    For a buy limit (long entry / short target): bar's low must be strictly below level.
    For a sell limit (short entry / long target): bar's high must be strictly above level.
    """
    if side == "buy":
        return float(bar["low"]) < level
    return float(bar["high"]) > level


def _bar_touches(bar, level: float) -> bool:
    """Check if bar's range touches a level (used for stop triggers)."""
    return float(bar["low"]) <= level <= float(bar["high"])


def _compute_r(paper_entry: float, paper_stop: float, direction: str,
               hostile_entry_price: float, exit_price: float) -> float:
    """R = direction_pnl(hostile_entry, hostile_exit) / setup_risk(paper).

    Entry slippage (already fee'd hostile fill vs paper close) is charged in the
    numerator only. Risk is fixed by the trade setup: |paper_entry - paper_stop|,
    never the slipped entry.
    """
    risk = abs(paper_entry - paper_stop)
    if risk <= 0:
        return 0.0
    if direction == "long":
        return (exit_price - hostile_entry_price) / risk
    else:
        return (hostile_entry_price - exit_price) / risk


def widen_stop(entry: float, stop: float, direction: str, factor: float) -> float:
    """Widen the stop distance by `factor` (>= 1.0) away from entry (US-180).

    long  -> entry - |entry - stop| * factor   (lower the stop)
    short -> entry + |entry - stop| * factor   (raise the stop)
    Never shrinks a stop. Guard: entry<=0 or stop<=0 or factor<1.0 or unknown
    direction -> return `stop` unchanged.
    """
    if entry <= 0 or stop <= 0 or factor < 1.0:
        return stop
    distance = abs(entry - stop) * factor
    if direction == "long":
        return entry - distance
    if direction == "short":
        return entry + distance
    return stop


def _adversarial_cost_drag(entry_price: float, stop_price: float,
                           round_trip_bps: float | None = None) -> float:
    """Cost drag (R units) for the adversarial taker round trip.

    cost_drag_R = round_trip_bps / 10000 / risk_pct.
    Returns float('inf') for a degenerate stop (risk_pct < DEGENERATE_RISK_FLOOR)
    so the caller treats the trade as unscoreable.
    `round_trip_bps` None -> DEFAULT_ROUND_TRIP_BPS.
    """
    # Self-guard: non-positive prices cannot produce a meaningful risk distance.
    # Return +inf (unscoreable) instead of risking ZeroDivisionError / negative
    # risk. Consistent with the existing degenerate-stop sentinel and the
    # callers' math.isfinite(...) guards in _paper_r. (US-167)
    if entry_price <= 0 or stop_price <= 0:
        return float("inf")

    if round_trip_bps is None:
        round_trip_bps = DEFAULT_ROUND_TRIP_BPS
    risk_pct = abs(entry_price - stop_price) / entry_price
    if risk_pct < DEGENERATE_RISK_FLOOR:
        return float("inf")
    return (round_trip_bps / 10000.0) / risk_pct


def _paper_r(trade: dict, round_trip_bps: float | None = None) -> tuple:
    """Return (value, costed) for the paper model's R-multiple.

    Prefer the cost-adjusted `gauntlet_r` when present and finite -> (value, True).

    Round 3 fixes:
      * time_zombie_cleanup (r=0) is a forced cleanup, not a real trade outcome
        -> excluded from the scored / win-rate populations as (None, False).
      * entry_price <= 0 or stop_price <= 0 is REJECTED (None, False) BEFORE any
        cost-drag computation — it must not fall through to a zero cost drag and
        return an uncosted R.
      * a closed trade whose gauntlet_r is missing is charged the adversarial
        taker round trip (round_trip_bps), not a trivially-favorable venue model.

    `round_trip_bps` None -> DEFAULT_ROUND_TRIP_BPS.
    """
    if round_trip_bps is None:
        round_trip_bps = DEFAULT_ROUND_TRIP_BPS

    if trade.get("exit_reason", "") == "time_zombie_cleanup":
        return (None, False)

    gauntlet = trade.get("gauntlet_r", "")
    if gauntlet not in ("", None):
        try:
            v = float(gauntlet)
            if math.isfinite(v):
                return (v, True)
        except (ValueError, TypeError):
            pass

    r_str = trade.get("r_multiple", "")
    if r_str in ("", None):
        return (None, False)
    try:
        gross = float(r_str)
    except (ValueError, TypeError):
        return (None, False)
    if not math.isfinite(gross):
        return (None, False)

    try:
        entry = float(trade.get("entry_price", 0))
        stop = float(trade.get("stop_price", 0))
    except (ValueError, TypeError):
        return (None, False)

    # Reject non-positive prices BEFORE cost-drag computation.
    if entry <= 0 or stop <= 0:
        return (None, False)

    cost_drag = _adversarial_cost_drag(entry, stop, round_trip_bps)
    if not math.isfinite(cost_drag):
        return (None, False)  # degenerate stop — genuinely unscoreable
    adversarial_r = gross - cost_drag
    if not math.isfinite(adversarial_r):
        return (None, False)
    return (round(adversarial_r, 6), True)


# ── Signal dedup with journal reconciliation (STR-Q pair) ───────────────────

def _authoritative_close() -> dict:
    """Return {signal_id: (exit_reason, r_multiple_float)} from the journal.

    The append-only journal (US-123) is the source of truth; trades.csv is a
    derived projection. Every signal_id has at most one 'close' event (duplicate
    close is refused by the journal), so a journal close is the single
    authoritative outcome used to reconcile divergent CSV close rows.
    """
    closes = {}
    if not trade_journal.JOURNAL_PATH.exists():
        return closes
    with open(trade_journal.JOURNAL_PATH, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                ev = json.loads(line)
            except json.JSONDecodeError:
                continue
            if ev.get("type") != "close":
                continue
            sig = ev.get("signal_id", "")
            if not sig:
                continue
            data = ev.get("data", {})
            try:
                rm = float(data.get("r_multiple", 0.0))
            except (ValueError, TypeError):
                rm = 0.0
            closes[sig] = (data.get("exit_reason", ""), rm)
    return closes


def _close_outcome(row: dict) -> tuple:
    """Close-outcome signature of a closed CSV row: (exit_reason, rounded r_multiple).

    Two rows agree iff this signature is identical — float noise in exit_price /
    gauntlet_r is ignored, but a real divergence (target vs stop, or conflicting
    r_multiple) is caught.
    """
    try:
        rm = round(float(row.get("r_multiple", "")), 3)
    except (ValueError, TypeError):
        rm = None
    return (row.get("exit_reason", ""), rm)


def _reconcile_signal_dedup(strq_trades: list) -> tuple:
    """Dedup STR-Q input on signal_id, validating every closed signal_id against
    the journal's authoritative close.

    Round 3: EVERY closed signal_id is validated — not just multi-row divergent
    groups. A closed signal_id is kept only when its CSV close outcome EXACTLY
    matches the journal close (exit_reason AND r_multiple), and the first
    matching row is kept (duplicate rows share the same outcome). Any divergence
    (reason mismatch, r_multiple mismatch) or a missing journal close is
    QUARANTINED — never silently arbitrated by row order or by a reason-only
    fallback.

    Returns (deduped_list, quarantined_count, quarantine_lines).
    """
    groups = {}
    order = []
    for r in strq_trades:
        sid = r.get("signal_id", "")
        if sid not in groups:
            groups[sid] = []
            order.append(sid)
        groups[sid].append(r)

    closes = _authoritative_close()

    out = []
    quarantined = 0
    quarantine_lines = []
    for sid in order:
        rows = groups[sid]
        closed_rows = [r for r in rows if r.get("status") == "closed"]
        if not closed_rows:
            # Nothing closed for this signal_id — nothing to reconcile.
            out.append(rows[0])
            continue

        auth = closes.get(sid)
        if auth is None:
            quarantined += 1
            outcomes = sorted(map(str, {_close_outcome(r) for r in closed_rows}))
            quarantine_lines.append(
                f"{sid}: no journal close; {len(closed_rows)} closed CSV row(s) {outcomes}")
            continue
        a_reason, a_rm = auth

        # Exact match only: same exit_reason AND same r_multiple (3 dp). Any
        # reason-match ambiguity or r_multiple divergence -> quarantine.
        exact = [r for r in closed_rows
                 if _close_outcome(r) == (a_reason, round(a_rm, 3))]
        if not exact:
            quarantined += 1
            outcomes = sorted(map(str, {_close_outcome(r) for r in closed_rows}))
            quarantine_lines.append(
                f"{sid}: journal says ({a_reason},{a_rm}) unmatched by CSV {outcomes}")
            continue
        out.append(exact[0])

    return out, quarantined, quarantine_lines