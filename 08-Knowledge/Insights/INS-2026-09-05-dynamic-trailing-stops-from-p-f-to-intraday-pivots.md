---
type: insight
date: 2026-09-05
actionability: 4
connection_type: confirms_risk_rule
domains: [concepts, risk-guidelines, rules]
sources: ["RG023-pf-trailing-stop-adjustment", "C245-stop-order", "EN071-pivot-point-buy-signal-rules"]
seed_id: system_exit_design
tags: [insight, discovery, knowledge-evolution]
topic: knowledge
confidence: high
has_quotes: false
source: unknown
---
# Dynamic Trailing Stops from P&F to Intraday Pivots

## Discovery Summary

Murphy's emphasis on exits over entries is operationalized by combining the P&F trailing stop method from RG023 with the specific stop placement rules in EN071. RG023 adjusts stops under the latest o-column in uptrends, while EN071 places protective stops below the current day's low after a pivot point breakout—both use recent structural lows to protect profits. This connection reveals that EN071's intraday stop rule can be dynamically trailed session-over-session using P&F column logic, rather than remaining static, directly confirming Murphy's principle.

## Trading Implication

After entering a long on EN071's pivot point buy signal above the previous day's high, replace the static protective stop under the current day's low with a dynamic trailing stop under each new P&F o-column low as the uptrend matures.

## Supporting Notes

- [[RG023-pf-trailing-stop-adjustment]]
- [[C245-stop-order]]
- [[EN071-pivot-point-buy-signal-rules]]

## Connection Type

**confirms_risk_rule** — Actionability score: 4/5

## Related Notes
- [[RG022-pf-stop-placement-rule|P&F Stop Placement Rule]]
- [[EN071-pivot-point-buy-signal-rules|Pivot Point Buy Signal Rules]]
