---
type: backtest-result
strategy_id: STR-B
strategy_name: MACD Divergence
phase: walk-forward
asset_class: both
direction: bidirectional
universe: 529 stocks + 42 crypto
period_start: 2019-01-01
period_end: 2026-12-31
verdict: PASS
verdict_reason: "Stocks: ROBUST EDGE (OOS R=1.25, p<0.001, all 5 windows positive). Crypto: INSUFFICIENT DATA (only 2 OOS signals in 1 window, 4/5 windows had <3 training signals). Passes on stocks per ADR-004 Amendment 1."
data_limitations: "Daily bars, survivorship bias, quick mode, crypto optimization sample too small"
produced_by: "Walk-Forward Framework"
tags: [backtest, walkforward, STR-B, stocks, crypto, pass]
topic: strategies
confidence: high
has_quotes: false
source: HermesForge Strategies
---
# STR-B Walk-Forward Validation Results

## Method
Per-ticker walk-forward validation. 5 rolling windows (2-year train, 1-year test).
Quick mode (3 param combos per window).

## Results: Stocks

### OOS Per Window

| Window | Train R | Train N | OOS R | OOS N | Win Rate |
|--------|---------|---------|-------|-------|----------|
| 2022   | +0.7712 | 82      | **+2.0003** | 344   | 53%      |
| 2023   | +0.6067 | 88      | **+0.9602** | 551   | 42%      |
| 2024   | +0.8816 | 103     | **+0.8250** | 536   | 46%      |
| 2025   | +0.8162 | 99      | **+1.2073** | 437   | 45%      |
| 2026   | +0.9801 | 90      | **+2.0781** | 167   | 57%      |

### OOS Significance (Stocks)
- **N = 2035 signals**
- **Mean R = 1.25** (with costs)
- **t-stat = 10.60, p-value < 0.001**
- **Verdict: ROBUST EDGE**

All 5 windows positive and individually significant. This is a robust, consistent edge.

## Results: Crypto

### OOS Per Window

| Window | Train R | Train N | OOS R | OOS N | Win Rate |
|--------|---------|---------|-------|-------|----------|
| 2022   | n/a     | n/a     | n/a   | n/a   | n/a      |
| 2023   | n/a     | n/a     | n/a   | n/a   | n/a      |
| 2024   | +2.1108 | 3       | +2.1534 | 2   | 50%      |
| 2025   | n/a     | n/a     | n/a   | n/a   | n/a      |
| 2026   | n/a     | n/a     | n/a   | n/a   | n/a      |

### Crypto Assessment
- 4 of 5 windows: insufficient training signals (< 3) for optimization
- Only 2 OOS signals total — cannot draw conclusions
- **Verdict: INSUFFICIENT DATA**

The 10-coin optimization sample is too small for MACD divergence to generate enough signals. Expanding to the full 42-coin universe for optimization might help, but the signal frequency on crypto is inherently lower (MACD divergence requires specific market structure).

## Overall Verdict: PASS (on stocks)

Per ADR-004 Amendment 1:
- **Stocks**: ROBUST EDGE — all 5 windows positive and significant, OOS R = 1.25
- **Crypto**: INSUFFICIENT DATA — not killed, just untested
- Strategy survives and remains LIVE for stocks
- Crypto: retains current status (runs but with insufficient validation)
- To validate crypto properly, would need a larger optimization sample or different approach

## Related
- [[STR-B-phase1a]]
- [[STR-20260719-macd-histogram-divergence-weekly-assessment]]
- [[ADR-004-Phase1-Validation-Framework]]