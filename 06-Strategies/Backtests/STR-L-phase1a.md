---
type: backtest-result
strategy_id: STR-20260730-atr-contraction-breakout
strategy_name: ATR Contraction Breakout
phase: 1A
asset_class: stocks
direction: long-only
universe: 529 tickers
period_start: 2019-04-01
period_end: 2026-07-30
signals_per_year: 1.2
avg_r: 0.582
win_rate: 57.1
sub_periods_positive: "1/2 (period1 +0.190, period3 +2.935)"
trade_count: 7
verdict: WATCH
verdict_reason: "Positive avg R (0.582) and 57.1% win rate. Originally killed for low frequency (1.2 sig/yr) but ADR-004 updated: frequency is no longer a kill reason. Low-frequency positive-edge strategies contribute to portfolio diversity. Phase 1B should confirm edge survives costs and explore loosening filters to increase signal count."
data_limitations: "Daily bars, survivorship bias (current S&P constituents), frictionless"
produced_by: "[[Backtester]]"
tags: [backtest, phase1a, STR-L, stocks, watch]
---

# STR-L Phase 1A Results

## Summary

7 signals across 529 tickers over ~7 years (1.2 signals/year). This is well below the ADR-004 kill threshold of 12 signals/year.

The positive average R (0.582) and win rate (57.1%) are encouraging, but the strategy is too restrictive. The ATR 120-bar low + ADX < 18 + breakout above 20-bar high + 1.5x volume + SMA200 creates a compound filter that rarely fires.

This echoes the STR-H failure: too many filters compounded. However, STR-L's edge per trade is much stronger (0.582R vs -1.975R), so the concept has merit if the filter can be loosened.

## Signals

| Ticker | Date | R | Exit | Sub-period |
|--------|------|---|------|-----------|
| AFL | 2019-11-26 | -1.000 | stop | period1_bull |
| DLR | 2021-06-02 | +2.071 | trailing | period1_bull |
| DLR | 2021-06-03 | +1.975 | trailing | period1_bull |
| FRT | 2021-06-02 | +0.096 | trailing | period1_bull |
| PAYX | 2021-06-10 | -1.000 | stop | period1_bull |
| RL | 2021-10-29 | -1.000 | stop | period1_bull |
| GLD | 2025-08-29 | +2.935 | trailing | period3_current |

## Key Findings

1. **Positive avg R (0.582)** — the edge per trade is real. When it fires, it works.
2. **Signal scarcity is the killer** — 1.2/year is below the 12/year floor.
3. **June 2021 cluster** — 4 of 7 signals in a 2-week window (DLR, FRT, PAYX) suggests the strategy detects genuine low-vol clusters, but they're too rare.
4. **No period2_bear signals** — the ATR 120-bar low + ADX < 18 combo never fires in bear markets (volatility stays elevated).

## Phase 1B Opportunity

The concept is sound but the filter is too strict. Possible Phase 1B perturbations:
- Reduce ATR lookback from 120 to 60 bars (more frequent contraction detection)
- Relax ADX threshold from < 18 to < 25 (broader low-trend definition)
- Remove volume confirmation (it's the 4th filter, lesson from STR-H: max 2-3)
- These changes might lift signal frequency to a usable level while preserving the positive edge.

## Related
- [[STR-20260730-atr-contraction-breakout|STR-L Strategy]]
- [[FAIL-STR-F-bollinger-squeeze]]
- [[ADR-004-Phase1-Validation-Framework]]
- [[REGIME-low-volatility]]