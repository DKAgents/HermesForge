---
hypothesis_id: HYP-32
source: internal (first on-chain/flow test — the untested data class)
venue: cross-sectional (BTC/ETH + majors)
instruments: BTC/ETH (and majors where the flow metric resolves)
horizon: weekly (on-chain flow is slow/lagging)
signal: stablecoin supply growth (mint/burn) + aggregate TVL change -> subsequent price
data_dependencies:
  - stablecoin supply: DefiLlama free API (historical, years) — BACKFILL
  - TVL: DefiLlama free API (historical) — BACKFILL
  - price: existing HL mark/oracle + HF candles
cost_hurdle_bps: realistic taker + funding (slow weekly signal, low turnover)
counterparty: the capital rotating into/out of crypto (stablecoin minters + TVL providers)
topic: structural (flow/macro)
confidence: low (untested class; macro flow is correlated-with-price, not obviously causal or leading)
has_quotes: false
tags: []
---
# HYP-32 — On-chain/stablecoin flow predicts subsequent price

## Motivation

The one data class we have never tested: ON-CHAIN flow. Stablecoin supply growth
(new dry powder minted) and TVL change (capital entering DeFi) are the ecosystem's
capital-flow signals — in principle LEADING price (capital arrives before it
bids). This is genuinely different from the price/positioning/derivatives data
that all came back null.

## Pre-registered operationalization (fixed)

- H1 STABLECOIN SUPPLY: does a sustained increase in aggregate stablecoin supply
  (7d/30d growth rate) predict subsequent BTC/ETH price appreciation at a weekly
  horizon? Test growth -> forward return (and whether it is LEADING or merely
  coincident).
- H2 TVL: does aggregate TVL growth predict subsequent price?
- Cost: weekly rebalance, realistic taker + funding (low turnover, so cost is
  secondary to signal strength).
- Universe: BTC/ETH (the macro flow should hit the majors first).

## Prior (recorded)

On-chain/macro flow is the least-validated frontier — treat as likely null. The
specific risk: stablecoin supply + TVL are CORRELATED WITH price (they grow in
bull markets), so the test must separate a LEADING signal (flow predicts future
return) from mere COINCIDENCE (flow is a lagging echo of price). A coincident
signal is not tradeable, whatever its correlation.

## Falsification / promotion

- Promote only if the flow metric predicts forward return at a horizon that is
  (a) LEADING not coincident (flow at t predicts return t+1, not just correlates
  with return t), (b) net-positive after cost, (c) robust (G4/G5). A coincident
  correlation is reported honestly and NOT promoted.

## Note

DefiLlama provides FREE deep history for stablecoin supply + TVL — backfillable.
This is a MACRO on-chain test (aggregate flow), not per-coin exchange netflow
(which is paid-tier Glassnode/CryptoQuant — flag if that becomes necessary).