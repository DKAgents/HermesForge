---
id: ADR-009
type: adr
status: proposed
created: 2026-11-02
revised: 2026-11-02
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

**Revision 2 (2026-11-02) — response to risk-guardian admission-bar rejection:**
the draft's `fill_prob = 0.75` was too optimistic (it let a strategy clear a
cheaper hurdle on a self-declared maker label, with no adverse-selection model
and no requirement to ever demonstrate passive fills). Three fixes: (a) the
default `fill_prob` is lowered to **0.35**; (b) the maker path requires an
explicit **adverse-selection** term, not the two-leg-independence shortcut; and
(c) maker labeling is **fail-closed** — a strategy is taker-costed unless G3
demonstrates passive fills on real book data. Details in "Risk-Guardian
Objections Closed".

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
will never actually realize. A resting maker fill is **adversely selected**:
it is more likely to fill precisely when price is moving *against* the maker
(a resting buy limit fills as price falls through it; a resting sell fills as
price rises through it), so the realized cost of a "maker" fill exceeds the raw
1.5 bps and cannot be modeled as a frictionless, independent event.

## Decision

### 1. G0 accepts an explicit execution mode, but maker is FAIL-CLOSED

G0's cost screen gains an `execution_mode ∈ {taker, maker}` parameter (mirrors
the existing `entry_mode` stub in `g0_cost_screen.screen_from_parquet`, currently
taker-only). The default remains `taker`.

- `taker` — unchanged: taker fee both legs, 4× gross-multiplier.
- `maker` — maker fee both legs, with the fill-probability haircut (§2) AND the
  adverse-selection term (§3).

**Fail-closed labeling rule (binding):** a strategy declared `maker` in its
hypothesis frontmatter (US-202 `execution_mode`) is **screened at taker cost at
G0 by default**. The maker discount is **not** creditable on the proposer's
word. The maker cost basis only becomes available to a candidate once G3
(execution realism) has **demonstrated passive fills on real L2 book data** for
that strategy (see §4). Until that demonstration exists, the strategy is
taker-costed — full stop.

### 2. Fill-probability haircut, lowered default

The effective per-leg cost for a maker-credit strategy is the probability-weighted
blend of "filled at rest" and "missed → must cross to taker to close the loop":

    effective_per_leg_bps = fill_prob · (maker_bps + adverse_selection_bps)
                            + (1 − fill_prob) · taker_bps

    all_in_round_trip_bps = 2 · effective_per_leg_bps + slippage_bps + funding_bps
    gross_capture_needed_bps = GROSS_MULTIPLIER · all_in_round_trip_bps

Binding defaults (tunable, flagged):

- `fill_prob = 0.35` — the assumed probability a posted maker order rests and
  fills passively. **Rationale for 0.35 (well below the prior 0.75):** on liquid
  crypto perps, a resting limit order that is not aggressively re-quoted fills
  only a minority of the time — realistic passive fill rates are in the ~30–50%
  band, and the fill that *does* occur is the adversely-selected one. 0.35 is the
  fail-closed anchor *inside* that band: it credits maker economics only for the
  fraction of the time we can actually expect them, and it is intentionally
  pessimistic about the fill rate precisely because the label has not yet been
  earned at G0. Applied to the maker leg; the taker leg is priced fully.
- `adverse_selection_bps` — the maker-side adverse-selection penalty (§3).
- `maker_bps = 1.5`, `taker_bps = 4.5` (via `fee_source.get_maker_bps` /
  `get_taker_bps`, fail-closed).
- `slippage_bps`, `funding_bps`, `GROSS_MULTIPLIER` unchanged from the taker
  path.

Worked default: `effective_per_leg = 0.35·(1.5 + adverse_selection) +
0.65·4.5`. With `adverse_selection_bps = 1.5` (§3 default): `= 0.35·3.0 +
0.65·4.5 = 1.05 + 2.925 = 3.975 bps`, round trip `= 2·3.975 + 2.5 + 0.5 ≈
10.95 bps` → gross capture needed `≈ 43.8 bps` — essentially the taker hurdle,
which is the point: at G0, an *unproven* maker label buys almost no discount.

### 3. Explicit adverse-selection modeling (no two-leg independence)

The maker path must model adverse selection explicitly. The prior draft's
two-leg-independence assumption (old Q1) is **rejected**: entry and exit fill
outcomes are not independent, and a maker fill is a *conditional* event.

Binding requirement: a maker-credit candidate must supply (or G3 must measure)
an `adverse_selection_bps` term modeled as the expected adverse move *conditioned
on a filler*:

- Default `adverse_selection_bps = 1.5` (flagged, tunable). This is a
  conservative prior, NOT a measured value — it assumes a maker fill slips
  against the poster by roughly one base-maker fee's worth on average.
- It must be replaced by a **measured** estimate from G3 real-book data (queue
  position at rest, fill-or-kill crawl, and the mark-move between rest and fill)
  before any maker cost is credited at promotion. Until measured, the default is
  applied — no strategy gets a smaller-than-default adverse-selection term on its
  own assertion.

Joint modeling: where a strategy's entry and exit rests are correlated (e.g.
maker-in/maker-out on the same passive side), the screen must use a **joint
fill model** (conditional / Markov), not the product of independent
`fill_prob`s. A per-leg breakdown is acceptable only if the legs are structurally
demonstrated to be independent; otherwise the correlated path is priced as the
taker leg.

### 4. G3 remains the hard verification, and gates the maker credit

`fill_prob` and `adverse_selection_bps` are PROVISIONAL priors, not claims. G3
(execution realism — queue-aware `REALISTIC` / `PESSIMISTIC` fill modes) is where:

1. the maker-fill rate is actually measured against live L2 book data, and
2. the adverse-selection term is estimated from the mark-move conditioned on
   fills.

**Fail-closed promotion rule (binding):** a strategy is treated as taker-costed
through G0 and G3 promotion unless G3's real-book results **demonstrate passive
fills** — i.e. a measured fill rate `≥ some minimum` with the measured
adverse-selection term applied — for that strategy. The existing G3 fail-closed
promotion rule (realistic mean R > 0 AND pessimistic PF > 1.0) still governs.
A maker-declared strategy whose G3-measured fill rate is below 0.35, or whose
measured adverse selection exceeds the default, is re-priced at the measured
values (taker if worse) and may be rejected at G3.

## Rationale

- Modeling maker vs taker separately removes a systematic, one-sided false
  negative: passive execution is a real, cheaper path that the current single
  taker assumption structurally cannot see.
- The lowered `fill_prob` (0.35) plus the explicit adverse-selection term, plus
  fail-closed labeling, preserve a **strictly fail-closed posture**: we never
  credit the full maker rate (or even a generous partial one) on a label we have
  not yet earned, because maker fills are not guaranteed and carry adverse
  selection when they DO trade through.
- The practical effect is that G0's admission hurdle is essentially unchanged
  until G3 *demonstrates* passive fills — the maker discount is earned later, not
  assumed earlier.

## Consequences

**Positive:** maker-only strategies can still be evaluated on their true
(blended) cost basis — but only after they have *shown* passive fills, so the
favorable cost assumption is tested against reality before it lowers the bar.

**Negative / trade-offs:** the maker path is now gated behind a G3 measurement,
so the G0 false-negative the ADR originally set out to fix is only partially
relieved at G0 itself (a maker strategy still clears roughly the taker hurdle at
G0). That is accepted: the risk-guardian's bar-lowering objection takes
precedence over the false-negative, and the false-negative is re-opened only on
evidence (G3), not on assertion.

**Risks:** incorrect `fill_prob` or `adverse_selection_bps` still over- or
under-admits. The sensitivity of the gross-capture hurdle to
`fill_prob ∈ {0.2, 0.35, 0.5}` and `adverse_selection_bps ∈ {0, 1.5, 3.0}` must
be reported in the G0 run, alongside the measured G3 values.

## Risk-Guardian Objections Closed

1. **"`fill_prob = 0.75` is too optimistic — it lowers the admission bar."**
   Closed by lowering the default to **0.35** (§2), so a maker label buys almost
   no cost discount at G0 (worked round-trip ≈ 10.95 bps vs ≈ 11–13 bps taker).
2. **"No adverse-selection modeling; two-leg independence assumed."** Closed by
   §3: an explicit `adverse_selection_bps` term is added (default 1.5, must be
   measured at G3), and the two-leg-independence assumption is rejected in favor
   of a joint/conditional fill model.
3. **"Maker labeling can be gamed — self-declared maker passes cheaper."**
   Closed by §1 + §4: labeling is fail-closed — a strategy is taker-costed unless
   G3 demonstrates passive fills on real book data, and the maker credit is
   gated behind that demonstration.

## Assumptions & Open Questions (explicit)

- Q1 (resolved) Two-leg fill-probability independence is removed; a joint
  fill model is required where legs are correlated (§3).
- Q2 **Slippage retained at 2.5 bps on the maker path.** A resting fill should
  have ~0 slippage; retaining the 2.5 bps is conservative. OPEN — should the
  maker path use `slippage_bps=0` (resting) with the adverse-selection term
  carrying all the uncertainty, or retain 2.5 as an extra safety margin?
- Q3 **`fill_prob=0.35` and `adverse_selection_bps=1.5` are priors.** Both MUST
  be G3-empirically calibrated across the liquidity-filtered universe before
  they are defensible defaults. OPEN — the exact minimum measured fill rate that
  "demonstrates passive fills" (§4) must be specified.
- Q4 The bridge from `fill_prob` to the `execution_mode` frontmatter enum is
  underspecified; confirm the enum values (`taker` / `maker`) match the
  `validate_strategy.py` `execution_mode` extension in PROP-001 §03.
- Q5 The fail-closed default means G0 must be able to invoke the G3 measured
  values for re-pricing; the data-flow from G3's queue-position results back into
  the G0 screen is not yet specified. OPEN.

## Review Date
Revisit after G3 fill-probability + adverse-selection calibration (2026-12-02).

## Related
- [[US-208-G0-Maker-Taker]] · [[US-165-Dynamic-Venue-Correct-Fees]] · [[PROP-001-§02]]
- [[ADR-008-G1-Size-Relative-Capacity-Power-Floor]] · [[ADR-010-G7-Paper-Hostile-Fill]]