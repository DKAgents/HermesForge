---
hypothesis_id: HYP-26
source: internal (first structural class — forced liquidation flow; new data)
venue: hyperliquid
instruments: native HL perps (dex == '') above a liquidity floor
horizon: 1d and 5d forward returns
signal: net liquidation flow = (forced-buy notional − forced-sell notional) per market per day
data_dependencies:
  - liquidations: ~/.hermes/market_data/hl_liquidations_hf/ (events/ + fills/, 2025-05-25 -> 2026-10-31)
  - marks/OI: ~/.hermes/market_data/hl_oi_hf_clean/ (cleaned)
cost_hurdle_bps: realistic 4.5bps/leg taker + funding + adverse slip
counterparty: the forced closing of over-leveraged counterparties (margin-call flow)
topic: structural
confidence: low (prior is mixed-direction)
---

# HYP-26 — Liquidation flow predicts subsequent return (cascade vs exhaustion)

## Motivation

Liquidations are FORCED (involuntary) flow — margin-call selling/buying that is
mechanically obressive to price, unlike discretionary positioning. This is the
first structural data class available to us. Two competing mechanisms, both
economically motivated:

- H1 CASCADE / continuation: a wave of forced selling pushes price down, which
  triggers the next liquidation — self-reinforcing. Net forced flow -> same-
  direction continuation.
- H2 EXHAUSTION / reversal: forced flow is involuntary; once it completes, the
  pressure is spent and price reverts (the "long-squeeze bottom"). Net forced
  flow -> opposite-direction reversal.

## Pre-registered operationalization (fixed)

- Flow: aggregate liquidation FILLS to daily per-market NET flow = (buy notional
  − sell notional). A long-liquidation is closed by sells (downward pressure);
  a short-liquidation by buys (upward pressure). Cross-sectional rank so large
  books (BTC) don't dominate by raw size.
- Test BOTH directions (pre-registered as two arms):
  - H1 continuation: rank of net flow predicts same-sign forward return.
  - H2 reversal: rank of net flow predicts opposite-sign forward return.
- Horizon: 1d (cascade) and 5d (exhaustion) forward returns, non-overlapping.
- Universe: native perps, liquidity floor (drop un-tradeable/delisted tail).
- Cost: realistic 4.5bps/leg taker + funding + adverse slip.
- Zero-drift control where relevant (recognize any geometric/flow-size artifact).

## Prior (recorded)

The cascade is intraday and mechanical; the exhaustion is multi-day and completes.
Both are well-known and partially priced. Net-tradeable edge at the DAILY horizon
is unlikely after cost — but this is the first time we can measure it on real
forced-flow data rather than assume it.

## Falsification / promotion

- Report H1 vs H2 net multi-R at 1d and 5d, with the winning arm's robustness.
- Promote only a cell that is economically motivated, beats any control, has
  adequate sample, and survives G4/G5. If neither arm clears net-of-cost, the
  forced-flow class is tested-and-null at tradeable horizon (the cascade is real
  but not harvestable daily).

## Note

This is the first test of the liquidation data. The honest question is not just
"does liquidations predict" but "does forced-flow alpha survive the daily
horizon + cost where the cascade is already known and fast."