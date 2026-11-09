---
hypothesis_id: HYP-31
source: internal (structural carry cousin — cross-venue funding/basis spread)
venue: hyperliquid + okx (cross-venue)
instruments: BTC/ETH (liquid on both venues) — short the high-funding venue, long the low-funding venue (delta-neutral across venues)
horizon: holding days-weeks while the spread persists
signal: cross-venue funding spread (HL funding APR − OKX funding APR) + price basis (HL mark − OKX last)
data_dependencies:
  - HL funding: ~/.hermes/market_data/hl_funding_hf/*.parquet
  - OKX funding + ticker: ~/.hermes/market_data/cross_venue_basis/basis.db (okx_funding, okx_ticker) — BACKFILL deeper via OKX public funding/ticker history
cost_hurdle_bps: maker on BOTH venues + cross-venue risk (transfer/custody/liquidation on one leg) — flag explicitly
counterparty: the venue-specific funding demand (HL's leverage crowd vs OKX's)
topic: structural (carry)
confidence: low-medium (same mechanism as the validated HL carry, but cross-venue adds a hedge/transfer risk not yet priced)
has_quotes: false
tags: []
---
# HYP-31 — Cross-venue funding spread + price basis (HL vs OKX)

## Motivation

The HL funding carry validated because HL's base funding floor (~10.95% APR) is
venue-specific. If OKX's funding runs systematically LOWER, the SPREAD (HL − OKX)
is itself a harvestable carry: short the high-funding venue, long the low-funding
venue, delta-neutral across venues, collect the spread. Plus a second channel:
the cross-venue PRICE basis (HL mark vs OKX last) may mean-revert when it widens.

## Pre-registered operationalization (fixed)

- H1 FUNDING-SPREAD CARRY: when HL funding APR exceeds OKX funding APR by a
  sustained margin (rolling-mean spread above a pre-committed floor), short HL
  perp + long OKX perp (delta-neutral across venues), collect the spread; exit
  when the spread closes.
- H2 PRICE-BASIS MEAN-REVERSION: when |HL mark − OKX last| (basis bps) widens
  beyond a pre-committed band, fade it (expect convergence).
- Universe: BTC/ETH only (both venues liquid). No leverage beyond delta-neutral.
- Cost: maker on BOTH venues + the CROSS-VENUE RISK (transfer/custody/liquidation
  on one leg while the other runs) — this is the load-bearing honest unknown, not
  the fee.

## Prior (recorded)

The funding spread is the SAME mechanism as the validated HL carry, so a positive
prior is warranted — BUT the cross-venue hedge adds real risk (you hold offsetting
positions on two venues with transfer + liquidation asymmetry) that the HL-only
carry did not have. The honest test is whether the spread survives that hedge
risk + maker fees on both legs, not whether the spread exists (it does).

## Falsification / promotion

- Promote only if the spread, net of BOTH venues' maker fees + the cross-venue
  hedge risk, is positive and persistent. If the spread is too thin vs the
  two-venue cost, or the price basis doesn't mean-revert, the cross-venue channel
  adds nothing beyond the HL-only carry already validated.

## Note

Data is PARTIALLY accumulated (basis.db, ~days); the backtest must backfill OKX
funding/ticker history to match the HL funding depth before measuring the spread.