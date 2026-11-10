---
hypothesis_id: HYP-35
source: internal (copytrading reverse-engineering — the one clean mechanical rule from top HL traders)
venue: hyperliquid (xyz HIP-3 builder index-perp basket)
instruments: the xyz index-perp basket (identify the exact markets)
horizon: intraday — short in the 13:00–15:00 UTC window, cover ~2.6h later
signal: short the xyz index-perp in the 13–15 UTC window (reconstructed from 0x024294c53a: 75.6% win, 5.2:1, ~$1.05M realized)
data_dependencies:
  - xyz index-perp marks (HL HIP-3 builder market; identify exact market + fetch its candles via candleSnapshot)
  - the mechanism behind the 13–15 UTC window (funding settlement? index rebalance? — MUST be identified, not assumed)
cost_hurdle_bps: realistic taker + funding + the xyz market's wider HIP-3 spread
counterparty: the index-perp's arbitrage/marking counterparties in a specific daily window
topic: structural (intraday calendar window)
confidence: low (a specific intraday window with 5:1 on a modest sample is exactly the overfit signature; gate is mechanism-identification first)
has_quotes: false
tags: []
---
# HYP-35 — Short the xyz index-perp in the 13–15 UTC window

## Motivation

The one clean mechanical rule reconstructed from a genuine top HL trader
(0x024294c53a): short an `xyz` index-perp basket in the 13:00–15:00 UTC window,
cover ~2.6h later — 75.6% win, 5.2:1, $1.05M realized. This is the only
reverse-engineered candidate that is a RULE, not beta/MM/discretion.

## Pre-registered operationalization (fixed)

- FIRST GATE (blocking): identify the exact `xyz` index-perp market(s) and the
  MECHANISM behind the 13–15 UTC window. If it is a funding settlement, an index
  rebalance, or a mark-vs-oracle divergence — state it. If the mechanism cannot
  be identified, REPORT MECHANISM-UNKNOWN and do NOT backtest a bare "short at
  13:00" rule (that is data-mining an artifact).
- IF the mechanism is identified + economically motivated: short the index-perp
  in the 13–15 UTC window, cover ~2.6h later, across the available candle history.
- Cost: realistic taker + funding + the xyz HIP-3 market's wider spread (wider
  than a native perp — flag it).

## Prior (recorded)

A single intraday time-window with 5.2:1 R:R on a modest sample is the textbook
overfit signature — more likely a calendar/funding artifact than a persistent
edge. The mechanism must be identified and economically motivated BEFORE any
backtest; otherwise the honest verdict is "mechanism-unknown, not testable."

## Falsification / promotion

- Promote only if the mechanism is identified + the rule is net-positive + robust
  (G4/G5) on the available history. If the window is a funding-settlement artifact
  already priced, or the sample is too thin, report honestly and do not promote.

## Note

This is the sole surviving candidate from the copytracking reverse-engineering.
Treat the high win rate as a prior to be explained, not as evidence.