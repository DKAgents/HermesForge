---
type: insight
date: 2026-10-07
actionability: 3
connection_type: reveals_sequence
domains: [concepts, risk-guidelines, rules]
sources: ["RG023-pf-trailing-stop-adjustment", "C245-stop-order", "EN071-pivot-point-buy-signal-rules"]
seed_id: system_exit_design
tags: [insight, discovery, knowledge-evolution]
---

# Prioritize exit via pivot trailing stops

## Discovery Summary

Murphy's insight emphasizes exit over entry. EN071-pivot-point-buy-signal-rules provide entry triggers, but RG023-pf-trailing-stop-adjustment and C245-stop-order together create a systematic exit method. By trailing stops off pivot levels after a buy signal, a trader ensures exits are managed based on price structure rather than arbitrary levels, aligning risk management with price action.

## Trading Implication

After a pivot point buy signal, set an initial stop at the prior pivot low and trail it using the subsequent pivot highs or a moving average derived from pivots, shifting focus from entry timing to stop adjustment.

## Supporting Notes

- [[RG023-pf-trailing-stop-adjustment]]
- [[C245-stop-order]]
- [[EN071-pivot-point-buy-signal-rules]]

## Connection Type

**reveals_sequence** — Actionability score: 3/5
