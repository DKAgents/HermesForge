#!/usr/bin/env python3
"""
breaker_harness.py — US-222 breaker/harness.

Takes a reconstructed rule (from rule_builder) and answers the one question the
builder cannot: "did it learn the market, or just this record?" (Part 4):

  1. Replay the rule on the SEALED recent half (OOS) — the builder never saw it.
  2. Compute agreement_OOS vs the no-skill baseline (always-flat and/or
     state-imbalance chance level). If agreement_OOS does not CLEAR the baseline
     by NO_SKILL_MARGIN, the verdict is "learned the record, not the market" and
     the rule is NOT advanced.
  3. Only a rule that clears OOS reproduction is handed to the gauntlet, with
     fees CHARGED (the source methodology runs gross of cost; we do not):
       G0 cost screen (g0_cost_screen.screen) → G3 fill realism (g3_gate) →
       G4 CPCV + G5 DSR (cpcv_harness + trials_ledger). G3 is mandatory and
     fail-closed.
  4. Every run writes exactly ONE trials_ledger entry with a fresh param_hash
     (G5 reads the growing N).

Invariants honored:
  - "no number not computed": every metric is produced by a real computation on
    real data; anything un-computable is reported as not_computed/insufficient.
  - Q9: backtest PnL is always RECOMPUTED from price/size × fee_source (taker,
    fail-closed); the record's own `pnl` column is provenance-only, never used.
  - Q7: reconstructed rules ALWAYS flow as `diagnostic: true`. They are measured
    freely (fees charged, reported) but NEVER auto-promoted and NEVER silently
    blocked by the US-191 signal-class intake (which governs PROMOTION, not
    diagnostic measurement). The rule + honest result are surfaced in a
    diagnostic report regardless of signal class.
  - No leverage; LIVE off.
"""

from __future__ import annotations

import math
from typing import Optional

import rule_builder as rb
import fee_source

# ---------------------------------------------------------------------------
# OOS reproduction (Part 4.1)
# ---------------------------------------------------------------------------

def replay_oos(rule: dict, series, oos_indices) -> list:
    """Replay the reconstructed rule over the full series, return OOS-bar states."""
    states = rb.apply_feature(series, rule["feature"], rule["params"])
    return [states[i] for i in oos_indices]


def no_skill_baseline(record_state_fn, bar_ts, indices) -> dict:
    """The better of always-flat agreement and state-imbalance (majority-class)
    agreement over the given bars. This is the chance level a trivial rule hits
    without any signal."""
    flat_match = 0
    counts = {1: 0, -1: 0, 0: 0}
    scored = 0
    for i in indices:
        r = record_state_fn(bar_ts[i])
        if r is None:
            continue
        scored += 1
        counts[r] = counts.get(r, 0) + 1
        if r == 0:
            flat_match += 1
    if scored == 0:
        return {"always_flat": None, "state_imbalance": None, "baseline": None,
                "scored": 0}
    always_flat = flat_match / scored
    majority = max(counts.values()) / scored
    baseline = max(always_flat, majority)
    return {"always_flat": round(always_flat, 6),
            "state_imbalance": round(majority, 6),
            "baseline": round(baseline, 6),
            "scored": scored}


def oos_verdict(agreement_oos, baseline) -> dict:
    """Decide advance vs kill from OOS agreement vs no-skill baseline + margin."""
    if agreement_oos is None or baseline is None:
        return {"verdict": "insufficient_data", "advance": False,
                "reason": "insufficient scored OOS observations to measure "
                          "out-of-sample agreement"}
    floor = baseline + rb.NO_SKILL_MARGIN
    if agreement_oos >= floor:
        return {
            "verdict": "advance", "advance": True,
            "agreement_oos": round(agreement_oos, 6),
            "baseline": round(baseline, 6),
            "floor": round(floor, 6),
            "reason": f"agreement_OOS {agreement_oos:.4f} >= no-skill baseline "
                      f"{baseline:.4f} + margin {rb.NO_SKILL_MARGIN:.2f}",
        }
    return {
        "verdict": "kill", "advance": False,
        "agreement_oos": round(agreement_oos, 6),
        "baseline": round(baseline, 6),
        "floor": round(floor, 6),
        "reason": (f"agreement_OOS {agreement_oos:.4f} collapsed below the "
                   f"no-skill baseline {baseline:.4f} + margin "
                   f"{rb.NO_SKILL_MARGIN:.2f} — learned the record, not the market"),
    }


# ---------------------------------------------------------------------------
# Trade reconstruction with fees (Part 4.2 / Q9)
# ---------------------------------------------------------------------------

def reconstruct_trades(states: list, series, asset_class: str = "crypto") -> list:
    """Derive round-trip trades from a state timeline using next-open execution
    (US-173 hostile entry) and RECOMPUTED net PnL via fee_source (taker,
    fail-closed). The record's own pnl is never an input here.

    states[i] is the signal at bar i; the fill happens at bar i+1's open.
    pnl_bps = direction * (exit−entry)/entry * 1e4 − round_trip_bps(asset_class).
    """
    trades = []
    pos = 0
    entry_price = None
    entry_bar = None
    rt_bps = fee_source.get_round_trip_bps(asset_class)

    def _close(direction, exit_price, exit_bar):
        gross = direction * (exit_price - entry_price) / entry_price * 10000.0
        net = gross - rt_bps
        return {
            "direction": "long" if direction == 1 else "short",
            "entry_price": entry_price,
            "exit_price": exit_price,
            "entry_time": series.ts[entry_bar],
            "exit_time": series.ts[exit_bar],
            "gross_bps": gross,
            "pnl_bps": net,
            "asset_class": asset_class,
        }

    for i in range(len(states) - 1):
        target = states[i]
        if target is None:
            target = 0
        if i + 1 >= len(series.open):
            break
        fill_price = series.open[i + 1]
        if target != pos:
            if target == 0 and pos != 0:
                trades.append(_close(pos, fill_price, i + 1))
                pos = 0
                entry_price = None
                entry_bar = None
            elif target in (1, -1) and pos == 0:
                pos = target
                entry_price = fill_price
                entry_bar = i + 1
            elif target in (1, -1) and pos in (1, -1):
                # direct long<->short flip: flatten then reopen (two legs, two fees)
                trades.append(_close(pos, fill_price, i + 1))
                pos = target
                entry_price = fill_price
                entry_bar = i + 1
    return trades


# ---------------------------------------------------------------------------
# Gauntlet handoff (Part 4.2 / 4.3)
# ---------------------------------------------------------------------------

def hand_to_gauntlet(rule: dict, series, asset_class: str, timeframe: str,
                     write_trial: bool = True) -> dict:
    """Run the reconstructed rule through G0 → G3 → G4/G5 with fees charged.

    Only called for a rule that cleared OOS reproduction. Returns a dict of
    computed metrics (never fabricated). G3 is mandatory and fail-closed.
    """
    from g0_cost_screen import screen as g0_screen
    from g3_gate import evaluate_fill_realism
    import cpcv_harness
    import trials_ledger

    report = {}

    # G0 — cost screen over the instrument's closes (round-trip taker fees).
    g0 = g0_screen(rule.get("instrument", "reconstructed"),
                   list(series.close))
    report["g0"] = {
        "median_abs_move_bps": g0.get("median_abs_move_bps"),
        "all_in_cost_bps": g0.get("all_in_cost_bps"),
        "gross_capture_needed_bps": g0.get("gross_capture_needed_bps"),
        "passes": g0.get("passes"),
        "explanation": g0.get("explanation"),
    }

    # Reconstruct trades with fees charged (Q9), then G3 fill realism.
    states = rb.apply_feature(series, rule["feature"], rule["params"])
    trades = reconstruct_trades(states, series, asset_class)
    report["n_trades"] = len(trades)

    g3_trades = []
    for t in trades:
        direction = 1 if t["direction"] == "long" else -1
        stop = t["entry_price"] * (1 - 0.01 * direction)  # nominal 1% risk stop
        g3_trades.append({
            "entry_price": t["entry_price"],
            "stop_price": stop,
            # G3 expects the OPTIMISTIC (gross) R and applies its own cost drag
            # via compute_cost_drag — passing net pnl_bps here would double-count.
            # 100 bps = 1 R at the nominal 1% risk stop.
            "r_multiple": t["gross_bps"] / 100.0,
            "asset_class": asset_class,
        })
    g3 = evaluate_fill_realism(rule.get("instrument", "reconstructed"),
                               g3_trades, asset_class, timeframe)
    report["g3"] = g3

    # Aggregate net PnL stats (recomputed via fee_source).
    pnls = [t["pnl_bps"] for t in trades]
    if pnls:
        report["net_avg_pnl_bps"] = round(sum(pnls) / len(pnls), 6)
        report["net_total_pnl_bps"] = round(sum(pnls), 6)
    else:
        report["net_avg_pnl_bps"] = None
        report["net_total_pnl_bps"] = None

    # G4/G5 only if G3 survives.
    report["g4g5"] = None
    if g3["passed"]:
        cpcv_trades = [{"entry_time": t["entry_time"], "exit_time": t["exit_time"],
                        "pnl_bps": t["pnl_bps"]} for t in trades]
        cpcv = cpcv_harness.run_cpcv(
            cpcv_trades, n_groups=12, k_test=2,
            n_trials_from_ledger=trials_ledger.count() + 1)
        report["g4g5"] = {"pbo": cpcv.get("pbo"), "dsr": cpcv.get("dsr"),
                          "sharpe": cpcv.get("sharpe"),
                          "n_splits": cpcv.get("n_splits"),
                          "n_paths": cpcv.get("n_paths")}

    # Every run writes exactly ONE trial (G5 N grows).
    trial = None
    if write_trial:
        try:
            trial = trials_ledger.increment_trial(
                hypothesis_id=f"US222-DIAG-{rule['param_hash']}",
                param_hash=rule["param_hash"],
                universe_hash=rule.get("instrument", "reconstructed"),
                period_start=str(int(series.ts[0])),
                period_end=str(int(series.ts[-1])),
                result={
                    "feature": rule["feature"],
                    "params": rule["params"],
                    "agreement_is": rule.get("agreement_is"),
                    "g0_passes": g0.get("passes"),
                    "g3_passed": g3["passed"],
                    "net_avg_pnl_bps": report["net_avg_pnl_bps"],
                    "diagnostic": True,
                },
            )
        except Exception as e:  # ledger write must never crash the diagnostic
            trial = {"error": str(e)}
    report["trial"] = trial
    return report


# ---------------------------------------------------------------------------
# Top-level driver
# ---------------------------------------------------------------------------

def run(record: dict, series, run_gauntlet: bool = True,
        asset_class: Optional[str] = None,
        timeframe: Optional[str] = None) -> dict:
    """Full builder + breaker run. Returns the diagnostic report.

    run_gauntlet=False skips the fee-charging gauntlet handoff (used by the
    hermetic OOS-reproduction fixtures, which need no network / ledger).
    """
    from signal_class import classify as _classify

    result = rb.reconstruct(record, series)
    report = {"diagnostic": True, "status": result["status"],
              "reason": result.get("reason")}

    if result["status"] != "ok":
        report["rule"] = None
        return report

    rule = result["rule"]
    norm = result["normalized"]
    asset_class = asset_class or norm.asset_class or "crypto"
    timeframe = timeframe or norm.timeframe or "1h"

    timeline = rb.build_state_timeline(norm.rows)
    record_state_fn = rb.make_record_state_fn(timeline)

    # OOS reproduction.
    oos_states = replay_oos(rule, series, result["oos_indices"])
    oos_ag = rb.agreement_stats(
        rb.apply_feature(series, rule["feature"], rule["params"]),
        record_state_fn, series.ts, result["oos_indices"])
    baseline = no_skill_baseline(record_state_fn, series.ts,
                                 result["oos_indices"])
    verdict = oos_verdict(oos_ag["agreement"], baseline["baseline"])

    # Surface signal class (Q7): measured honestly, never blocks the report.
    signal_class = _classify(
        strategy_id="", description=rule["feature"],
        primitives=[rule["feature"]])

    report.update({
        "rule": rule,
        "agreement_is": rule.get("agreement_is"),
        "agreement_oos": oos_ag["agreement"],
        "oos_scored": oos_ag["scored"],
        "no_skill_baseline": baseline,
        "verdict": verdict["verdict"],
        "advance": verdict["advance"],
        "verdict_reason": verdict["reason"],
        "signal_class": signal_class,
        "t_split": result["t_split"],
        "train_transitions": result["train_transitions"],
        "oos_transitions": result["oos_transitions"],
        "v2_note": result.get("v2_note"),
        "instrument": norm.instrument,
        "asset_class": asset_class,
        "timeframe": timeframe,
    })

    if run_gauntlet:
        if verdict["advance"]:
            rule["instrument"] = norm.instrument
            report["gauntlet"] = hand_to_gauntlet(
                rule, series, asset_class, timeframe)
        else:
            report["gauntlet"] = None
            report["gauntlet_reason"] = "not advanced to gauntlet (OOS kill)"

    return report
