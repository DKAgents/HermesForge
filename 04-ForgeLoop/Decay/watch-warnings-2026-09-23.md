---
date: 2026-09-23
check_type: Jev-powered decay detection (US-151)
source: jev_decay.check_all_active()
---

# Watch Warnings — 2026-09-23

Strategies flagged by Jev for monitoring (decay_prob > 45%, not yet at demote threshold 70%/60%):

| Strategy | Decay % | Concern |
|---|---|---|
| 🟡 NARROW_LEAD_BREADTH | 71% | High decay signal but breakdown confidence below demote threshold |
| 🟡 STR-20260726-eufearia-cci-reversal | 72% | Elevated decay — approaching danger zone |
| 🟡 STR-20260726-first-pullback-trend-swing | 82% | **Critical watch** — decay >80%, may demote next cycle |
| 🟡 STR-20260814-SECTOR-MOMENTUM | 75% | Sector rotation edge eroding |
| 🟡 STR-20260816-CRYPTO-FG-CONTRARIAN | 71% | Sentiment-based edge weakening |
| 🟡 STR-20260816-VIX-VRP-CONTANGO | 69% | Vol premium capture underperforming |
| 🟡 STR-20260903-BTC-LEVERAGE-FLUSH | 80% | **Critical watch** — decay >80%, may demote next cycle |
| 🟡 STR-A-ma-pullback-fibonacci | 56% | Moderate decay — monitor |
| 🟡 STR-C-breakout-volume | 71% | Volume breakout edge fading |
| 🟡 STR-D-sr-role-reversal | 58% | Moderate — approaching watch boundary |
| 🟡 STR-E-rsi-mean-reversion | 73% | Mean reversion edge weakening |
| 🟡 STR-F-bollinger-squeeze-breakout | 64% | Squeeze breakout losing edge |
| 🟡 STR-GOLD-LEAD | 72% | Gold-leading signal decaying |
| 🟡 STR-NVDA-LEAD | 76% | NVDA leadership signal eroding |
| 🟡 STR-VIXFG-DIVERGENCE | 71% | VIX/FG divergence weakening |
| 🟡 scanner_crypto_deleveraging_breakout | 70% | Deleveraging scanner underperforming |
| 🟡 scanner_skew_crosssectional | 65% | Cross-sectional skew fading |

## Already Demoted (previously handled)

These were flagged again today but already demoted in prior cycles:

- 🔴 STR-BTC-DOM: 86% (demoted 2026-09-21)
- 🔴 STR-EBE-DISPERSION: 83% (demoted 2026-09-21)
- 🔴 STR-W-stocks: 89% (demoted 2026-09-22)
- 🔴 STR-YIELD-SURGE: 85% (demoted 2026-09-22)
- 🔴 scanner_overnight_drift: 82% (demoted 2026-09-22)

## Healthy (no action)

39 strategies with decay < 45% — no action needed.

## Unknown (Jev leave-last-state)

- STR-OP-MR-CRYPTO-MEAN-REVERSION: 0% → unknown (no trade data or Jev error)
- STR-QW-crypto: 0% → unknown
- scanner_lowcorr_regime: 0% → unknown