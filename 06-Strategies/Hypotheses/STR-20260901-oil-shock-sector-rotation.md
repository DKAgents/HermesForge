---
topic: strategies
confidence: high
has_quotes: false
tags: []
source: HermesForge Strategies
created: 2026-09-02
---
|---
|id: STR-20260901-oil-shock-sector-rotation
|type: strategy
|status: watch
|asset_class: stock
|trade_style: swing
|timeframe: daily
|market_regime: caution
|core_idea: macro_overlay
|confidence: low
|publish_enabled: false
|publish_channel: stock
|evidence_links:
|  - CAND-20260901-hormuz-oil-shock
|last_reviewed: 2026-09-01
|created: 2026-09-01
|updated: 2026-09-01
|origin: HermesForge Autonomous Strategy Pipeline (cron)
|tags: [strategy, macro, oil, energy, geopolitical, sector-rotation, autonomous-pipeline]
|topic: strategies
|has_quotes: false
|source: HermesForge Autonomous Pipeline
|scanner_module: scanner_hormuz_oil_shock
|scanner_alias: scan_oil_shock
|strategy_id: STR-OIL-SHOCK
|scan_mode: batch
|---

# Oil Shock Sector Rotation v1.0

## Hypothesis
Geopolitical oil supply shocks through critical chokepoints (Strait of Hormuz)
create a predictable cross-asset pattern: Energy stocks (XLE, XOM, CVX) benefit
from the risk premium expansion, while consumer discretionary (XLY) suffers from
higher gasoline prices → lower disposable income.

## Entry Rules
- **Primary Signal:** CL crude oil rises >= SPIKE_PCT (3.5%) over SPIKE_LOOKBACK (2) days
- **Confirmation:** XLE volume > 1.5x 20d average (optional, disabled by default)
- **Signal 1 (Energy Long):** Long XLE, XOM, CVX. ATR-based stop (2.0x). Target: 1.5x risk.
- **Signal 2 (Discretionary Short):** Short XLY. ATR-based stop (2.0x). Target: 1.5x risk.
- **Max Hold:** 20 trading days (~1 month)

## Exit Rules
- Stop loss (ATR_STOP_MULT * ATR from entry)
- Target hit (MIN_RR * risk)
- Time stop at MAX_BARS_HELD

## Walk-Forward Validation Results
- **Phase 1A:** 148 signals, mean R=+0.183, p=0.1069 (SPECULATIVE)
- **OOS Overall:** 88 signals, mean R=+0.1712, p=0.2311 (NO EDGE overall)
- **Recent Windows:** 2025 OOS +0.37R (Possible Edge), 2026 OOS +0.65R (Robust Edge, p=0.0056)
- **Verdict:** WATCH — deployed with 0.5% risk

## Risk Note
- Geopolitical oil trades have high variance and can reverse abruptly on diplomatic breakthroughs
- 2022-2023 windows showed consistent losses (OOS mean R of -0.86 in 2023)
- Effectiveness appears to be regime-dependent: works in risk-off/energy bull, fails in disinflation
- Deploy with 0.5% risk — do NOT size up even if recent performance is strong