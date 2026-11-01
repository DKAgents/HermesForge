#!/usr/bin/env python3
"""
g3_gate.py — mandatory G3 fill-realism promotion gate (US-174).

Makes "execution realism" a fail-closed pre-condition for promotion. A strategy
may NOT be promoted to LIVE/WATCH unless its out-of-sample edge survives
realistic/pessimistic fills:

    G3.1  n_trades >= 10
    G3.2  realistic mean R > 0          (strictly; == 0 also fails)
    G3.3  pessimistic profit factor > 1.0
    G3.4  realistic mean R >= 0.60 * optimistic mean R

All four must hold; any failure => REJECT. A rejected strategy is demoted to
Hypothesis ("no claimable edge under realistic fills") — never auto-KILLED, never
flag-only-warned.

Fill-model dispatch (asset_class + timeframe; one decision point so a call site
can never route a daily-bar stock trade through the L2 crypto simulator — which
would silently treat a missing L2 book as zero depth):

  * INTRADAY CRYPTO (5m/1h/6h perps) -> execution_sim.batch_simulate() over the
    trade's L2 snapshots with FillMode.REALISTIC / FillMode.PESSIMISTIC (the
    pre-existing G3 path; ``realistic`` reads batch_simulate(REALISTIC)[mean_net_r],
    ``pessimistic`` reads batch_simulate(PESSIMISTIC)[pf]).

  * EVERYTHING ELSE (daily-bar swing/pattern, stocks AND daily crypto) ->
    BAR-LEVEL hostile model: next-open entry (US-173) + fee_source round-trip
    (cost_adjuster.compute_cost_drag) for the realistic leg; the pessimistic leg
    adds an extra adverse exit leg (worst-print stop / missed trade-through
    target). The full worst-print / trade-through exit walk lives in
    hostile_fills.py; the closed-form extra-leg here is the conservative
    equivalent that does not require re-loading OHLC per trade.

This module is the ONLY sanctioned promotion entry point (promote_strategy). It
does not mutate strategy notes or the registry itself — the swarm/orchestrator
calls assert_g3_gate before recording any LIVE/WATCH status.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from cost_adjuster import compute_cost_drag
from fee_source import get_taker_bps

MIN_TRADES = 10
EDGE_DECAY_FLOOR = 0.60

_INTRADAY_CRYPTO_TIMEFRAMES = ("5m", "1h", "6h")


class FillRealismGateError(RuntimeError):
    """Raised by assert_g3_gate / promote_strategy when a strategy fails G3.

    Carries the strategy_id, the computed gate record, and the human-readable
    REJECT reason, so the promotion caller can demote to Hypothesis with a
    citable rationale ("no claimable edge under realistic fills").
    """

    def __init__(self, strategy_id: str, record: dict, reason: str):
        self.strategy_id = strategy_id
        self.record = record
        self.reason = reason
        super().__init__(f"[{strategy_id}] REJECT: {reason}")


def _is_intraday_crypto(asset_class: str, timeframe: str) -> bool:
    return asset_class == "crypto" and timeframe in _INTRADAY_CRYPTO_TIMEFRAMES


def _pf(rs: list[float]) -> float:
    gains = sum(r for r in rs if r > 0)
    losses = abs(sum(r for r in rs if r < 0))
    if losses > 0:
        return gains / losses
    return float("inf") if gains > 0 else 0.0


def _mean(rs: list[float]) -> float:
    return sum(rs) / len(rs) if rs else 0.0


def _bar_level_metrics(trades: list) -> dict:
    """Closed-form realistic/pessimistic R for the daily-bar hostile model.

    optimistic_r  = the frictionless gross R the scanner emitted (r_multiple).
                    (Post-US-173, entry is already next-open, so the next-open
                    adverse selection is already priced into r_multiple.)
    realistic_r   = optimistic_r - fee round-trip (compute_cost_drag) - any
                    residual next-open drift (entry_drift_r, e.g. from the
                    legacy-CSV shim).
    pessimistic_r = realistic_r - one extra adverse exit leg (taker), the
                    conservative closed-form stand-in for worst-print stop
                    fills / missed trade-through targets (hostile_fills' model).
    """
    opt_rs, real_rs, pess_rs = [], [], []
    for t in trades:
        try:
            entry = float(t.get("entry_price", 0))
            stop = float(t.get("stop_price", 0))
        except (ValueError, TypeError):
            continue
        try:
            r = float(t.get("r_multiple", 0))
        except (ValueError, TypeError):
            r = 0.0

        asset_class = t.get("asset_class", "stock")
        opt_rs.append(r)

        drag = compute_cost_drag(entry, stop, asset_class)
        if not math.isfinite(drag):
            drag = 0.0  # degenerate stop -> cannot cost-adjust; treat as 0 drag
        try:
            drift = float(t.get("entry_drift_r", 0.0) or 0.0)
        except (ValueError, TypeError):
            drift = 0.0

        realistic = r - drag - drift
        real_rs.append(realistic)

        # One extra adverse exit leg (worst print / trade-through miss).
        if entry > 0 and stop > 0:
            risk_pct = abs(entry - stop) / entry
            extra_r = (get_taker_bps(asset_class) / 10000.0) / risk_pct if risk_pct >= 1e-9 else 0.0
        else:
            extra_r = 0.0
        pess_rs.append(realistic - extra_r)

    return {
        "n": len(opt_rs),
        "optimistic_mean_r": _mean(opt_rs),
        "realistic_mean_r": _mean(real_rs),
        "pessimistic_pf": _pf(pess_rs),
    }


def _intraday_crypto_metrics(trades: list) -> dict:
    """execution_sim L2 replay for intraday crypto (the pre-existing G3 path)."""
    import execution_sim as es

    # batch_simulate needs l2_snapshots etc per trade; drop trades missing them
    # rather than treating a missing L2 book as zero depth (which is wrong).
    usable = [t for t in trades if t.get("l2_snapshots")]
    if not usable:
        return {
            "n": len(trades),
            "optimistic_mean_r": 0.0,
            "realistic_mean_r": 0.0,
            "pessimistic_pf": 0.0,
        }

    opt = es.batch_simulate(usable, es.FillMode.OPTIMISTIC)
    real = es.batch_simulate(usable, es.FillMode.REALISTIC)
    pess = es.batch_simulate(usable, es.FillMode.PESSIMISTIC)

    return {
        "n": len(usable),
        "optimistic_mean_r": float(opt.get("mean_net_r", 0.0)),
        "realistic_mean_r": float(real.get("mean_net_r", 0.0)),
        "pessimistic_pf": float(pess.get("pf", 0.0)),
    }


def evaluate_fill_realism(strategy_id: str, trades: list,
                          asset_class: str, timeframe: str) -> dict:
    """Compute the G3 gate record for a strategy's trade set.

    Returns a dict:
        n, optimistic_mean_r, realistic_mean_r, pessimistic_pf,
        edge_decay_ratio, passed, reasons.
    """
    if _is_intraday_crypto(asset_class, timeframe):
        m = _intraday_crypto_metrics(trades)
    else:
        m = _bar_level_metrics(trades)

    n = m["n"]
    opt = m["optimistic_mean_r"]
    real = m["realistic_mean_r"]
    pess_pf = m["pessimistic_pf"]
    decay = (real / opt) if opt > 0 else float("inf")

    reasons = []
    if n < MIN_TRADES:
        reasons.append(f"INSUFFICIENT DATA: n={n} < {MIN_TRADES}")
    if real <= 0:
        reasons.append(f"realistic mean R = {real:.4f} <= 0")
    if pess_pf <= 1.0:
        reasons.append(f"pessimistic PF = {pess_pf:.4f} <= 1.0")
    if opt > 0 and real < EDGE_DECAY_FLOOR * opt:
        reasons.append(
            f"edge decay: realistic {real:.4f} < {EDGE_DECAY_FLOOR}*optimistic "
            f"{opt:.4f}"
        )

    passed = len(reasons) == 0

    return {
        "strategy_id": strategy_id,
        "n": n,
        "optimistic_mean_r": round(opt, 4),
        "realistic_mean_r": round(real, 4),
        "pessimistic_pf": round(pess_pf, 4),
        "edge_decay_ratio": round(decay, 4) if math.isfinite(decay) else None,
        "passed": passed,
        "reasons": reasons,
    }


def assert_g3_gate(strategy_id: str, trades: list,
                   asset_class: str, timeframe: str) -> dict:
    """Fail-closed: raise FillRealismGateError if G3 does not pass.

    On failure the recorded reason matches the story's wording: a non-positive
    realistic edge is "no claimable edge under realistic fills".
    """
    record = evaluate_fill_realism(strategy_id, trades, asset_class, timeframe)
    if not record["passed"]:
        reason = (
            f"NO CLAIMABLE EDGE UNDER REALISTIC FILLS: "
            f"realistic mean R = {record['realistic_mean_r']:.4f} "
            f"(pessimistic PF = {record['pessimistic_pf']:.4f}) — "
            + "; ".join(record["reasons"])
        )
        raise FillRealismGateError(strategy_id, record, reason)
    return record


def promote_strategy(strategy_id: str, *, trades, asset_class, timeframe) -> dict:
    """THE ONLY sanctioned promotion entry point.

    Calls assert_g3_gate() FIRST. On pass, returns the gate record (which the
    swarm then writes into the strategy note + registry as the LIVE/WATCH
    evidence). On fail, performs NO mutation and raises FillRealismGateError.
    """
    record = assert_g3_gate(strategy_id, trades, asset_class, timeframe)
    return {
        "strategy_id": strategy_id,
        "promoted": True,
        "g3_realistic_mean_r": record["realistic_mean_r"],
        "g3_pessimistic_pf": record["pessimistic_pf"],
        "g3_edge_decay_ratio": record["edge_decay_ratio"],
        "g3_passed": True,
    }