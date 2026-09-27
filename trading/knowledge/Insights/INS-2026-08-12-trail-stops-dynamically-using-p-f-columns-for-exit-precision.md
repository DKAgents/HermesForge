---
type: insight
date: 2026-08-12
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
# Trail Stops Dynamically Using P&F Columns for Exit Precision

## Discovery Summary

RG023 provides a mechanical, chart-based rule for trailing stops using P&F column structure (below latest O column in uptrend, above latest X column in downtrend), while EN071 establishes intraday entry triggers using buy stops above prior highs with immediate protective stops below the current day's low. C245 confirms that sell stops can be trailed upward to protect profits. Together, these notes reveal a sequence: EN071 governs entry and initial stop placement, while RG023 governs how that stop should be dynamically trailed as the trend develops — answering Murphy's implicit thesis that the exit decision (when and how to trail) is more systematically addressable than entry.

## Trading Implication

Once an EN071 pivot-point buy signal is triggered and the initial protective stop is set below the current day's low, the trader should switch to RG023's P&F trailing stop methodology — raising the stop to just below the latest O column on each new repeat buy signal — rather than holding the original entry-day stop indefinitely.

## Supporting Notes

- [[RG023-pf-trailing-stop-adjustment]]
- [[C245-stop-order]]
- [[EN071-pivot-point-buy-signal-rules]]

## Connection Type

**reveals_sequence** — Actionability score: 4/5
