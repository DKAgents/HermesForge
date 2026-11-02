---
id: ADR-009
type: adr
status: proposed
created: 2026-11-02
deciders: [architect]
tags: [adr, gauntlet, gate-g0, cost-model, maker-taker]
topic: adrs
confidence: medium
has_quotes: false
source: HermesForge ADR
---
# ADR-009: G0 Maker/Taker Cost Model + Fill-Probability Haircut

## Status
**proposed** — records the G0 cost-model change BEFORE it takes effect.
No running gate code is altered by this ADR; the change is binding only after
human approval and path-scoped implementation (US-208).

## Context

G0 ("Cost & capacity pre-screen") currently prices every candidate as an
unconditional **taker** round trip:

    all-in round-trip = 2 × 4.5 taker + slippage + funding ≈ 11–13 bps
    gross capture needed ≥ 45 bps (4× cost)

This is deliberately conservative, but it is WRONG for **maker-only** strategies.
Hyperliquid's base perp tier is **1.5 bps maker / 4.5 bps taker**
(`fee_source.py` `FAIL_CLOSED_FALLBACK.crypto.maker_bps=1.5`). A strategy that
genuinely posts passive (maker) limit orders and is filled at rest pays 1.5 bps
per leg, not 4.5 — a 6 bps round-trip cost saving versus taker.

The current screen forces maker-only strategies to clear the taker hurdle,
rejecting candidates whose true cost basis is one-third of what G0 assumes. This
is the "edge < friction" false-negative in the negative direction: it kills
strategies that would be viable if executed correctly.

BUT — maker fills are NOT guaranteed. A maker order may go unfilled (no
trade) or, if the market moves through it, fills as the passive side with
adverse selection (you are the liquidity when the taker has an information
edge). Crediting the full maker rate with no haircut would be the optimistic
error the opposite direction, and would let a strategy "pass" G0 on costs it
will never actually realize.

## Decision

### 1. G0 accepts an explicit execution mode

G0's cost screen gains an `execution_mode ∈ {taker, maker}` parameter (mirrors
the existing `entry_mode` stub in `g0_cost_screen.screen_from_parquet`, currently
taker-only). The default remains `taker`.

- `taker` — unchanged: taker fee both legs, 4× gross-multiplier.
- `maker` — maker fee both legs, with the fill-probability haircut (§2).

A strategy may only be screened at `maker` if it declares `maker-only` execution
in its hypothesis frontmatter (US-202 `execution_mode`); an unconditional-taker
strategy is screened at `taker`.

### 2. Fill-probability haircut for maker-only strategies

The effective per-leg cost for a maker-only strategy is the probability-weighted
blend of "filled at rest" and "missed → must cross to taker to close the loop":

    effective_per_leg_bps = fill_prob · maker_bps + (1 − fill_prob) · taker_bps

    all_in_round_trip_bps = 2 · effective_per_leg_bps + slippage_bps + funding_bps
    gross_capture_needed_bps = GROSS_MULTIPLIER · all_in_round_trip_bps

Binding defaults (tunable, flagged):

- `fill_prob = 0.75` — the assumed probability a posted maker order rests and
  fills passively. Applied identically to both legs.
- `maker_bps = 1.5`, `taker_bps = 4.5` (via `fee_source.get_maker_bps` /
  `get_taker_bps`, fail-closed).
- `slippage_bps`, `funding_bps`, `GROSS_MULTIPLIER` unchanged from the taker
  path (slippage for a resting fill is effectively zero, but the funding
  overhead and the 4× gross multiplier are retained; the haircut already taxes
  the fill uncertainty — see Q2).

Worked default: `effective_per_leg = 0.75·1.5 + 0.25·4.5 = 2.25 bps`, round trip
= `4.5 + 2.5 + 0.5 = 7.5 bps` → gross capture needed `≥ 30 bps` (vs 45 taker).

### 3. G3 remains the hard verification

The 0.75 `fill_prob` is a PROVISIONAL admission, not a claim. G3 (execution
realism — queue-aware `REALISTIC` / `PESSIMISTIC` fill modes) is where the
maker-fill rate is actually measured against L2. A strategy admitted through G0
at `maker` MUST have its `fill_prob` re-estimated from G3's queue-position fill
results, and the G3 fail-closed promotion rule (realistic mean R > 0 AND
pessimistic PF > 1.0) still governs. A maker strategy whose G3-measured fill
rate is below the 0.75 assumption is re-priced at the measured rate and may be
rejected at G3.

## Rationale

- Modeling maker vs taker separately removes a systematic, one-sided false
  negative: passive execution is a real, cheaper path that the current single
  taker assumption structurally cannot see.
- The probability-weighted haircut preserves the fail-closed posture: we never
  credit the full maker rate, because maker fills are not guaranteed and carry
  adverse selection when they DO trade through.
- Leaving G3 as the verification point keeps G0 cheap and conservative while
  ensuring the favorable cost assumption is eventually tested against reality.

## Consequences

**Positive:** maker-only strategies are evaluated on their true (blended) cost
basis; the pipeline can now distinguish "unscreened passive candidates" from
"unconditionally taker" ones instead of flattening both to taker.

**Negative / trade-offs:** a lower hurdle admits more candidates to G1, and the
0.75 default can be gamed by a strategy merely *labelling* itself maker without
ever resting. Mitigation: `execution_mode` must be declared at intake
(US-202) and is validated in G3, not trusted at face value.

**Risks:** incorrect `fill_prob` over- or under-admits. The sensitivity of the
gross-capture hurdle to `fill_prob ∈ {0.5, 0.75, 0.9}` must be reported in the
G0 run.

## Assumptions & Open Questions (explicit)

- Q1 **Two-leg fill-probability independence.** The formula assumes entry and
  exit fill outcomes are independent. A maker-in/taker-out hybrid (or correlated
  fills) is NOT modeled. OPEN — do we need a per-leg `fill_prob` breakdown?
- Q2 **Slippage retained at 2.5 bps on the maker path.** A resting fill should
  have ~0 slippage; retaining the 2.5 bps is conservative. OPEN — should the
  maker path use `slippage_bps=0` (resting) with the haircut carrying all the
  uncertainty, or retain 2.5 as an extra safety margin?
- Q3 **`fill_prob=0.75` prior.** Clearly a placeholder; needs a G3-empirical
  calibration across the liquidity-filtered universe before it is a defensible
  default. OPEN — propose measuring it on the candidate set, not asserting it.
- Q4 The bridge from `fill_prob` to the `execution_mode` frontmatter enum is
  underspecified; confirm the enum values (`taker` / `maker`) match the
  `validate_strategy.py` `execution_mode` extension in PROP-001 §03.

## Review Date
Revisit after G3 fill-probability calibration (2026-12-02).

## Related
- [[US-208-G0-Maker-Taker]] · [[US-165-Dynamic-Venue-Correct-Fees]] · [[PROP-001-§02]]
- [[ADR-008-G1-Size-Relative-Capacity-Power-Floor]] · [[ADR-010-G7-Paper-Hostile-Fill]]