---
date: 2026-09-26
tool: jev_decay
total_checked: 56
demoted: 5
watch: 16
healthy: 33
unknown: 2
---

# Decay Check — 2026-09-26

## 🔴 Demoted (5)

| Strategy | Decay | Action | Notes |
|----------|-------|--------|-------|
| STR-BTC-DOM | 86% | Already demoted 2026-09-21 | csv-only; CSV still in results/ — archive it |
| STR-EBE-DISPERSION | 84% | Already demoted 2026-09-21 | csv-only; CSV still in results/ — archive it |
| STR-W-stocks | 88% | Already demoted 2026-09-21 | csv-only; CSV still in results/ — archive it |
| STR-YIELD-SURGE | 84% | Already demoted 2026-09-21 | csv-only; CSV still in results/ — archive it |
| scanner_overnight_drift | 82% | Already demoted 2026-09-21 | csv-only; CSV still in results/ — archive it |

⚠️ All 5 CSVs remain in `scripts/validation/results/` despite being demoted 5 days ago. They are re-checked every run, wasting Jev credits (~$0.006/run). Archive them to stop re-checking.

## 🟡 Watch (16)

| Strategy | Decay | Trend |
|----------|-------|-------|
| NARROW_LEAD_BREADTH | 71% | — |
| STR-20260726-eufearia-cci-reversal | 71% | — |
| STR-20260726-first-pullback-trend-swing | 83% | ↑ concern |
| STR-20260814-SECTOR-MOMENTUM | 73% | — |
| STR-20260816-CRYPTO-FG-CONTRARIAN | 72% | — |
| STR-20260816-VIX-VRP-CONTANGO | 68% | — |
| STR-20260903-BTC-LEVERAGE-FLUSH | 76% | — |
| STR-A-ma-pullback-fibonacci | 58% | — |
| STR-C-breakout-volume | 71% | — |
| STR-D-sr-role-reversal | 59% | — |
| STR-E-rsi-mean-reversion | 76% | — |
| STR-F-bollinger-squeeze-breakout | 65% | — |
| STR-GOLD-LEAD | 72% | — |
| STR-NVDA-LEAD | 74% | — |
| STR-VIXFG-DIVERGENCE | 71% | — |
| scanner_crypto_deleveraging_breakout | 68% | — |
| scanner_skew_crosssectional | 65% | — |

## 🟢 Healthy (33)

All remaining strategies below demotion (70%) and watch (45%) thresholds. Range: 12%–42%.

## ⚪ Unknown (2)

- STR-OP-MR-CRYPTO-MEAN-REVERSION: 0 trades → decay=0%, no data
- STR-QW-crypto: 0 trades → decay=0%, no data
- scanner_lowcorr_regime: 0 trades → decay=0%, no data

## Actions Required

1. **Archive demoted CSVs**: Move the 5 demoted CSV files out of `validation/results/` so they stop consuming Jev credits on every check.
2. **Watch STR-20260726-first-pullback-trend-swing**: At 83%, one more bad week could push it into demotion territory.
3. **Watch STR-E-rsi-mean-reversion** and **STR-20260903-BTC-LEVERAGE-FLUSH**: Both at 76%, above the 70% demotion threshold for decay but below the breakdown threshold.