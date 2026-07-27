---
type: insight
date: 2026-07-26
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
# Entry Triggers Double as Exit Anchors via Stop Sequencing

## Discovery Summary

EN071-pivot-point-buy-signal-rules defines a precise two-phase stop logic: a buy stop entry above the previous day's high is immediately paired with a protective sell stop below the current day's low — meaning the exit rule is structurally embedded in the entry rule itself. C245-stop-order (Murphy) establishes that stops serve dual roles: initiating positions on breakouts AND protecting profits when trailed upward. RG023-pf-trailing-stop-adjustment extends this into the trend continuation phase, specifying that once a position matures, the stop migrates to just below the latest O-column (P&F), creating a dynamic exit ladder. Together, the three notes reveal a sequential stop lifecycle — entry stop → immediate protective stop → trailed P&F structural stop — that operationalizes Murphy's principle that exits dominate performance.

## Trading Implication

At entry via EN071 pivot rules, immediately place the protective sell stop below the current day's low; as the trade develops and repeat P&F buy signals appear per RG023, migrate the stop to just below the latest O-column rather than holding the original day's-low stop, tightening protection without arbitrary price targets.

## Supporting Notes

- [[RG023-pf-trailing-stop-adjustment]]
- [[C245-stop-order]]
- [[EN071-pivot-point-buy-signal-rules]]

## Connection Type

**reveals_sequence** — Actionability score: 4/5
