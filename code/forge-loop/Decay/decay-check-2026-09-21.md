---
type: decay-check
date: 2026-09-21T14:02:34Z
engine: jev
total_checked: 56
demoted: 5
watching: 17
healthy: 32
unknown: 2
---

# Jev Decay Check — 2026-09-21

## Summary

| Category | Count |
|----------|-------|
| 🔴 Demoted | 5 |
| 🟡 Watching | 17 |
| 🟢 Healthy | 32 |
| ⚪ Unknown (no data) | 2 |
| **Total** | **56** |

Thresholds: decay_prob > 0.70 AND breakdown_prob > 0.60 → demote; decay_prob > 0.45 → watch.

---

## 🔴 Demotions (5)

| Strategy | Decay % | Action |
|----------|---------|--------|
| STR-BTC-DOM | 86% | CSV-only — no .md to move. Flagged for removal from active tracking. |
| STR-EBE-DISPERSION | 84% | CSV-only — no .md to move. Flagged for removal from active tracking. |
| STR-W-stocks | 89% | CSV-only — no .md to move. Flagged for removal from active tracking. |
| STR-YIELD-SURGE | 84% | CSV-only — no .md to move. Flagged for removal from active tracking. |
| scanner_overnight_drift | 82% | CSV-only — no .md to move. Flagged for removal from active tracking. |

Note: None of these strategies have corresponding .md files in `06-Strategies/Active/`. They exist only as CSV backtest results. No file moves were possible.

---

## 🟡 Watching (17)

| Strategy | Decay % | Threshold breached |
|----------|---------|--------------------|
| NARROW_LEAD_BREADTH | 71% | watch (>45%) |
| STR-20260726-eufearia-cci-reversal | 71% | watch (>45%) |
| STR-20260726-first-pullback-trend-swing | 81% | watch (>45%) ⚠️ near demote |
| STR-20260814-SECTOR-MOMENTUM | 75% | watch (>45%) |
| STR-20260816-CRYPTO-FG-CONTRARIAN | 72% | watch (>45%) |
| STR-20260816-VIX-VRP-CONTANGO | 68% | watch (>45%) |
| STR-20260903-BTC-LEVERAGE-FLUSH | 78% | watch (>45%) ⚠️ near demote |
| STR-A-ma-pullback-fibonacci | 56% | watch (>45%) |
| STR-C-breakout-volume | 71% | watch (>45%) |
| STR-D-sr-role-reversal | 59% | watch (>45%) |
| STR-E-rsi-mean-reversion | 73% | watch (>45%) |
| STR-F-bollinger-squeeze-breakout | 64% | watch (>45%) |
| STR-GOLD-LEAD | 72% | watch (>45%) |
| STR-NVDA-LEAD | 75% | watch (>45%) |
| STR-VIXFG-DIVERGENCE | 71% | watch (>45%) |
| scanner_crypto_deleveraging_breakout | 70% | watch (>45%) |
| scanner_skew_crosssectional | 65% | watch (>45%) |

⚠️ = 75%+ decay — close to demotion threshold, re-check next cycle.

---

## 🟢 Healthy (32)

STR-20260728-adaptive-trend (35%), STR-20260906-BTC-SUPPLY-CRUNCH (24%), STR-20260906-SENTIMENT-DIVERGENCE (13%), STR-AA-stocks (32%), STR-AB-stocks (24%), STR-AC-stocks (27%), STR-AD-stocks (24%), STR-ADD-FACTOR (13%), STR-AE-stocks (40%), STR-AF-stocks (39%), STR-AG-stocks (19%), STR-AH-stocks (21%), STR-AI-stocks (30%), STR-AJ-stocks (32%), STR-B-macd-histogram-divergence (27%), STR-B-stocks (41%), STR-CAP-BOTTOM-CRYPTO-CAPITULATION-BOUNCE (26%), STR-DEBASEMENT (35%), STR-FOMC-CERTAINTY (37%), STR-G-relative-strength-rotation (24%), STR-OIL-SHOCK (27%), STR-Q-crypto (23%), STR-Q-stocks-deep (23%), STR-Q-stocks (26%), STR-R-crypto (37%), STR-R-stocks (33%), STR-S-stocks (32%), STR-SKEW-PRED (24%), STR-T-stocks (38%), STR-TRIPLE-HEADWIND (25%), STR-U-stocks (30%), STR-V-stocks (26%), STR-X-stocks (21%), STR-Y-stocks (25%), STR-Z-stocks (28%)

## ⚪ Unknown / No Data (2)

STR-OP-MR-CRYPTO-MEAN-REVERSION (0%), scanner_lowcorr_regime (0%)