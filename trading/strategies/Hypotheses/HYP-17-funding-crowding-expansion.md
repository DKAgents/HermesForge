---
hypothesis_id: HYP-17
source: human (coach-derived proxy)
venue: hyperliquid
instruments: top-35 HL perps by funding-store coverage
horizon: 1d bars; forward return 1-5 bars
trigger: |funding| >= 90th percentile of the coin's trailing 90d distribution (extreme EITHER direction)
outcome: mean absolute forward return (1-5 bars) extreme-funding regime vs unconditional
expected_gross_edge_bps: claimed positive (crowding -> big move); measured, not assumed
cost_hurdle_bps: 45 (single-leg 4x taker)
data_dependencies: HL funding store (~400d, 35 coins) + HL 1d bars (~4y, 31 coins) + OKX mark proxy
counterparty: the crowded side forced to unwind when positioning becomes extreme — their forced exit is the move.
---

# HYP-17 — Crowding (extreme funding) predicts big moves (proxy for the coach's OI claim)

## Why a proxy

The coach's kernel is "OI particularly high -> price ripe for a big move." Exact
OI history is AWS-gated (HYP-16). But the *underlying* thesis is "crowded
positioning -> volatility expansion," and we already hold ~400d of free HL
funding history — extreme funding is ALSO a crowding signal. This tests the
thesis, not the exact OI recipe.

## Pre-registered operationalization (fixed; no post-hoc tuning)

- **Crowding trigger:** `|funding| >= 90th percentile of the coin's trailing 90d`
  — extreme in EITHER direction (crowded longs OR crowded shorts), matching
  "particularly high positioning."
- **Primary outcome (H1, expansion):** mean |return| over the next 1-5 bars in
  the extreme-funding regime vs the unconditional full-sample mean.

## Sub-hypotheses

- **H1 — expansion ("ripe for a big move"):** extreme-funding regime's mean
  |forward return| is materially LARGER than unconditional. This is the coach's
  claim, proxied by funding.
- **H2 — directional unwind (labeled exploratory):** extreme POSITIVE funding
  -> negative forward return (crowded longs unwind); extreme NEGATIVE funding ->
  positive forward return (crowded shorts squeeze), net of fees. NOTE: HYP-01
  already tested fading-extreme-funding profitably and FAILED on friction, so H2
  net-of-fees is expected to fail — record the GROSS expansion regardless.

## Falsification criteria (kill rules)

- H1 KILL: extreme-funding regime's mean |move| is NOT statistically larger than
  unconditional (no crowding->volatility signal) -> the coach's kernel fails.
- H2 KILL: net-of-fees directional expectancy <= 0 (confirms HYP-01 — the
  crowding-to-volatility part is informative, but not a tradable directional edge
  at this tier).

## Notes

- This is a PROXY (funding, not OI). A pass here supports the thesis but does not
  replace the faithful OI test (HYP-16) once AWS/forward-accumulation is ready.
- Funding is directional crowding (long/short imbalance); OI is total positioning.
  Related, not identical.