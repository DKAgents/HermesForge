#!/usr/bin/env python3
"""g1_gate.py — G1 signal-scan gate (US-207 / ADR-008 recalibration).

Replaces G1's fixed, absolute admission floors (>=200 signals across >=15
symbols · 30d median 5m notional >= $250k · top-5 depth >= $50k within 10 bps)
with three size-relative / evidence-based checks:

  1. Capacity (size-relative): the strategy's planned maximum single-order
     notional at the $10K capital stage must be <= SIZE_RELATIVE_CAP of the
     top-5 depth within 10 bps on the consumed side.

        pass_capacity = max_order_usd_at_10k <= SIZE_RELATIVE_CAP * top5_depth_usd_10bps

     SIZE_RELATIVE_CAP defaults to 0.015 (1.5%), within the binding 0.01--0.02
     band. max_order_usd_at_10k is derived from the strategy's OWN sizing rule
     (1R = 1% capital / stop_distance_frac, capped by any declared rail). If no
     sizing rule is declared the candidate FAILS CLOSED (``sizing_rule_missing``);
     if L2 depth is unavailable for a symbol the check FAILS CLOSED
     (``depth_unavailable``) — no fabricated depth.

  2. Statistical power (floor), floored by a hard MIN_SAMPLE_FLOOR:

        N_min = ceil( (z_{1-alpha/2} + z_{1-beta})^2 * (sigma_R / mu_R)^2 )
        pass_power = signal_count >= max(N_min, MIN_SAMPLE_FLOOR)

     MIN_SAMPLE_FLOOR = 200 (the old >=200 rule preserved verbatim as a hard
     lower bound), so the power term can only ever RAISE the requirement for
     thin-edge candidates and can never admit a strategy on fewer than 200
     trades. mu_R / sigma_R are MEASURED (mean/std of the prior backtest /
     trials-ledger R distribution for the same param_hash + universe_hash),
     never self-declared. mu_R unmeasured -> fail closed (``mu_R_unmeasured``);
     mu_R <= 0 -> reject (no positive edge).

  3. Breadth (restored): distinct_symbols >= MIN_BREADTH_SYMBOLS = 15. This is
     a standalone hard gate (cross-sectional independence), never silently
     dropped and never proxied by aggregate signal_count.

All three are a hard conjunction; any failure rejects. No running gate code is
mutated by this module — it is a self-contained gate evaluator (like the other
g0/g2/g3/g6/g7 gate modules).
"""

from __future__ import annotations

import math

# ── Binding defaults (ADR-008) ────────────────────────────────────────────────
ALPHA = 0.05              # two-sided significance (tunable default)
BETA = 0.20               # beta -> power = 1 - beta = 0.80 (tunable default)
MIN_SAMPLE_FLOOR = 200    # hard lower bound on signal_count (the old >=200 rule)
MIN_BREADTH_SYMBOLS = 15  # restored breadth floor (distinct symbols)
SIZE_RELATIVE_CAP = 0.015 # 1.5% market-impact clip (binding band 0.01..0.02)
SIZE_RELATIVE_CAP_RANGE = (0.01, 0.02)
DEPTH_BPS_WINDOW = 10.0   # "within 10 bps" of mid for the top-5 depth window

CAPITAL_AT_10K = 10_000.0   # the deployment size G1 is sized against
CAPITAL_RISK_BUDGET = 0.01  # 1R = 1% of capital (PROP-001 §04 sizing invariant)


def _norm_ppf(p: float) -> float:
    """Standard normal quantile (inverse CDF), rational approximation.

    Mirrors cpcv_harness._norm_ppf so z_{1-alpha/2} and z_{1-beta} are computed
    without a scipy dependency (keeps the gate self-contained).
    """
    if p <= 0.0:
        return -float("inf")
    if p >= 1.0:
        return float("inf")
    a = 0.147
    y = 2.0 * p - 1.0
    part1 = math.log(1.0 - y * y)
    part2 = 2.0 / (math.pi * a) + part1 / 2.0
    sign = 1.0 if y >= 0 else -1.0
    result = sign * math.sqrt(math.sqrt(part2 * part2 - part1 / a) - part2)
    return result * math.sqrt(2.0)


def power_min_sample(mu_r: float | None, sigma_r: float | None,
                     alpha: float = ALPHA, beta: float = BETA) -> float | None:
    """Minimum sample N_min to detect effect size mu_R at power (1-beta).

    N_min = ceil( (z_{1-alpha/2} + z_{1-beta})^2 * (sigma_R / mu_R)^2 ).

    Returns None when the effect size is unmeasured (mu_R/sigma_R None) or
    non-positive (mu_R <= 0) — both fail closed upstream. sigma_R <= 0 (a
    degenerate zero-variance series) yields N_min = 0, since a flat positive
    edge needs no sample to distinguish from zero.
    """
    if mu_r is None or sigma_r is None:
        return None
    mu_r = float(mu_r)
    sigma_r = float(sigma_r)
    if mu_r <= 0:
        return None
    if sigma_r <= 0:
        return 0
    z_alpha = _norm_ppf(1.0 - alpha / 2.0)
    z_beta = _norm_ppf(1.0 - beta)
    n = (z_alpha + z_beta) ** 2 * (sigma_r / mu_r) ** 2
    return math.ceil(n)


def max_order_usd_at_10k(stop_distance_frac: float | None,
                         *, declared_notional_cap: float | None = None,
                         capital: float = CAPITAL_AT_10K,
                         risk_budget: float = CAPITAL_RISK_BUDGET) -> float | None:
    """Derive the largest single-order notional the sizing rule submits at $10K.

    max_order_usd = risk_budget * capital / stop_distance_frac, capped by any
    declared OI-capacity / gross-notional rail.

    Returns None (fail closed, ``sizing_rule_missing``) when the strategy does
    not declare a sizing rule — i.e. no finite positive stop distance.
    """
    if stop_distance_frac is None or not math.isfinite(float(stop_distance_frac)):
        return None
    stop_distance_frac = float(stop_distance_frac)
    if stop_distance_frac <= 0:
        return None
    order = risk_budget * capital / stop_distance_frac
    if declared_notional_cap is not None and math.isfinite(float(declared_notional_cap)):
        order = min(order, float(declared_notional_cap))
    return order


def capacity_ok(max_order_usd: float | None, top5_depth_usd_10bps: float | None,
                cap: float = SIZE_RELATIVE_CAP) -> tuple[bool, str | None]:
    """Size-relative capacity check.

    Returns (ok, reason). ok=False with a non-None reason is a fail-closed
    rejection (sizing rule missing, or depth unavailable). ok=False with
    reason=None means the clip was simply violated (numeric failure).
    """
    if max_order_usd is None:
        return False, "sizing_rule_missing"
    if top5_depth_usd_10bps is None or not math.isfinite(float(top5_depth_usd_10bps)):
        return False, "depth_unavailable"
    depth = float(top5_depth_usd_10bps)
    if depth <= 0:
        return False, "depth_unavailable"
    return (max_order_usd <= cap * depth), None


def evaluate_g1(*,
                signal_count: int,
                distinct_symbols: int,
                mu_r: float | None,
                sigma_r: float | None,
                max_order_usd: float | None,
                top5_depth_usd_10bps: float | None,
                stop_distance_frac: float | None = None,
                declared_notional_cap: float | None = None,
                size_relative_cap: float = SIZE_RELATIVE_CAP,
                min_sample_floor: int = MIN_SAMPLE_FLOOR,
                min_breadth_symbols: int = MIN_BREADTH_SYMBOLS,
                alpha: float = ALPHA,
                beta: float = BETA,
                ) -> dict:
    """Evaluate the recalibrated G1 gate (hard conjunction of three checks).

    All inputs are measured / declared-external quantities; this evaluator
    performs NO data access itself (fail-closed on any missing input).

    Returns a record:
        passed, reasons, capacity_ok, power_ok, breadth_ok,
        n_min_power, required_min_sample, mu_r, sigma_r,
        max_order_usd, top5_depth_usd_10bps, size_relative_cap, clip_usd.
    """
    reasons: list[str] = []

    # 0. Derive max order from the declared sizing rule if not passed directly.
    if max_order_usd is None:
        max_order_usd = max_order_usd_at_10k(
            stop_distance_frac, declared_notional_cap=declared_notional_cap)

    # 1. Capacity (size-relative).
    cap_ok, cap_reason = capacity_ok(max_order_usd, top5_depth_usd_10bps,
                                     cap=size_relative_cap)
    if not cap_ok:
        reasons.append(cap_reason if cap_reason else
                       f"max order {max_order_usd:,.0f} USD exceeds "
                       f"{size_relative_cap:.1%} of top-5 depth {top5_depth_usd_10bps:,.0f} USD")

    # 2. Statistical power floor (floored by the hard minimum sample).
    n_min_power = power_min_sample(mu_r, sigma_r, alpha=alpha, beta=beta)
    if n_min_power is None:
        if mu_r is None or sigma_r is None:
            reasons.append("mu_R_unmeasured")
        else:
            reasons.append(f"non_positive_edge (mu_R = {mu_r})")
        required_min_sample = min_sample_floor
        power_ok = False
    else:
        required_min_sample = max(n_min_power, min_sample_floor)
        power_ok = signal_count >= required_min_sample
        if not power_ok:
            reasons.append(
                f"insufficient sample: n={signal_count} < "
                f"max(N_min={n_min_power}, floor={min_sample_floor}) = {required_min_sample}")

    # 3. Breadth (restored standalone hard gate).
    breadth_ok = distinct_symbols >= min_breadth_symbols
    if not breadth_ok:
        reasons.append(
            f"insufficient breadth: distinct_symbols={distinct_symbols} < {min_breadth_symbols}")

    passed = len(reasons) == 0

    clip_usd = (size_relative_cap * top5_depth_usd_10bps
                if top5_depth_usd_10bps is not None else None)
    return {
        "passed": passed,
        "reasons": reasons,
        "capacity_ok": cap_ok,
        "power_ok": power_ok,
        "breadth_ok": breadth_ok,
        "n_min_power": n_min_power,
        "required_min_sample": required_min_sample,
        "signal_count": signal_count,
        "distinct_symbols": distinct_symbols,
        "mu_r": mu_r,
        "sigma_r": sigma_r,
        "max_order_usd": max_order_usd,
        "top5_depth_usd_10bps": top5_depth_usd_10bps,
        "size_relative_cap": size_relative_cap,
        "clip_usd": clip_usd,
        "min_sample_floor": min_sample_floor,
        "min_breadth_symbols": min_breadth_symbols,
    }


if __name__ == "__main__":
    import json

    def show(label, **kw):
        print(f"\n=== {label} ===")
        print(json.dumps(evaluate_g1(**kw), indent=2, default=str))

    # (a) PASS: ample depth, measured positive edge (thin -> N_min > 200),
    #          200 signals, 15 symbols.
    show("pass (thin edge, N_min>200, exactly 200 signals)",
         signal_count=200, distinct_symbols=15,
         mu_r=0.1, sigma_r=0.5,
         max_order_usd=1000.0, top5_depth_usd_10bps=500_000.0)

    # (b) PASS: LARGE measured edge -> N_min < 200 but floor keeps 200.
    show("pass (large edge, power floor floored at 200)",
         signal_count=200, distinct_symbols=20,
         mu_r=0.8, sigma_r=1.0,
         max_order_usd=1000.0, top5_depth_usd_10bps=500_000.0)

    # (c) FAIL: capacity — max order exceeds 1.5% clip.
    show("fail (capacity: order > clip)",
         signal_count=1000, distinct_symbols=20,
         mu_r=0.2, sigma_r=0.5,
         max_order_usd=10_000.0, top5_depth_usd_10bps=100_000.0)

    # (d) FAIL: sizing rule missing (max_order derived from None stop distance).
    show("fail (sizing_rule_missing)",
         signal_count=1000, distinct_symbols=20,
         mu_r=0.2, sigma_r=0.5,
         max_order_usd=None, stop_distance_frac=None, top5_depth_usd_10bps=500_000.0)

    # (e) FAIL: mu_R unmeasured.
    show("fail (mu_R_unmeasured)",
         signal_count=1000, distinct_symbols=20,
         mu_r=None, sigma_r=None,
         max_order_usd=1000.0, top5_depth_usd_10bps=500_000.0)

    # (f) FAIL: mu_R <= 0 (no positive edge).
    show("fail (non-positive edge)",
         signal_count=1000, distinct_symbols=20,
         mu_r=-0.1, sigma_r=0.5,
         max_order_usd=1000.0, top5_depth_usd_10bps=500_000.0)

    # (g) FAIL: breadth below 15 symbols.
    show("fail (breadth: 14 symbols)",
         signal_count=1000, distinct_symbols=14,
         mu_r=0.2, sigma_r=0.5,
         max_order_usd=1000.0, top5_depth_usd_10bps=500_000.0)

    # (h) FAIL: power floor RAISES the bar — thin edge needs N_min > 200.
    show("fail (thin edge: N_min=785 > 200, only 200 signals)",
         signal_count=200, distinct_symbols=20,
         mu_r=0.05, sigma_r=0.5,
         max_order_usd=1000.0, top5_depth_usd_10bps=500_000.0)