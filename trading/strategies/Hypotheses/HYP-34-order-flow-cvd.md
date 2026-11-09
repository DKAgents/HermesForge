---
hypothesis_id: HYP-34
source: internal (order-flow imbalance / microstructure — short-horizon continuation)
venue: hyperliquid (tick trades already on disk)
instruments: BTC/ETH (+ majors)
horizon: intraday to 1d (short-horizon continuation)
signal: CVD (cumulative volume delta = aggressive buy − aggressive sell) and its rate-of-change
data_dependencies:
  - tick trades: ~/.hermes/market_data/hl_liquidations_hf/ or the trades dataset (5.8GB) — aggressor side (buy/sell) already present
  - bars: existing 5m (hl_bars/bars_5m.db) + hourly marks
cost_hurdle_bps: realistic taker + funding (intraday turnover is the binding cost)
counterparty: the passive/maker side providing liquidity to aggressive flow
topic: microstructure
confidence: low-medium (order-flow imbalance is a documented short-horizon predictor, but it is crowded + cost-sensitive)
has_quotes: false
tags: []
---
# HYP-34 — Order-flow imbalance (CVD) predicts short-horizon continuation

## Motivation

A flow-direction signal we already hold the raw for but never aggregated: the
tick trades carry aggressor side (buy/sell) + dir (Open Long/Short). Cumulative
volume delta (aggressive buy − sell) is the classic microstructure predictor of
short-horizon continuation — buy pressure -> up. Genuinely different from the
daily LEVEL signals that all came back null.

## Pre-registered operationalization (fixed)

- Signal: CVD (cumulative buy − sell notional per bar) and its change over a
  short window. A sustained CVD imbalance in one direction predicts same-direction
  continuation over the next N bars (intraday to 1d).
- Cost: realistic taker + funding. Intraday turnover is the binding constraint —
  report whether the signal clears it.

## Prior (recorded)

Order-flow imbalance is real + short-horizon, but it is EXACTLY what market
makers are paid to absorb, so it is crowded and cost-sensitive. Likely positive
gross, negative net after taker cost — test whether a slower (1d) version or a
maker-side capture survives.

## Falsification / promotion

- Promote only a net-positive, robust cell. If CVD is positive gross but dies at
  taker cost (as prior expects), report honestly: it is a real microstructure
  signal that is the market-maker's edge, not a taker's.

## Note

Data is already on disk (tick trades + 5m bars) — no new feed, just aggregation.