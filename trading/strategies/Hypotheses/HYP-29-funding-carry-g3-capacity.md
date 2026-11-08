---
hypothesis_id: HYP-29
source: internal (HYP-28 G3 fill-realism + capacity gate — the "harvestable?" question)
venue: hyperliquid
instruments: native perps with liquid spot — BTC-PERP, ETH-PERP, SOL-PERP (long-spot hedge + short-perp)
horizon: holding while funding-gated (churns ~48-59/yr)
signal: delta-neutral funding carry (per HYP-28: base funding floor 10.95% APR)
data_dependencies:
  - funding: ~/.hermes/market_data/hl_funding_hf/*.parquet
  - mark + oracle: ~/.hermes/market_data/hl_oi_hf_clean/
  - fill-depth: ~/.hermes/market_data/hl_liquidations_hf/data/fills + (optional) trades for depth estimate
cost_hurdle_bps: realistic on BOTH legs (short-perp taker/maker + long-spot taker/maker + spread)
counterparty: same as HYP-28 (the leverage crowd paying the funding floor)
topic: structural (carry execution)
confidence: medium (positive prior from HYP-28, but this is the gate where the class historically dies)
has_quotes: false
tags: []
---
# HYP-29 — Funding carry: G3 fill-realism + capacity gate

## Motivation

HYP-28 established the delta-neutral funding carry is REAL (~15–21% unlevered APR,
funding-true, maker survives, taker degrades-but-survives). But it hedged with the
oracle PRICE (mid) and never proved the spot leg fills at quoted prices, nor how
much notional the funding floor can absorb. This is the "is it actually
harvestable" gate — the exact stage where every other real gross signal died.

## Pre-registered operationalization (fixed)

- G3 FILL-REALISM on BOTH legs: grade the carry (short-perp + long-spot) through
  optimistic (mid) / realistic (queue/same-side adverse) / pessimistic (taker +
  adverse) fills. The load-bearing check is the HEDGE leg: buying spot at the
  ASK and selling at the BID, i.e. the spot round-trip spread — does that adverse
  spread (not just the fee) eat the funding, given the ~48–59 churns/yr?
- The perp leg's own entry/exit fill: short at the bid, cover at the ask.
- CAPACITY: estimate the notional ceiling before the funding floor compresses,
  using a CONservative liquidity proxy (e.g. a fraction of the market's daily
  notional volume / spot depth). Report the ceiling in USD and the APR at that
  ceiling, honestly flagged as an estimate (no L2 spot book is held).
- RISK CHECK (why is the floor 11%?): enumerate the uncompensated risks the
  market could be charging for — hedge basis drift (mark-oracle), exchange/custody
  risk, the churn's forced-fill cost. Quote each.

## Prior (recorded)

The carry is real; the open question is executability. The two death modes to
test honestly: (a) the spot hedge's adverse round-trip spread + churn blows up
the ~15–21% headline, or (b) capacity is so thin the floor only yields on pocket
notional. A carry that survives realistic fills on both legs AND yields on
meaningful notional is a genuine tradeable result.

## Falsification / promotion

- If the ~15–21% APR survives realistic/pessimistic fills on both legs at a
  capacity ceiling that is not trivially small, the carry clears its execution
  gate -> moves to paper-forward + forward accumulation (the promotion path).
- If the hedge spread + churn turns it net-negative, or capacity is pocket-sized,
  the carry is real-but-not-harvestable -> it is retired as a tradeable edge and
  recorded honestly as a structural yield one cannot capture at scale.

## Note

This is the decisive execution test on the one real, persistent edge found. The
carry either earns the paper-forward promotion or is retired with the honest
"real yield, can't harvest it" number.