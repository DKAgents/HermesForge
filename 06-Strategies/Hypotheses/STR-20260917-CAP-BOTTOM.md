---
id: STR-20260917-CAP-BOTTOM
type: strategy
status: watch
asset_class: crypto
trade_style: swing
timeframe: daily
market_regime: neutral
core_idea: mean_reversion
confidence: low
publish_enabled: false
publish_channel: crypto
evidence_links:
  - CAND-20260917-crypto-post-cap-bottom
last_reviewed: 2026-09-17
created: 2026-09-17
updated: 2026-09-17
origin: HermesForge Autonomous Strategy Pipeline (cron)
tags: [strategy, crypto, btc, eth, sol, capitulation, mean-reversion, volume, dip-buying, autonomous-pipeline]
topic: strategies
has_quotes: false
source: HermesForge Autonomous Pipeline
scanner_module: scanner_crypto_post_cap_bottom
scanner_alias: scan_cap_bottom
strategy_id: STR-20260917-CAP-BOTTOM
scan_mode: batch
---

# STR-20260917-CAP-BOTTOM: Crypto Post-Capitulation Bounce

## Origin
Autonomous pipeline run 2026-09-17. Candidate: `05-Research/Edge-Candidates/CAND-20260917-crypto-post-cap-bottom.md` (composite score 58.0, confidence: medium, SPECULATIVE).

## Hypothesis
When BTC, ETH, or SOL experiences a capitulation-sized daily decline (>= 4% single-day drop) on volume at least 1.5x the 20-day average, the asset tends to bounce at least 40% of the drop within 10 trading days. The edge is strongest in established uptrends (price above 200-day SMA) where the drop is a correction, not a trend change.

This is a generalized version of the specific setup observed after the CLARITY Act failure (Sep 15, 2026) + Fed hike (Sep 16, 2026): BTC dropped 4.6% to $75K on $771M liquidations, then found support and began recovering.

## Signal Rules
1. Entry after >= DROP_PCT (4%) single-day decline.
2. Volume must be >= VOLUME_MULT (1.5x) the 20-day average (elevated volume = liquidation).
3. Price must be above 200-day SMA (uptrend filter — avoid catching falling knives).
4. Direction: Long only.
5. Stop: Entry - ATR_STOP_MULT (1.5x)  ATR(14).
6. Target: Entry + RECOVERY_FRACTION (0.40) × drop_pct × entry price.
7. Time stop: 10 trading days max.

## Backtest Results

### Phase 1A (Frictionless)
| Metric | Value |
|--------|-------|
| Total signals | 139 |
| Signals/year | 25.2 |
| **Mean R** | **+0.143** |
| Median R | +0.100 |
| Win rate | 55.4% |
| p-value | **0.125** (SPECULATIVE — p < 0.20) |
| Classification | ⚠️ WATCH (crypto subperiod classification) |

### Walk-Forward (With Costs)
| Window | Train R | OOS R | OOS Win Rate | Verdict |
|--------|---------|-------|-------------|---------|
| 2022 | +0.1756 | **-0.6956** | 50.0% | Insufficient Data (2 sigs) |
| 2023 | +0.1492 | **+0.4914** | 73.7% | **FRAGILE EDGE** (p=0.0602) |
| 2024 | +0.2257 | **+0.0241** | 50.0% | NO EDGE |
| 2025 | +0.1700 | **-0.0496** | 50.0% | NO EDGE |
| 2026 | +0.1263 | **+0.1850** | 50.0% | Insufficient Data (2 sigs) |

**Aggregate OOS:** Mean R=+0.106, p=0.418 — **NO EDGE** (positive but not statistically significant).
**In-sample:** Mean R=+0.138, p=0.137 — **POSSIBLE EDGE (low confidence)**.

### Per-Ticker Breakdown
- **BTC:** Strong performance in 2023 (recovery rally), degraded in 2024-2025 chop.
- **ETH:** Captured bounce trades well, especially in 2023. Mixed in 2024.
- **SOL:** Higher volatility produced larger R-multiples but also larger losses on failed bounces.

## Deployment Decision
**Status: WATCH** — deployed at 0.25% risk per SOUL.md single-idea ceiling (reduced due to NO EDGE overall OOS verdict).

### Rationale
- Phase 1A shows weak positive edge (p=0.125, 55.4% win rate).
- Walk-forward OOS mean R positive (+0.106) but not significant (p=0.418).
- Strong conditional performance in 2023 (bull recovery) suggests the strategy works in trend reversals but not in chop.
- The CLARITY Act failure + Fed hike setup (Sep 2026) is qualitatively similar to early 2023 conditions — recovery from a sharp catalyst-driven drop.
- Deploy at minimal risk (0.25%) with watch status. Monitor for regime condition.

### Key Risks
- **Regime dependence:** The strategy only works in bounce/uptrend regimes. In choppy/sideways markets (2024-2025), it's flat to negative.
- **Volume data quality:** Hyperliquid volume data may have gaps (some signals show vol_ratio=0.0).
- **200-day SMA filter lag:** In sharp reversals, the 200-day SMA may lag, allowing false entries during bear market drops.

## Performance Targets
- Target R-multiple per trade: ~1.5:1 (40% drop recovery on 4%+ drops)
- Stop loss: 1.5× ATR(14)
- Max hold: 10 trading days
- Position size: 0.25% risk (WATCH status, reduced)

## Paper Trading
Scanner integrated via capture_signals.py auto-discovery. Status: watch → scanned daily.
Position sizing: 0.25% risk via size_strategy_cap_bottom().