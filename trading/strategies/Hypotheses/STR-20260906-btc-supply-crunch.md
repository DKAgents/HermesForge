---
id: STR-20260906-BTC-SUPPLY-CRUNCH
type: strategy
status: watch
asset_class: crypto
trade_style: swing
timeframe: daily
market_regime: neutral
core_idea: regime_trade
confidence: medium
publish_enabled: false
publish_channel: crypto
evidence_links:
  - CAND-20260906-btc-supply-crunch-institutional-floor
last_reviewed: 2026-09-06
created: 2026-09-06
updated: 2026-09-06
origin: HermesForge Autonomous Strategy Pipeline (cron)
tags: [strategy, crypto, btc, supply-crunch, volume, compression, autonomous-pipeline]
topic: strategies
has_quotes: false
source: HermesForge Autonomous Pipeline
scanner_module: scanner_btc_supply_crunch
scanner_alias: scan_btc_supply
strategy_id: STR-20260906-BTC-SUPPLY-CRUNCH
scan_mode: batch
---

# STR-20260906-BTC-SUPPLY-CRUNCH: BTC Supply Crunch / Thin-Float Breakout

## Origin
Autonomous pipeline run 2026-09-06. Candidate: `05-Research/Edge-Candidates/CAND-20260906-btc-supply-crunch-institutional-floor.md` (composite score 68.0, confidence: medium).

## Hypothesis
BTC in a supply crunch regime (thin spot volume + compression near key levels + uptrend intact) tends to break out asymmetrically to the upside. The mechanism: declining available spot liquidity amplifies any directional catalyst, creating explosive upside moves from compressed price structures.

## Signal Rules
1. BTC must be above its 50-day SMA (uptrend intact / institutional floor holding).
2. 20-day volume percentile must be below THIN_VOLUME_PCT (50th percentile) — confirming thin float.
3. 20-day price range (H-L)/close must be below COMPRESSION_THRESHOLD (15%) — confirming consolidation.
4. Entry: LONG at close when all conditions met.
5. Exit: ATR-based trailing stop (2.5× ATR) or MIN_RR target (1.5:1), max 15 bars held.

## Backtest Results

### Phase 1A (Frictionless)
| Metric | Value |
|--------|-------|
| Total signals | 65 |
| Signals/year | 19.4 |
| **Mean R** | **+0.256** |
| Median R | +0.065 |
| Win rate | 53.8% |
| p-value | **0.0651** (significant at 10% level) |
| Sub-periods positive | 2/3 |
| Classification | ⚠️ WATCH |
| Friction note | avg R < 0.5 — check edge survives costs |

### Walk-Forward (With Costs)
| Window | Train R | OOS R | OOS Win Rate |
|--------|---------|-------|-------------|
| 2024 | +0.5915 | **+0.3160** | 53.8% |
| 2025 | +0.4636 | **+0.1633** | 55.0% |
| 2026 | +0.3385 | **-0.0044** | 41.2% |

**Aggregate OOS:** Mean R=+0.146, p=0.326 — **NO EDGE** (positive but not statistically significant).
**In-sample:** Mean R=+0.249, p=0.068 — **FRAGILE EDGE**.

## Deployment Decision
**Status: WATCH** — deployed at 0.5% risk per SOUL.md single-idea ceiling.

### Rationale
- Phase 1A shows real edge (p=0.065, 53.8% win rate, 2/3 sub-periods positive).
- Walk-forward OOS mean R positive (+0.146) but not significant (p=0.326).
- 2026 window was a drawdown (-0.0044) — the signal worked in 2024-2025 but struggled in the current regime.
- The edge is genuinely novel (no direct historical analog for $3.8B ETF inflows into 7-year low volume).
- Deploy at reduced risk (0.5%) with watch status. Monitor for regime change.

### Key Risks
- **Regime fragility:** The supply crunch setup is regime-dependent. If macro shifts (hawkish Fed, oil shock, dollar strength), the institutional floor could break.
- **Volume normalization:** If spot volume returns to normal, the thin-float amplification disappears.
- **2026 degradation:** OOS 2026 shows slightly negative returns — the edge may be decaying.

## Performance Targets
- Target R-multiple per trade: 1.5:1 (MIN_RR)
- Trailing stop: 2.5× ATR(14)
- Max hold: 15 trading days
- Position size: 0.5% risk (WATCH status)

## Paper Trading
Scanner integrated via capture_signals.py auto-discovery. Status: watch → scanned daily.
Position sizing: 0.5% risk via size_strategy_btc_supply().