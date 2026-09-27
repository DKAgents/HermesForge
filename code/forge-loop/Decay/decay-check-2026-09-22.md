---
type: decay-check
date: 2026-09-22T00:00:00Z
engine: jev
total_checked: 56
demoted: 5
watching: 17
healthy: 32
unknown: 2
---

# Jev Decay Check — 2026-09-22

## Summary

| Category | Count | Δ from 09-21 |
|----------|-------|---------------|
| 🔴 Demoted | 5 | — |
| 🟡 Watching | 17 | — |
| 🟢 Healthy | 32 | — |
| ⚪ Unknown (no data) | 2 | — |
| **Total** | **56** | — |

Thresholds: decay_prob > 0.70 AND breakdown_prob > 0.60 → demote; decay_prob > 0.45 → watch.

No new demotions today. Same 5 as yesterday. All already processed — demotion notes exist, CSV-only (no .md files to move).

---

## 🔴 Demotions (5) — unchanged

| Strategy | Decay % | Status |
|----------|---------|--------|
| STR-BTC-DOM | 86% | Already demoted 09-21 |
| STR-EBE-DISPERSION | 84% | Already demoted 09-21 |
| STR-W-stocks | 88% | Already demoted 09-21 |
| STR-YIELD-SURGE | 85% | Already demoted 09-21 |
| scanner_overnight_drift | 82% | Already demoted 09-21 |

---

## 🟡 Watching (17)

| Strategy | Decay % | Δ from 09-21 |
|----------|---------|---------------|
| STR-20260726-first-pullback-trend-swing | 81% | — ⚠️ near demote |
| STR-20260903-BTC-LEVERAGE-FLUSH | 78% | — ⚠️ near demote |
| STR-NVDA-LEAD | 75% | — ⚠️ near demote |
| STR-E-rsi-mean-reversion | 74% | +1pp |
| STR-20260726-eufearia-cci-reversal | 73% | +2pp |
| STR-20260814-SECTOR-MOMENTUM | 72% | -3pp |
| STR-20260816-CRYPTO-FG-CONTRARIAN | 71% | -1pp |
| STR-C-breakout-volume | 71% | — |
| STR-GOLD-LEAD | 71% | -1pp |
| STR-VIXFG-DIVERGENCE | 71% | — |
| NARROW_LEAD_BREADTH | 70% | -1pp |
| STR-20260816-VIX-VRP-CONTANGO | 69% | +1pp |
| scanner_crypto_deleveraging_breakout | 69% | -1pp |
| STR-F-bollinger-squeeze-breakout | 65% | +1pp |
| scanner_skew_crosssectional | 65% | — |
| STR-D-sr-role-reversal | 59% | — |
| STR-A-ma-pullback-fibonacci | 57% | +1pp |

⚠️ = 75%+ decay — close to demotion threshold, re-check next cycle.

---

## 🟢 Healthy (32)

STR-20260728-adaptive-trend (35%), STR-20260906-BTC-SUPPLY-CRUNCH (23%), STR-20260906-SENTIMENT-DIVERGENCE (14%), STR-AA-stocks (31%), STR-AB-stocks (23%), STR-AC-stocks (27%), STR-AD-stocks (24%), STR-ADD-FACTOR (13%), STR-AE-stocks (39%), STR-AF-stocks (40%), STR-AG-stocks (19%), STR-AH-stocks (20%), STR-AI-stocks (30%), STR-AJ-stocks (30%), STR-B-macd-histogram-divergence (27%), STR-B-stocks (43%), STR-CAP-BOTTOM-CRYPTO-CAPITULATION-BOUNCE (25%), STR-DEBASEMENT (37%), STR-FOMC-CERTAINTY (37%), STR-G-relative-strength-rotation (24%), STR-OIL-SHOCK (27%), STR-Q-crypto (23%), STR-Q-stocks-deep (23%), STR-Q-stocks (27%), STR-R-crypto (34%), STR-R-stocks (33%), STR-S-stocks (32%), STR-SKEW-PRED (25%), STR-T-stocks (40%), STR-TRIPLE-HEADWIND (25%), STR-U-stocks (31%), STR-V-stocks (27%), STR-X-stocks (23%), STR-Y-stocks (25%), STR-Z-stocks (27%)

## ⚪ Unknown / No Data (2)

STR-OP-MR-CRYPTO-MEAN-REVERSION, scanner_lowcorr_regime