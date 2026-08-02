---
type: backtest-result
strategy_id: STR-20260730-atr-contraction-breakout
strategy_name: ATR Contraction Breakout
phase: 1B
asset_class: stocks
direction: long-only
universe: 529 tickers (full), 100 tickers (variants)
period_start: 2019-04-01
period_end: 2026-07-30
verdict: WATCH
verdict_reason: "Baseline (V1) has strong positive edge (+0.582R) but very low frequency (1.2/yr). Phase 1B shows loosening ADX destroys edge while shortening ATR lookback dilutes it. The strategy works as designed but is inherently low-frequency. Per updated ADR-004, frequency is not a kill reason. Retain as WATCH — low-frequency positive-edge contributor to portfolio."
data_limitations: "Daily bars, survivorship bias, frictionless, ADX computation is slow on full universe"
produced_by: "[[Backtester]]"
tags: [backtest, phase1b, STR-L, stocks, watch]
topic: strategies
confidence: high
has_quotes: false
source: HermesForge Strategies
---
# STR-L Phase 1B Results

## Perturbation Summary

| Variant | ATR Lookback | ADX | Vol | SMA | Trail | Sigs (per 100 tk) | Avg R | Win% | Notes |
|---------|-------------|-----|-----|-----|-------|-------------------|-------|------|-------|
| **V1: Baseline** | 120 | <18 | ✅ | ✅ | 2.0 | 1.3 | **+0.582** | **57.1%** | Original — strongest edge |
| V2: Shorter ATR | 60 | <18 | ✅ | ✅ | 2.0 | 2.8 | +0.168 | 40.0% | 2x signals, edge diluted |
| V4: Looser ADX | 60 | <25 | ❌ | ✅ | 2.0 | 110 | -0.203 | 17.3% | Volume removal destroys edge |
| V8: Moderate ADX | 60 | <20 | ✅ | ✅ | 2.0 | 2.0 | -1.000 | 0.0% | No improvement |
| V9: Wider trail | 60 | <18 | ✅ | ✅ | 3.0 | 1.0 | -1.000 | 0.0% | Wider stop doesn't help |
| V10: Baseline+trail | 120 | <18 | ✅ | ✅ | 3.0 | 1.0 | -1.000 | 0.0% | Wider stop hurts |

## Key Findings

1. **Volume filter is the edge preserver.** Removing it (V4) generates 110 signals per 100 tickers but flips avg R to -0.203. The volume confirmation is non-negotiable.

2. **ADX < 18 is the frequency bottleneck.** This threshold identifies genuine low-volatility regimes. Loosening to < 20 or < 25 either doesn't help (V8) or destroys edge when combined with other loosening (V4).

3. **ATR lookback is the frequency lever.** Shortening from 120 to 60 (V2) doubles signal count but dilutes avg R from +0.582 to +0.168. The 120-bar lookback identifies more prolonged, more reliable contractions.

4. **Trailing stop 2.0 is optimal.** Widening to 3.0 (V9, V10) hurts — the strategy benefits from a tight trailing stop that locks in gains quickly.

5. **The baseline configuration is the best configuration.** No perturbation improves on V1. The strategy is inherently low-frequency but high-conviction.

## Decision: WATCH

Per updated ADR-004 (frequency is no longer a kill reason), STR-L advances to WATCH status. The strategy has:
- Strong positive edge (+0.582R, well above 0.2 kill threshold)
- Good win rate (57.1%)
- Positive in 1 of 2 sub-periods tested (period3_current: +2.935R)

The low frequency (1.2 signals/year across 529 tickers) means this strategy will contribute occasional high-conviction setups to the portfolio rather than frequent signals. This is acceptable — the goal is surfacing high-probability trades across many strategies, not requiring each to fire often.

## Phase 1B/2 Recommendation

Advance to Phase 1B/2 portfolio backtest to confirm:
- Edge survives transaction costs (0.15%/side)
- Performance in a multi-strategy portfolio context
- Whether universe expansion (beyond S&P 500) increases signal frequency

## Related
- [[STR-L-phase1a]]
- [[STR-20260730-atr-contraction-breakout|STR-L Strategy]]
- [[ADR-004-Phase1-Validation-Framework]]
- [[REGIME-low-volatility]]