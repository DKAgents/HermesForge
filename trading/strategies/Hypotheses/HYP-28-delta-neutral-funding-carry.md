---
hypothesis_id: HYP-28
source: internal (structural carry class — the documented-persistent flagship)
venue: hyperliquid
instruments: native perps with LIQUID SPOT hedge — BTC-PERP, ETH-PERP, SOL-PERP (and any other major with real spot)
horizon: holding days-weeks while funding is sustained; exit when the gate clears
signal: sustained elevated funding — rolling 24h mean APR >= 8% AND >= 75% of hours in window positive
data_dependencies:
  - funding: ~/.hermes/market_data/hl_funding_hf/*.parquet (hourly funding_rate + premium)
  - mark + oracle: ~/.hermes/market_data/hl_oi_hf_clean/ (mark_price + oracle_price, for the BASIS = mark-oracle and the hedge accounting)
cost_hurdle_bps: MAKER fills both legs (0.015%/leg per the cost model); taker is treated as a break-even halving, reported separately
counterparty: leveraged longs paying the funding premium to hold leverage without hedging
topic: structural (carry)
confidence: low-medium (flagship prior, but skill warns it "lies too" — funding vs basis must be decomposed)
---

# HYP-28 — Delta-neutral funding carry (cash-and-carry) on liquid-spot majors

## Motivation

The one documented-persistent structural edge: collect positive funding by
shorting the perp while holding the spot (delta-neutral cash-and-carry). The
counterparty is the leverage crowd, structurally willing to keep paying as long
as they want exposure. This is the flagship the gauntlet has flagged but never
tested cleanly with the funding + mark + oracle data now in hand.

## Pre-registered operationalization (fixed)

- Gate: enter short-perp + long-spot ONLY when funding is SUSTAINED — rolling
  24h mean APR >= 8% AND >= 75% of the window's hours positive (a single
  reading does NOT qualify). Exit when the gate clears.
- Instrument: native perps with a LIQUID spot hedge (BTC/ETH/SOL; a coin without
  real spot has no executable delta-neutral hedge — exclude it).
- Hedge: long spot (proxy = oracle_price for the majors; the mark-oracle BASIS is
  the residual risk, tracked explicitly).
- H1 FUNDING component: net funding received on the short-perp leg, minus MAKER
  fees on both legs. Is it positive after fees?
- H2 BASIS decomposition (the skill's "it lies too" check): separate funding from
  basis (mark-oracle drift). Quote each separately — a "funding carry" whose net
  is majority BASIS is not a funding edge.
- Cost: MAKER fills both legs (0.015%). Report taker separately (the skill: taker
  roughly DOUBLES the breakeven funding rate, so taker is expected to break it).
- Forward: the assetCtxs daemon already accumulates mark/oracle/funding/OI for the
  basis to keep validating entry/exit forward.

## Prior (recorded)

The carry is the flagship BECAUSE the mechanism is structural and persistent; but
the skill carries hard-won cautions: it is only executable where liquid spot
exists (the hedge), it nets positive only under MAKER fills, and the apparent
"funding edge" is often contaminated by a BASIS proxy. This test decomposes
funding vs basis and applies the maker-fill + liquid-hedge constraints honestly.

## Falsification / promotion

- Promote only if the FUNDING component (not basis) is net-positive after maker
  fees on the majors, with the gate honored. A funding edge that survives only on
  taker fills, or that is majority basis, is not a real carry edge.

## Note

This is the flagship test — the carry class either produces the persistent
structural number the prior expects, or it decomposes to basis/fee and we retire
the "flagship" label with the honest number.