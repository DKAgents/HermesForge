---
type: decay-watch
date: 2026-09-21
engine: jev
count: 17
---

# Watch Warnings — 2026-09-21

Strategies crossing the watch threshold (decay_prob > 0.45) but below demotion (≤0.70 or breakdown < 0.60).

| Strategy | Decay % | Notes |
|----------|---------|-------|
| NARROW_LEAD_BREADTH | 71% | — |
| STR-20260726-eufearia-cci-reversal | 71% | — |
| STR-20260726-first-pullback-trend-swing | 81% | ⚠️ Near demote zone — re-check urgently |
| STR-20260814-SECTOR-MOMENTUM | 75% | ⚠️ Near demote zone |
| STR-20260816-CRYPTO-FG-CONTRARIAN | 72% | — |
| STR-20260816-VIX-VRP-CONTANGO | 68% | — |
| STR-20260903-BTC-LEVERAGE-FLUSH | 78% | ⚠️ Near demote zone |
| STR-A-ma-pullback-fibonacci | 56% | — |
| STR-C-breakout-volume | 71% | — |
| STR-D-sr-role-reversal | 59% | — |
| STR-E-rsi-mean-reversion | 73% | — |
| STR-F-bollinger-squeeze-breakout | 64% | — |
| STR-GOLD-LEAD | 72% | — |
| STR-NVDA-LEAD | 75% | ⚠️ Near demote zone |
| STR-VIXFG-DIVERGENCE | 71% | — |
| scanner_crypto_deleveraging_breakout | 70% | — |
| scanner_skew_crosssectional | 65% | — |

## Action

- **No file moves** — these remain active
- **Escalation path**: re-check next decay cycle; if any cross decay > 0.70 AND breakdown > 0.60, demote
- **⚠️ = 75%+**: priority re-check — likely demotion candidates next cycle