---
type: insight
date: 2026-08-31
actionability: 4
connection_type: contradicts_assumption
domains: [concepts, risk-guidelines, rules]
sources: ["C245-stop-order", "RG035-combining-technical-factors-with-money-management-for-stop-p", "EN071-pivot-point-buy-signal-rules"]
seed_id: prior_swing_low_stop
tags: [insight, discovery, knowledge-evolution]
---

# Pivot Point Stops Clash with 3:1 Reward/Risk Money Management

## Discovery Summary

EN071-Pivot-Point-Buy-Signal-Rules mandate protective stops below today's low or today's open, producing a stop distance that may be wide. RG035-Combining-Technical-Factors-with-Money-Management-for-Stop-P requires stops at technical levels but also limits total risk (e.g., 5% of account). If the EN071 stop distance forces a risk per share that, when sized to the max risk, yields a tiny position size and a 3:1 reward target that exceeds typical volatility, the trade becomes unworkable—directly contradicting the assumption that any valid technical stop automatically supports fixed reward/risk ratios.

## Trading Implication

Before entering EN071 pivot point buys, calculate the EN071 stop distance; reject the trade if the required risk per share either violates the RG035 max risk limit or makes a realistic 3:1 target unattainable given the instrument’s average range.

## Supporting Notes

- [[C245-stop-order]]
- [[RG035-combining-technical-factors-with-money-management-for-stop-p]]
- [[EN071-pivot-point-buy-signal-rules]]

## Connection Type

**contradicts_assumption** — Actionability score: 4/5
