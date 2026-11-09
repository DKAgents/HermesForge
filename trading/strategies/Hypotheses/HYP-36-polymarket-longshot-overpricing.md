---
hypothesis_id: HYP-36
source: internal (directive §8 — "NEW approach", cross-market pricing wedge; flagship)
venue: polymarket (prediction markets) vs deribit (options-implied fair value)
instruments: BTC/ETH threshold, range, and touch markets on Polymarket
horizon: hold-to-resolution (or exit-on-gap-close); maturity up to ~3 months
signal: Polymarket "Yes" price minus Deribit-implied European digital fair value; sell the
  overpriced Yes (buy No) when gap > threshold after fees/spread AND implied prob <= 20%
data_dependencies:
  - D-5: Polymarket public API (Gamma + CLOB) — market prices/trades/resolutions, free
  - D-6: Deribit IV surface — ~/.hermes/market_data/iv_surface/ (ATM IV + DVOL stored) and
    the full strike smile via the free Deribit public API (get_book_summary_by_currency)
cost_hurdle_bps: Polymarket no-Yes spread + CLOB fees, plus a capital charge at the carry
  benchmark (~3.21% idle USDC APY) for the locked-up holding period
counterparty: the overpaying retail longshot buyer (favorite-longshot bias, "Yes" bias),
  who cannot be arbitraged away because capital-constrained options-market arbs can't bridge
  the two venues
topic: structural (cross-market pricing wedge / behavioral longshot overpricing)
confidence: low-medium (two 2026 studies report the wedge widest at low probs + long maturity;
  but no independent reproduction, and harvestability at small-account capacity is unproven)
note: |
  RENUMBER COLLISION FLAG — the orchestrator's directive labeled this "HYP-28", but HYP-28 is
  already taken (delta-neutral funding carry). Rather than overwrite an existing pre-registration
  (data loss is unacceptable), this is registered as HYP-36 (next free number). If the directive
  intended to renumber the funding carry elsewhere, rename this file in one path-scoped commit.
---

# HYP-36 — Polymarket longshot overpricing vs options-implied probabilities

## Motivation

The flagship of the NEW approach (a cross-market pricing wedge, capacity-limited — ideal for a
small account). Retail prediction-market buyers systematically overpay for low-probability crypto
outcomes (favorite-longshot bias + a "Yes" bias). Capital-constrained options-market arbitrageurs
cannot close the gap between the two venues, so the mispricing persists. The other side of every
trade is the overpaying retail longshot buyer.

## Evidence (recorded)

Two 2026 studies (Portnaya, comparing Binance options vs Polymarket BTC threshold contracts; and a
Deribit-implied-distributions study) report Polymarket prices systematically ABOVE option-implied
risk-neutral values, widest at low probabilities and long maturities, amplified on weekends;
"above"/"range" bets tracked fair value better than "touch"/"dip". These are external claims to be
independently verified — I do not treat them as established fact.

## Pre-registered operationalization (fixed)

- Universe: BTC/ETH threshold, range, and touch markets on Polymarket.
- Fair value: European digitals from the Deribit IV smile via call spreads (Breeden-Litzenberger);
  touch markets priced as barriers (one-touch) — flagged separately since barrier pricing is model
  dependent.
- Signal: gap = Polymarket "Yes" price (prob space, 0..1) minus fair digital probability.
- Trade: sell overpriced Yes (buy No) when gap > pre-registered threshold after fees/spread, and
  implied prob <= 20% (the longshot bucket). Threshold = 5¢ (0.05 in prob space) net of fees.
- Variants (pre-registered):
  V1 hold-to-resolution vs V2 exit-on-gap-close;
  V3 unhedged vs V4 delta-hedged with an HL perp.
- Statistics: outcomes are correlated through the shared BTC/ETH price path — the effective sample
  is the number of DISTINCT (underlying, expiry) clusters, not the number of contracts. Cluster-robust
  inference (cluster by (underlying, expiry)).
- Capital cost: charge locked-up capital at the carry benchmark (~3.21% idle USDC APY) for the
  holding period.

## Prior (recorded)

The prior is that the longshot wedge is real and persistent because the counterparty is behavioral
(retail overpaying) and the arbitrage channel is capital-constrained. The skill cautions: (a) the
wedge must survive Polymarket's no-Yes spread and fees, (b) capital is locked to resolution, and
(c) the two studies are external and un-reproduced.

## Falsification / promotion

Promote only if the mean realized edge per $ at risk is > 0 after fees + capital charge, with a
cluster-robust CI that excludes 0, over >= 40 independent (underlying, expiry) clusters. A wedge
that is real in a single cross-section but not demonstrated over >= 40 independent expiry clusters,
or that vanishes after fees/spread/capital charge, is NOT promoted.

## Data-feasibility note (honest)

The Deribit IV smile and Polymarket current prices are pullable live (free APIs). However, free
Polymarket does not expose a full historical price time-series, and the stored iv_surface.db holds
only ATM IV + DVOL (~8 days, no smile history). The >= 40-cluster time-series falsification therefore
cannot be run on currently-stored data. Phase 1 (this run) is a LIVE cross-sectional snapshot of the
wedge + a data-feasibility verdict; Phase 2 (time-series falsification) is gated on a historical
Polymarket price feed (paid) + a smile-history store.
