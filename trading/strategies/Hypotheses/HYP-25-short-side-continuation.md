---
hypothesis_id: HYP-25
source: internal (HYP-24 short-leg finding)
venue: hyperliquid
instruments: native HL perps (dex == '') above a liquidity floor
horizon: target-dependent (3R target, 2x ATR stop)
entry: SHORT the cross-sectional 7d-momentum bottom-decile (losers) — short-only, one-sided
stop: 2x ATR
target: 3R
cost_hurdle_bps: realistic 4.5bps/leg taker + funding (shorts pay negative funding) + adverse entry slip + liquidity gate
data_dependencies: HF OI/mark (~/.hermes/market_data/hl_oi_hf/); funding (~/.hermes/market_data/hl_funding_hf/)
counterparty: the forced/unwilling holders of decaying coins (catch-the-falling-knife buyers of names in persistent decline)
topic: general
confidence: low-medium
---

# HYP-25 — Short-side continuation (short the decaying losers), gated on shortability

## Motivation

HYP-24's leg decomposition found a REAL, control-beating asymmetry: SHORT the
bottom-decile momentum losers shows +0.20R above the zero-drift geometric control
(losers keep decaying), while the LONG leg (winners) is -0.125R below control
(mean-revert). Downside continuation is genuine; upside is mean-reversion.

The CAVEAT that separates this from a win: shorting the bottom decile means
shorting tiny/illiquid/dying coins. The effect may live entirely on names you
cannot actually borrow, fill, or hold (delistings). HYP-25 tests whether the edge
SURVIVES the shortability gates.

## Pre-registered operationalization (fixed)

- Signal: cross-sectional 7d momentum; SHORT ONLY the bottom-decile.
- SHORTABILITY GATE (the crux): restrict the short universe to LIQUID names —
  e.g. coins above a minimum trailing open-interest (or OI rank) floor, the coins
  you can actually fill a short on. Document the floor.
- Cost: realistic 4.5bps/leg taker + FUNDING (shorts pay when funding<0) +
  adverse entry slip; G3 fill-realism on the (post-floor) illiquid tail.
- Report: (a) net multi-R of the short leg on the FULL bottom-decile vs (b) the
  same leg restricted to the LIQUID floor — the gap is whether the +0.20R edge
  lives on tradeable names or only on the un-shortable dying tail.
- Zero-drift synthetic control runs alongside; discount any residual that the
  control reproduces.

## Falsification

- If the +0.20R short edge VANISHES when restricted to liquid/shortable names
  (i.e. it lived only on the illiquid/dying tail), it is not harvestable -> close
  short-continuation as a tradeable edge.
- If it SURVIVES the floor + realistic fills + funding, promote as a real
  candidate (subject to G4/G5 robustness).

## Note

This is the honest adjudication of the one real asymmetry the momentum work
produced: short-the-losers. The whole question is whether it is tradeable-on-
liquid-names or a geometry-of-dying-coins artifact you cannot actually file.