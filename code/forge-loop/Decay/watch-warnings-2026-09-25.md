---
date: 2026-09-25
check_type: Jev-powered decay detection (US-151)
source: jev_decay.check_all_active()
---

# Watch Warnings — 2026-09-25

Strategies flagged by Jev for monitoring (decay_prob > 45%, recommendation=watch):

| Strategy | Decay % | Δ | Concern |
|---|---|---|---|
| 🟡 NARROW_LEAD_BREADTH | 72% | — | Narrow leadership edge flat |
| 🟡 STR-20260726-eufearia-cci-reversal | 72% | +1 | CCI reversal edge weakening |
| 🟡 STR-20260726-first-pullback-trend-swing | 82% | −1 | **Critical watch** — decay >80%, may demote soon |
| 🟡 STR-20260814-SECTOR-MOMENTUM | 73% | −3 | Sector rotation momentum improving slightly |
| 🟡 STR-20260816-CRYPTO-FG-CONTRARIAN | 72% | +1 | Fear & Greed contrarian weakening |
| 🟡 **STR-20260816-VIX-VRP-CONTANGO** ⚠ | 70% | +2 | **ACTIVE** — VRP capture fading, worsening trend |
| 🟡 STR-20260903-BTC-LEVERAGE-FLUSH | 77% | — | Leverage flush signal flat |
| 🟡 **STR-A-ma-pullback-fibonacci** ⚠ | 55% | −4 | **ACTIVE** — improving, was 59% yesterday |
| 🟡 STR-C-breakout-volume | 74% | +3 | Volume breakout eroding — largest jump today |
| 🟡 STR-D-sr-role-reversal | 59% | +1 | S/R role reversal stable at moderate |
| 🟡 STR-E-rsi-mean-reversion | 75% | +2 | RSI mean reversion weakening |
| 🟡 STR-F-bollinger-squeeze-breakout | 65% | +1 | Squeeze breakout stable |
| 🟡 STR-GOLD-LEAD | 72% | — | Gold-leading signal flat |
| 🟡 STR-NVDA-LEAD | 74% | −1 | NVDA leadership signal slightly better |
| 🟡 STR-VIXFG-DIVERGENCE | 72% | +2 | VIX/FG divergence worsening |
| 🟡 scanner_crypto_deleveraging_breakout | 70% | +1 | Deleveraging scanner worsening |
| 🟡 scanner_skew_crosssectional | 64% | — | Cross-sectional skew flat |

## ⚠ Active Strategy Alerts

| Strategy | Decay | Δ | Notes |
|---|---|---|---|
| **VIX-VRP-CONTANGO** | 70% | +2 | `06-Strategies/Active/STR-20260816-vix-vrp-contango-breakout.md` — worsening trend, approaching demote threshold. Monitor closely. |
| **ma-pullback-fibonacci** | 55% | −4 | `06-Strategies/Active/STR-20260719-ma-pullback-fibonacci-entry.md` — improving significantly. May clear watch soon if trend continues. |
| **lowcorr-regime** | N/A | — | `06-Strategies/Active/STR-20260818-lowcorr-regime.md` — Jev unreachable (jev_error=True), leave last state. scanner_lowcorr_regime. |

## Already Demoted (previously handled, no action)

| Strategy | Decay % | Demoted |
|---|---|---|
| 🔴 STR-BTC-DOM | 86% | 2026-09-21 |
| 🔴 STR-EBE-DISPERSION | 85% | 2026-09-21 |
| 🔴 STR-W-stocks | 87% | 2026-09-22 |
| 🔴 STR-YIELD-SURGE | 85% | 2026-09-22 |
| 🔴 scanner_overnight_drift | 82% | 2026-09-22 |

## Healthy Active Strategy (no action)

- 🟢 **STR-OIL-SHOCK** (27%, −2 from yesterday) — `06-Strategies/Active/STR-20260901-oil-shock-sector-rotation.md`

## Healthy (no action)

39 strategies with decay < 45% — no action needed.

## Unknown (Jev leave-last-state, no trade data)

- STR-OP-MR-CRYPTO-MEAN-REVERSION: jev_error
- STR-QW-crypto: jev_error
- scanner_lowcorr_regime: jev_error — **ACTIVE strategy**, manual review recommended