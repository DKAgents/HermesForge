---
hypothesis_id: HYP-16
source: human (coach-derived)
venue: hyperliquid
instruments: BTC, ETH, SOL + top-30 HL perps by open interest
horizon: 1d bars; hold 1–5 bars
entry: long when coin OI is in the TOP DECILE (>= 90th pct of its trailing 90d) AND close > SMA20
exit: close < SMA20, or time-stop at 5 bars
expected_gross_edge_bps: claimed positive (via high-OI filter); measured, not assumed
cost_hurdle_bps: 45 (single-leg 4x taker)
data_dependencies: HL 1d bars (~4y, 31 coins) + OI history (HL funding/metaAndAssetCtxs store)
counterparty: the leveraged crowd at crowded (extreme-OI) positioning, forced to unwind when the move starts — their forced exit is the exit liquidity.
topic: general
confidence: high
has_quotes: true
tags: []
---
# HYP-16 — High-OI expansion + trend-following (coach-derived)

## Claim (verbatim intent)
> "OI particularly high -> price action is ripe for a big move."

The coach uses extreme OI to flag conditions ripe for a large move, and an
SMA/trend filter for direction. This is a POSITIONING signal, not a price-timing
one — the class the pipeline has NOT yet rejected, and the reason US-199/OI feed
was built.

## Pre-registered operationalization (fixed before running; no post-hoc tuning)

- **OI regime:** `OI in top decile (>= 90th percentile) of the coin's own trailing
  90d distribution` ("particularly high" = relative, not absolute, to normalize
  across coins).
- **"Big move" metric (H1):** absolute return over the next 1–5 bars vs the
  unconditional (full-sample) distribution.
- **Directional entry (H2):** long when `extreme OI AND close > SMA20`; exit when
  `close < SMA20` or 5-bar time stop.

## Two sub-hypotheses, tested separately

- **H1 (expansion / "ripe for a big move"):** conditional on extreme OI, the
  realized |return| over the next 1–5 bars is materially LARGER than the
  unconditional |return|. This tests the coach's claim directly — is high OI
  genuinely predictive of large moves?
- **H2 (directional alpha):** the extreme-OI + trend entry produces POSITIVE net
  expectancy (edge − taker − funding) out-of-sample and clears G4/G5.

## Falsification criteria (kill rules)

- H1 KILL: if the extreme-OI regime's mean |move| is NOT statistically larger
  (or the effect is < cost), the "ripe for a big move" claim is rejected.
- H2 KILL: net expectancy <= 0, OR G4 CPCV 10th-pct fold PF < 1.0, OR G5
  PBO > 0.30 / DSR < 0.95 -> rejected (no directional alpha; the SMA still
  contributes nothing).

## Data gate

If OI history is shallower than ~200d (or absent for enough coins), H1/H2 are
DATA-GATED, not failed — report that honestly and identify the OI-history
backfill needed (HL funding/metaAndAssetCtxs history endpoint). Do NOT fabricate
or proxy OI with price.