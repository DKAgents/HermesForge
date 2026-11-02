---
id: ADR-008
type: adr
status: proposed
created: 2026-11-02
deciders: [architect]
tags: [adr, gauntlet, gate-g1, size-relative, statistical-power]
topic: adrs
confidence: medium
has_quotes: false
source: HermesForge ADR
---
# ADR-008: G1 Recalibration — Size-Relative Capacity + Statistical-Power Floor

## Status
**proposed** — records the G1 threshold change BEFORE it takes effect.
No running gate code is altered by this ADR; the change is binding only after
human approval and path-scoped implementation (US-207).

## Context

G1 ("Signal scan on liquidity-filtered universe") currently gates candidates on
three FIXED, absolute capacity minimums and one FIXED signal count:

    Pass — ≥ 200 signals across ≥ 15 symbols · 30d median 5m notional ≥ $250k ·
    top-5 depth ≥ $50k within 10 bps · universe hash recorded

These fixed floors have two defects for a pipeline that is meant to produce a
tradable edge starting at **$100 capital and scaling to $5K → $10K** (EPIC-017):

1. **Absolute capacity floors are calibrated to a size we are not yet trading.**
   A $250k 5-minute notional bar and a $50k top-5 depth are irrelevant to a $10K
   stage; they reject candidates that are perfectly tradeable at the actual
   deployment size, and (worse) they implicitly endorse the ones that only clear
   at a size we would never touch at $10K. Capacity should be judged *relative to
   the size we will actually submit*, not against an arbitrary absolute bar.

2. **A fixed ≥200-signal rule is a count, not evidence.** 200 signals is the
   wrong dimension. What matters is whether the sample is large enough to *detect
   the strategy's stated expected effect size* with adequate statistical power.
   A strategy expecting a large edge needs fewer signals to be distinguishable
   from zero; a strategy expecting a small edge needs many more. A flat 200 is
   simultaneously under-powered for small-edge candidates and over-demanding for
   large-edge candidates.

This ADR replaces both defects. It is one of the three EPIC-017 Phase-3 gate
recalibrations (US-207, US-208, US-209); each is recorded separately because
each is an independent, binding threshold change.

## Decision

### 1. Size-relative capacity check (replaces the $250k / $50k / ≥15-symbol floors)

Drop the three fixed minimums entirely. In their place, G1 requires that the
strategy's **planned maximum single-order notional at the $10K capital stage**
be no larger than a size-relative fraction of the **top-5 depth within 10 bps**
on the side the order will consume.

    pass_capacity = (
        max_order_usd_at_10k <= SIZE_RELATIVE_CAP * top5_depth_usd_10bps
    )

Definitions (binding):

- `max_order_usd_at_10k` — the largest single order the strategy's own sizing
  rule would submit when capital is $10K. Derived from the strategy's documented
  sizing logic (the 1R = 1% risk-budget rule from PROP-001 §04 / the
  `size_position` invariant): `max_order_usd = CAPITAL_RISK_BUDGET * 10_000 /
  (stop_distance_frac)`, capped by any OI-capacity / gross-notional rail the
  strategy itself declares. If the strategy does not declare a sizing rule, the
  check fails closed with reason `sizing_rule_missing`.

- `top5_depth_usd_10bps` — sum of resting notional (size × price) across the top
  5 price levels that lie within 10 bps of mid on the **passive/consumed side**
  (ask side for a buy, bid side for a sell). Sourced from live L2 (`l2Book`) at
  scan time; if L2 is unavailable for a symbol, that symbol does NOT contribute
  to the capacity pass (fail-closed — no fabricated depth).

- `SIZE_RELATIVE_CAP` — the allowed market-impact clip, a tunable default in the
  range **0.01 (1%) to 0.02 (2%)**, defaulting to **0.015 (1.5%)**.

The ≥15-symbol requirement is absorbed into the signal-power floor (§2): symbol
count is no longer a standalone gate, it is a property reported on the scan.

### 2. Statistical-power floor (replaces the fixed ≥200-signal rule)

Replace the flat 200 with a minimum sample `N_min` sufficient to detect the
strategy's expected effect size at a fixed significance and power:

    N_min = ceil( (z_{1-α/2} + z_{1-β})² · (σ_R / μ_R)² )

where

- `μ_R` = the strategy's expected effect size expressed as mean R-multiple per
  trade (converted from the pre-registered `expected gross edge bps` via the
  strategy's risk unit; see US-202 frontmatter `expected_gross_edge_bps`).
- `σ_R` = per-trade standard deviation of R, taken from the strategy's backtest
  R distribution (or, if unavailable pre-backtest, a conservative prior —
  flag `power_sigma_source=prior`).
- `α = 0.05` (two-sided), `β = 0.20` (power 0.80) — tunable defaults.

    pass_power = (signal_count >= N_min)

`N_min` is computed per-candidate from its OWN stated effect size, never a
constant. A candidate that pre-registers a small edge is required to produce a
proportionally larger sample. If `μ_R <= 0` (no claimed positive edge), the
candidate fails G1 immediately (cannot compute a positive power floor → reject).

Retirement / G5 (DSR/PBO) remain unchanged; they still consume the resulting N.

## Rationale

- Size-relative capacity ties the gate to the ACTUAL deployment size (the $10K
  stage), which is the point of a staged pipeline. An absolute $250k floor is a
  proxy for "tradeable at institutional size," which is not our objective.
- A power floor ties the signal rule to the strategy's OWN claim. Under-powered
  passes (too few signals for a thin edge) are the classic overfit/mirage
  failure mode; this makes "enough evidence" a function of "what you claim to
  have," which is exactly what pre-registration (US-202) enables.

## Consequences

**Positive:** candidates that are genuinely tradeable at $10K stop failing on
irrelevant absolute floors; thin-edge candidates are forced to either claim a
small effect (and produce a large sample) or be rejected.

**Negative / trade-offs:** the power floor is only as honest as `σ_R` and the
bps→R conversion; a bad risk-unit conversion can distort `N_min` (mitigation:
`risk_usd` is already required to be re-derived and stated per promotion record,
ADR-referenced US-185 §3.3).

**Risks:** `SIZE_RELATIVE_CAP` at 1.5% is a default, not a derived optimum —
flagged for sensitivity (0.01 / 0.015 / 0.02) in US-210 re-runs.

## Assumptions & Open Questions (explicit)

- A1 `max_order_usd_at_10k` assumes the strategy exposes a functional sizing
  rule. Candidates without one fail closed (`sizing_rule_missing`) — confirm this
  is the desired behavior rather than requiring a default sizing.
- A2 `SIZE_RELATIVE_CAP=0.015` is a placeholder within the stated 1–2% band.
  Sensitivity must be run before treating it as final (US-210).
- A3 The bps→R conversion for `μ_R` needs a canonical definition (which risk
  unit, which stop convention). OPEN — propose a single shared conversion helper
  shared with G0/G5 so the edge is not double-counted across gates.
- A4 `σ_R` pre-backtest prior value is unspecified. OPEN — needs a default (e.g.
  2.0 R) or a requirement that G1 only runs with a backtest R distribution.
- A5 α/β (0.05 / 0.80) are conventional defaults; whether a one-sided test is
  appropriate for a directional edge claim is an open statistical question.

## Review Date
Revisit after US-210 re-run under the recalibrated G1 (2026-12-02).

## Related
- [[US-207-G1-Recalibration]] · [[US-210-Rerun-G1-Died]] · [[PROP-001-§02]]
- [[ADR-009-G0-Maker-Taker-Cost-Model]] · [[ADR-010-G7-Paper-Hostile-Fill]]