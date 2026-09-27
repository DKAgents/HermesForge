---
type: insight
date: 2026-08-16
actionability: 4
connection_type: reveals_sequence
domains: [concepts, risk-guidelines, rules]
sources: ["RG023-pf-trailing-stop-adjustment", "C245-stop-order", "EN071-pivot-point-buy-signal-rules"]
seed_id: system_exit_design
tags: [insight, discovery, knowledge-evolution]
topic: knowledge
confidence: high
has_quotes: false
source: unknown
---
# Trail Stops Using P&F Columns, Not Arbitrary Price Levels

## Discovery Summary

RG023 establishes a structured P&F-based trailing stop rule (below latest O-column in uptrends), while C245 confirms that sell stops can be trailed upward to protect profits. EN071 adds a time-based intraday pivot structure where protective stops are placed below current-day lows after entry. Together these form a multi-timeframe exit sequence: enter on pivot breakout (EN071), trail using intraday structure initially, then migrate to P&F column-based trailing stops (RG023) as the trend matures — operationalizing Murphy's insight that exits matter more than entries.

## Trading Implication

After a pivot point buy signal (EN071) is triggered and the position matures across multiple days, a trader should transition from the intraday protective stop (below current day's low) to the P&F trailing stop (just below the latest O-column per RG023), creating a systematically tightening exit that protects accumulated profits without arbitrary placement.

## Supporting Notes

- [[RG023-pf-trailing-stop-adjustment]]
- [[C245-stop-order]]
- [[EN071-pivot-point-buy-signal-rules]]

## Connection Type

**reveals_sequence** — Actionability score: 4/5

## Related Notes
- [[EN071-pivot-point-buy-signal-rules|Pivot Point Buy Signal Rules]]
