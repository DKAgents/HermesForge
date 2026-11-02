---
id: ADR-008
type: adr
status: proposed
created: 2026-11-02
revised: 2026-11-02
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

**Revision 2 (2026-11-02) — response to risk-guardian admission-bar rejection:**
the power floor as originally drafted could (a) admit a strategy on fewer trades
than the old fixed `≥200` rule, (b) anchor `μ_R` to a *self-declared* bps edge
rather than a measured one, and (c) silently drop the `≥15`-symbol
cross-sectional-independence floor. All three are closed below (§2, §3, §4).
Details in "Risk-Guardian Objections Closed".

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

### 1. Size-relative capacity check (replaces the $250k / $50k floors)

Drop the two fixed *notional* minimums. In their place, G1 requires that the
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

### 2. Statistical-power floor, floored by a hard MIN_SAMPLE_FLOOR

Replace the flat 200 with a minimum sample `N_min` sufficient to detect the
strategy's measured effect size at a fixed significance and power:

    N_min = ceil( (z_{1-α/2} + z_{1-β})² · (σ_R / μ_R)² )

where

- `μ_R` = the strategy's **measured** expected effect size, expressed as the
  **mean R-multiple per trade of a prior backtest / ledger trial** (see §3 — it
  is read from data, never self-declared).
- `σ_R` = the **standard deviation of that same measured R distribution** (same
  source as `μ_R`; no separate prior is permitted).
- `α = 0.05` (two-sided), `β = 0.20` (power 0.80) — tunable defaults.

The power floor alone is **not** the admission rule. G1's pass condition is a
**hard conjunction** of the power floor and a fixed statistical minimum sample
size, so a large claimed `μ_R` can never lower the bar below what the old fixed
rule already required:

    pass_power = ( signal_count >= max(N_min, MIN_SAMPLE_FLOOR) )

- `MIN_SAMPLE_FLOOR` = **200** (binding default). This is the old `≥200`-signal
  floor preserved verbatim as a hard lower bound. Because `N_min` is combined via
  `max(...)`, the power-based floor can only ever **raise** the requirement for
  thin-edge candidates (`N_min > 200`) and can **never** admit a strategy on
  fewer than 200 trades. The power floor is a one-directional tightening, not a
  loosening.

If `μ_R <= 0` (no measured positive edge), the candidate fails G1 immediately
(cannot compute a positive power floor → reject).

Retirement / G5 (DSR/PBO) remain unchanged; they still consume the resulting N.

### 3. μ_R and σ_R are MEASURED, never self-declared (binding)

Neither `μ_R` nor `σ_R` may come from the proposer's declared edge (the US-202
frontmatter `expected_gross_edge_bps` is **not** a valid source). Both must be
read from a **prior backtest / trials-ledger R distribution** for the same
hypothesis under the **same `param_hash` and `universe_hash`**:

- `μ_R` = `mean(R_1 … R_n)` of the per-trade R-multiples recorded for that
  hypothesis in the trials ledger (`data/gauntlet/trials.jsonl`) or the most
  recent backtest's R-teacher series.
- `σ_R` = `std(R_1 … R_n)` of that same series.

If no prior backtest R distribution exists for the hypothesis (same param hash +
universe hash), G1 **fails closed** with reason `mu_R_unmeasured`. A candidate
cannot be admitted on an edge it has declared but not yet produced in a backtest.
This removes the bps→R conversion entirely (the old A3 hazard); the edge is read
directly as measured R, so there is no risk-unit/stop-convention distortion.

### 4. Breadth minimum RESTORED (≥ 15 symbols, or an explicit size-justified replacement)

The `≥15`-symbol requirement is **not** absorbed into the power floor. It is
restored as a **standalone hard gate**, because cross-sectional independence is
a property of *how many distinct symbols* produced the signal sample and cannot
be proxied by aggregate `signal_count` (200 signals on 2 symbols is not 200
independent observations — it is 2, heavily autocorrelated).

    pass_breadth = ( distinct_symbols >= MIN_BREADTH_SYMBOLS )

- `MIN_BREADTH_SYMBOLS` = **15** (binding default).

The only way to relax it is an **explicit, size-justified replacement** authored
and human-approved as its own decision record: the proposer must state the
reduced symbol count, the economic reason the strategy genuinely needs fewer
symbols, and how cross-sectional dependence is instead bounded (e.g., a
single-instrument strategy citing BTC/USD as a deep, OI-diverse name, with a
documented autocorrelation/clustering correction applied to the power floor).
Absent that approved record, the floor is 15. It is never dropped silently.

## Rationale

- Size-relative capacity ties the gate to the ACTUAL deployment size (the $10K
  stage), which is the point of a staged pipeline. An absolute $250k floor is a
  proxy for "tradeable at institutional size," which is not our objective.
- A power floor ties the signal rule to the strategy's OWN **measured** edge.
  Under-powered passes (too few signals for a thin edge) are the classic
  overfit/mirage failure mode; this makes "enough evidence" a function of "what
  you can **demonstrate**," not "what you claim."
- Folding `MIN_SAMPLE_FLOOR` and the breadth floor back in keeps the power floor
  a **strict tightening** of the old flat rule, so the recalibration can only
  raise the admission bar, never lower it.

## Consequences

**Positive:** candidates that are genuinely tradeable at $10K stop failing on
irrelevant absolute notional floors; thin-edge candidates are forced to either
produce a measured large sample or be rejected; the sample-size and breadth
floors the old rule encoded are preserved as hard lower bounds.

**Negative / trade-offs:** the power floor is only as honest as the measured
R distribution feeding `μ_R`/`σ_R`; a strategy with a short, noisy backtest
history fails closed (`mu_R_unmeasured`) rather than being admitted on a prior.
That is intentional — G1 is now *evidence-gated*, not *declaration-gated*.

**Risks:** `SIZE_RELATIVE_CAP` at 1.5% is a default, not a derived optimum —
flagged for sensitivity (0.01 / 0.015 / 0.02) in US-210 re-runs.

## Risk-Guardian Objections Closed

1. **"Power floor can admit fewer than 200 trades."** Closed by
   `pass_power = signal_count >= max(N_min, MIN_SAMPLE_FLOOR)` with
   `MIN_SAMPLE_FLOOR = 200`. The power term can only *increase* the required N.
2. **"μ_R is self-declared."** Closed by §3: `μ_R`/`σ_R` are read only from a
   prior backtest / trials-ledger R distribution (same `param_hash` +
   `universe_hash`), and G1 fails closed (`mu_R_unmeasured`) without one.
3. **"≥15-symbol breadth silently dropped."** Closed by §4: breadth is
   reinstated as a standalone hard gate (`MIN_BREADTH_SYMBOLS = 15`); any
   relaxation requires an explicit, separately human-approved size justification.

## Assumptions & Open Questions (explicit)

- A1 `max_order_usd_at_10k` assumes the strategy exposes a functional sizing
  rule. Candidates without one fail closed (`sizing_rule_missing`) — confirm this
  is the desired behavior rather than requiring a default sizing.
- A2 `SIZE_RELATIVE_CAP=0.015` is a placeholder within the stated 1–2% band.
  Sensitivity must be run before treating it as final (US-210).
- A3 (resolved) The prior OPEN bps→R conversion for `μ_R` is removed by §3; the
  edge is read directly as measured R. No shared conversion helper is needed.
- A4 (resolved) The prior OPEN `σ_R` "pre-backtest prior" is removed by §3; G1
  requires a measured R distribution and fails closed without one.
- A5 α/β (0.05 / 0.80) are conventional defaults; whether a one-sided test is
  appropriate for a directional edge claim is an open statistical question.
- A6 `MIN_SAMPLE_FLOOR=200` is carried from the old rule unchanged; whether it
  should eventually be expressed as a statistical minimum (e.g. a floor on the
  effective number of independent observations after breadth/autocorrelation
  correction) instead of the literal trade count is OPEN — do not change it
  without a separate decision record.

## Review Date
Revisit after US-210 re-run under the recalibrated G1 (2026-12-02).

## Related
- [[US-207-G1-Recalibration]] · [[US-210-Rerun-G1-Died]] · [[PROP-001-§02]]
- [[ADR-009-G0-Maker-Taker-Cost-Model]] · [[ADR-010-G7-Paper-Hostile-Fill]]