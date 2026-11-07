---
hypothesis_id: HYP-21
source: internal (builds on HYP-20's validated single-factor signal)
venue: hyperliquid
instruments: native HL perps (dex == '')
horizon: daily rebalance; 5d holding reported separately
entry: composite cross-sectional rank = equal-weight sum of per-factor z-scores; long top-decile, short bottom-decile
exit: next rebalance
expected_gross_edge_bps: target > 45 (the single-factor HYP-20 was +11-13 gross, below friction)
cost_hurdle_bps: 45 (both legs, fail-closed taker)
data_dependencies: HF OI dataset (~/.hermes/market_data/hl_oi_hf/); funding store (~405d x 35 coins) if usable
counterparty: cross-sectional relative-value repricing across the perp complex
topic: general
confidence: medium
has_quotes: false
tags: []
---
# HYP-21 — Multi-factor cross-sectional positioning composite

## Motivation

HYP-20 found a REAL but weak signal: cross-sectional 7d OI-change predicts relative
returns gross (+11-13 bps, momentum direction, corr 0.13 with price momentum — so
genuinely distinct) but is erased by turnover cost. Hypothesis: independent
positioning dimensions COMPOUND into a composite strong enough to clear the 45bps
hurdle.

## Pre-registered factors (each cross-sectionally z-scored DAILY)

1. **OI-change** — trailing 7d OI % (log) change (the validated signal).
2. **OI-level** — OI vs its own trailing 90d mean (z-score), cross-sectionally
   ranked ("how crowded is this coin relative to its norm AND relative to peers").
3. **Funding** — current funding rate, cross-sectionally ranked (IF usable; HYP-20
   flagged 57% ties at HL default — if still degenerate, report the composite
   WITHOUT funding and note it honestly).
4. **Price-momentum (7d)** — included as a CONTROL factor.

## Composites (both pre-committed, reported separately)

- **C-positioning (no price):** z(OI-change) + z(OI-level) [+ z(funding) if usable].
- **C-all:** C-positioning + z(price-momentum).

## Falsification (kill rules)

- KILL if neither composite produces a top-minus-bottom spread that is POSITIVE
  net of 45bps both-legs fail-closed taker, OR G4 CPCV 10th-pct PF < 1.0 /
  G5 PBO > 0.30 / DSR < 0.95.
- Report the per-factor contribution so we can see whether any composite edge
  comes from the NEW positioning dimensions or just re-introduces price momentum
  (which xsmom already failed on robustness).

## Notes

- This is the natural next test of the cross-sectional direction HYP-20 validated.
- Equal-weight z-score composite is the non-overfit default (no learned weights).
- Base rate remains low; a null here closes multi-factor cross-sectional
  positioning, not the whole search.
