---
hypothesis_id: HYP-22
source: internal (funding -> continuation, cross-regime)
venue: hyperliquid
instruments: native HL perps (dex == '')
horizon: 1d and 5d hold
entry: LONG high-positive-funding coins; SHORT high-negative-funding coins (continuation/momentum direction — FOLLOW the crowd, NOT fade)
exit: next rebalance / N-day hold
expected_gross_edge_bps: unknown (measured); the question is net, not gross
cost_hurdle_bps: 45 fail-closed + EXPLICIT funding cost (longs pay positive funding, shorts receive it)
data_dependencies: HF funding (~/.hermes/market_data/hl_funding_hf/, funding_rate+premium, 3.5y) + OI/mark for returns (~/.hermes/market_data/hl_oi_hf/)
counterparty: the funding-crowd (leveraged longs/shorts) whose crowding is the continuation fuel; honest note — the follower PAYS funding to the crowd, so net must beat that cost
topic: general
confidence: medium
---

# HYP-22 — Funding continuation momentum (directional)

## Motivation

Two independent results converge on ONE robust finding: funding extremes ->
CONTINUATION, not unwind. HYP-17 (funding extremes followed by continuation, the
fade lost money) and the funding-carry post-mortem (directional carry = fading the
crowd = fighting momentum = stopped out 20-39x) both point the same way. The
MIRROR is untested as a tradable signal: FOLLOW the crowd instead of fading it.

User clarification honored: directional is acceptable; the bar is NET positive
(not delta-neutral). This is a directional strategy by design.

## Pre-registered operationalization (fixed; no tuning)

- Signal: hourly funding_rate, resampled to daily (last rate of the day).
- H1 (confirm continuation is REGIME-ROBUST — the confirmation the old ~400d
  slice couldn't give): conditional on extreme |funding| (coin's top-decile of
  trailing 90d AND/OR cross-sectional top-decile), is the sign of the next 1-5d
  return = sign of funding (positive funding -> up)? Report per regime
  (bull/bear/flat) so we can finally say whether continuation is universal or a
  single-regime artifact.
- H2 (tradeable NET): long top-decile funding, short bottom-decile. **Net =
  price return - funding PAID (longs pay positive funding, shorts receive) -
  taker fees (4.5bps/leg realistic; also report 45bps).** The funding cost is
  the whole point — a follower pays the crowd to ride momentum, so NET must
  beat the carry cost + fees to be harvestable.

## Falsification (kill rules)

- H2 KILL: net (after funding + fees) <= 0, OR G4 CPCV 10th-pct PF < 1.0 /
  G5 PBO > 0.30 / DSR < 0.95.
- H1 is reported (regime-robust continuation or single-regime artifact), not
  a promotion criterion on its own.

## Notes

- The real question is NOT "is there signal" (HYP-17 already says the direction
  is real) — it is "is the momentum NET-harvestable after paying the funding
  carry + fees, and is it regime-robust."
- Base rate remains low; a null here closes funding-continuation as a tradeable
  directional edge on real multi-regime data.