---
id: STR-20260801-pricemom-factor
type: strategy
status: killed
asset_class: crypto
trade_style: swing
timeframe: daily
market_regime: trending
core_idea: factor_momentum
confidence: low
publish_enabled: false
kill_reason: "Phase 1A: avg R=-0.05 (crypto), all perturbations negative. PRICEMOM factor works as relative quintile ranking, not absolute per-ticker threshold. Scanner architecture cannot capture cross-sectional factor edge."
kill_date: 2026-08-01
source: "Factor decomposition: PRICEMOM +40% annualized, p=0.04 in crypto"
topic: strategies
has_quotes: false
tags: []
scanner_module: scanner_p_pricemom
scanner_alias: scan_p_mom

strategy_id: STR-P-pricemom-factor
---
# STR-O: Price Momentum Factor Strategy

## Hypothesis

Built from factor decomposition evidence: PRICEMOM factor (price relative to SMA200) showed +40% annualized return, p=0.04 in crypto long-short quintile portfolio. Hypothesis: this factor edge can be captured as a per-ticker signal.

## Design

- PRICEMOM = close / SMA(200) - 1
- Long when PRICEMOM > 0.15 AND PRICEMOM is accelerating
- Short when PRICEMOM < -0.15 AND PRICEMOM is decelerating
- ATR trailing stop (2.5x ATR), 60-bar time stop

## Phase 1A Results

| Asset | Signals | Avg R | Win Rate | PF |
|-------|---------|-------|----------|-----|
| Crypto | 2814 | -0.05 | 37.8% | 0.87 |
| Stocks | 18144 | +0.12 | 40.4% | 1.30 |

## Phase 1B Perturbations (Crypto)

| Variant | Signals | Avg R | Win Rate | PF |
|---------|---------|-------|----------|-----|
| Baseline | 2814 | -0.05 | 37.8% | 0.87 |
| Higher threshold (0.25) | 2119 | -0.10 | 36.0% | 0.76 |
| Higher threshold (0.40) | 1205 | -0.14 | 34.1% | 0.67 |
| Shorter SMA (100) | 2914 | -0.06 | 38.9% | 0.84 |
| Tighter stop (1.5x) | 2814 | -0.16 | 34.6% | 0.63 |
| Longer hold (120) | 2814 | -0.06 | 37.7% | 0.85 |
| Long only | 1046 | -0.10 | 32.0% | 0.77 |

All perturbations negative. Strategy killed.

## Why It Failed

The PRICEMOM factor works as a **relative ranking** (top quintile vs bottom quintile across all tickers), not as an **absolute threshold** per ticker. During bull markets, many cryptos are above SMA200 — buying any crypto 15% above SMA200 doesn't select the BEST ones. The edge comes from cross-sectional ranking, which our per-ticker scanner architecture cannot capture.

## Lesson

Factor-based strategies require a fundamentally different architecture than pattern-based scanners. Cross-sectional ranking scanners (rank all tickers, long top N, short bottom N) are needed to express factor bets properly. This is a future research direction — the current scanner framework is designed for per-ticker pattern detection, not portfolio-level factor construction.
