---
type: insight
date: 2026-09-07
actionability: 5
connection_type: confirms_risk_rule
domains: [concepts, risk-guidelines, rules]
sources: ["C065-previous-support-as-future-resistance-in-downtrend", "EN069-price-gaps-as-support-and-resistance-for-timing", "RG035-combining-technical-factors-with-money-management-for-stop-p"]
seed_id: support_stop_sizing
tags: [insight, discovery, knowledge-evolution]
---

# Role Reversal and Gaps as Stop-Level Anchors for Position Sizing

## Discovery Summary

The concepts note on previous support becoming resistance in a downtrend (C065) and the rules note on price gaps as support/resistance (EN069) provide concrete technical levels where stops can be placed. The risk guideline RG035 requires that protective stops be placed at valid technical levels and links stop distance to position size via a fixed percentage risk rule. Together, they form a complete decision chain: identify a violated support level or a gap as the new resistance (for shorts), place the stop just above that level, then calculate position size so that the dollar risk equals a set percentage of account equity.

## Trading Implication

A trader should explicitly map recent role-reversal levels and unfilled gaps as stop-anchoring points, then derive position size using the formula: shares = (account_risk_dollar)/(entry_price – stop_price). This replaces discretionary stop placement with a rule-based sizing method.

## Supporting Notes

- [[C065-previous-support-as-future-resistance-in-downtrend]]
- [[EN069-price-gaps-as-support-and-resistance-for-timing]]
- [[RG035-combining-technical-factors-with-money-management-for-stop-p]]

## Connection Type

**confirms_risk_rule** — Actionability score: 5/5
