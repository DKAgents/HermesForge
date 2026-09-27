---
type: strategy-vault-note
strategy_id: STR-20260917-CAP-BOTTOM
status: watch
created: 2026-09-17
updated: 2026-09-17
tags: [strategy, crypto, btc, mean-reversion, capitulation, dip-buying, autonomous-pipeline]
---

# STR-20260917-CAP-BOTTOM — Crypto Post-Capitulation Bounce

**Status:** ⚠️ WATCH (deployed at 0.25% risk)
**Origin:** HermesForge Autonomous Strategy Pipeline (2026-09-17)
**Edge Candidate:** [[CAND-20260917-crypto-post-cap-bottom]]

## Summary
Generalized dip-buying strategy for BTC/ETH/SOL after 4%+ single-day capitulation drops on elevated volume (>1.5x avg). Mean-reverts 40% of drop within 10 days.

## Backtest Results
| Metric | Value |
|--------|-------|
| Phase 1A Mean R | +0.143 (p=0.125, SPECULATIVE) |
| Walk-Forward OOS Mean R | +0.106 (p=0.418, NO EDGE) |
| Best Window | 2023: OOS +0.49R (p=0.06) |
| Worst Window | 2022: OOS -0.70R (only 2 signals) |
| Win Rate | 55.4% (Phase 1A) |
| Signals/Year | 25.2 |

## Deployment
- **Scanner:** `scanner_crypto_post_cap_bottom.py` (batch mode)
- **Sizing:** 0.25% risk per trade (WATCH, reduced)
- **Regime:** `regime_strategy_selector.py` → `STR-CAP-BOTTOM`
- **Paper Trading:** Auto-discovered via capture_signals.py

## Key Risk
Regime-dependent — works in recovery/uptrend (2023) but degrades in chop (2024-2025). Current setup (Sep 2026 CLARITY failure + Fed hike) qualitatively resembles 2023 conditions.

## Related
- [[STR-20260917-CAP-BOTTOM]] (full hypothesis file)
- [[CAND-20260917-crypto-post-cap-bottom]] (edge candidate)