---
type: backtest-result
strategy_id: STR-Q
strategy_name: Liquidity Sweep Reversal
phase: 1B
walk_forward: true
asset_class: both
direction: bidirectional
universe: 8 crypto + 8 stocks
period_start: 2026-08-06
period_end: 2026-08-15
is_ratio: 0.6
oos_ratio: 0.4
verdict: PASS
verdict_reason: "OOS avg R = 1.131 (> 0) and p-value = 0.0000 (<= 0.05). Edge is confirmed out-of-sample."
data_limitations: "Short intraday history (~2 days crypto, ~8 days stocks, 5m bars). Small sample sizes limit statistical power."
produced_by: "Phase 1B Walk-Forward Script (run_phase1b_q.py)"
generated: 2026-08-15 21:40
tags: [backtest, walkforward, STR-Q, liquidity-sweep, crypto, stocks, pass]
topic: strategies
confidence: moderate
has_quotes: false
source: HermesForge Strategies
---
# STR-Q Phase 1B Walk-Forward Validation Results

## Method
Per-symbol walk-forward validation of the STR-Q Liquidity Sweep Reversal strategy.

1. **Data**: Full intraday 5m bars fetched per symbol (same fetchers as Phase 1A)
2. **Split**: Each symbol's data split chronologically — In-Sample (first 60%) and Out-of-Sample (last 40%)
3. **Re-scan**: The STR-Q scanner re-run independently on each segment with identical parameters
4. **Comparison**: IS vs OOS metrics compared (win rate, avg R, profit factor)
5. **ADR-004 kill floor**: If OOS avg R < 0 and p-value > 0.05 → flag for KILL
6. **P-value**: One-sample t-test on OOS R-multiples (H0: mean R = 0, two-tailed)

**Note**: This is intraday data with limited history (~2 days crypto, ~8 days stocks at 5m resolution).
Sample sizes per segment are small, which limits statistical power. Results should be interpreted
as indicative rather than definitive.

## Phase 1A Baseline (Frictionless)
- **Total signals**: 550
- **Avg R**: +0.855
- **Win rate**: 53.1%

## Aggregate Results (All Symbols Combined)

### IS vs OOS Comparison

| Metric | In-Sample (60%) | Out-of-Sample (40%) |
|--------|----------------:|--------------------:|
| Trades | 310 | 140 |
| Avg R | +0.675 | +1.131 |
| Median R | -0.190 | +1.208 |
| Sum R | +209.309 | +158.363 |
| Win Rate | 48.7% | 62.1% |
| Profit Factor | 2.43 | 4.46 |
| Max Win | +3.000R | +3.000R |
| Max Loss | -1.000R | -1.000R |
| Avg Bars Held | 8.5 | 8.9 |

### OOS Statistical Significance
- **N = 140 signals**
- **Mean R = +1.131**
- **p-value = 0.0000** (one-sample t-test, H0: mean R = 0)
- **ADR-004 kill floor**: OOS avg R >= 0 and p-value <= 0.05

- **Avg R degradation**: +0.456 (IS: +0.675 → OOS: +1.131)
- **Win rate degradation**: +13.4pp (IS: 48.7% → OOS: 62.1%)

## Per-Symbol Results: Crypto

| Symbol | IS N | IS Avg R | IS Win% | IS PF | OOS N | OOS Avg R | OOS Win% | OOS PF | p-value | Verdict |
|--------|------|----------|---------|-------|-------|-----------|----------|--------|---------|---------|
| BTC | 30 | +0.276 | 40.0% | 1.47 | 12 | +0.278 | 50.0% | 1.57 | 0.5562 | WATCH (positive but not significant) |
| ETH | 32 | +1.072 | 59.4% | 3.85 | 6 | +0.333 | 33.3% | 1.50 | 0.7089 | WATCH (positive but not significant) |
| SOL | 34 | +1.070 | 52.9% | 3.55 | 3 | +0.973 | 66.7% | 3.92 | 0.4882 | WATCH (positive but not significant) |
| OP | 14 | +0.566 | 42.9% | 2.26 | 3 | +2.338 | 100.0% | inf | 0.0716 | WATCH (positive but not significant) |
| ARB | 11 | +0.454 | 45.5% | 1.89 | 7 | +1.286 | 57.1% | 4.00 | 0.1627 | WATCH (positive but not significant) |
| AVAX | 11 | +1.577 | 81.8% | 9.67 | 3 | +3.000 | 100.0% | inf | 0.0000 | CONFIRMED |
| DOGE | 18 | +0.917 | 50.0% | 2.91 | 5 | +0.610 | 40.0% | 2.03 | 0.5659 | WATCH (positive but not significant) |
| LINK | 9 | +0.333 | 33.3% | 1.50 | 6 | +2.756 | 100.0% | inf | 0.0001 | CONFIRMED |

### Crypto Aggregate
| Segment | N | Avg R | Win Rate | Profit Factor |
|---------|---|-------|----------|---------------|
| IS | 159 | +0.810 | 50.9% | 2.78 |
| OOS | 45 | +1.175 | 62.2% | 4.14 |
| p-value | | | | 0.0001 |

## Per-Symbol Results: Stocks

| Symbol | IS N | IS Avg R | IS Win% | IS PF | OOS N | OOS Avg R | OOS Win% | OOS PF | p-value | Verdict |
|--------|------|----------|---------|-------|-------|-----------|----------|--------|---------|---------|
| SPY | 26 | +0.581 | 53.8% | 2.26 | 9 | +1.425 | 66.7% | 7.17 | 0.0388 | CONFIRMED |
| AAPL | 13 | +0.274 | 46.2% | 1.61 | 8 | +1.572 | 75.0% | 9.96 | 0.0343 | CONFIRMED |
| NVDA | 18 | +0.675 | 44.4% | 2.34 | 16 | +0.986 | 56.2% | 3.43 | 0.0572 | WATCH (positive but not significant) |
| TSLA | 21 | +0.391 | 47.6% | 1.75 | 12 | +1.767 | 83.3% | 11.60 | 0.0028 | CONFIRMED |
| AMZN | 16 | +1.403 | 62.5% | 5.24 | 10 | +0.917 | 50.0% | 4.76 | 0.1276 | WATCH (positive but not significant) |
| MSFT | 15 | +0.479 | 46.7% | 1.90 | 11 | +1.095 | 72.7% | 5.30 | 0.0489 | CONFIRMED |
| GOOGL | 19 | +0.134 | 36.8% | 1.26 | 17 | +0.716 | 52.9% | 2.90 | 0.1035 | WATCH (positive but not significant) |
| META | 23 | +0.407 | 34.8% | 1.73 | 12 | +0.812 | 50.0% | 2.83 | 0.1785 | WATCH (positive but not significant) |

### Stocks Aggregate
| Segment | N | Avg R | Win Rate | Profit Factor |
|---------|---|-------|----------|---------------|
| IS | 151 | +0.534 | 46.4% | 2.09 |
| OOS | 95 | +1.111 | 62.1% | 4.65 |
| p-value | | | | 0.0000 |

## Direction Breakdown (All Symbols)

### In-Sample
  - **bullish**: 151 trades, WR=51.0%, avg R=+0.708, PF=2.61
  - **bearish**: 159 trades, WR=46.5%, avg R=+0.644, PF=2.28

### Out-of-Sample
  - **bullish**: 68 trades, WR=54.4%, avg R=+0.893, PF=3.20
  - **bearish**: 72 trades, WR=69.4%, avg R=+1.356, PF=6.40

## Assessment

### Data Limitations
- **Crypto**: ~2 days of 5m bars (500 bars per symbol). IS segment ~300 bars, OOS ~200 bars.
- **Stocks**: ~8 days of 5m bars (500 bars per symbol). IS segment ~300 bars, OOS ~200 bars.
- These short windows mean few trades per symbol per segment, limiting statistical power.
- The p-value from a one-sample t-test on small samples should be interpreted cautiously.

### Comparison to Phase 1A

| Metric | Phase 1A (frictionless, full) | Phase 1B IS (60%) | Phase 1B OOS (40%) |
|--------|------------------------------|-------------------|---------------------|
| Avg R | +0.855 | +0.675 | +1.131 |
| N | 550 | 310 | 140 |
| Win Rate | 53.1% | 48.7% | 62.1% |

## Overall Verdict: PASS

OOS avg R = 1.131 (> 0) and p-value = 0.0000 (<= 0.05). Edge is confirmed out-of-sample.

Per ADR-004 kill floor check:
- **OOS avg R**: +1.131 (>= 0 → not losing)
- **p-value**: 0.0000 (<= 0.05 → significant)
- **Kill condition** (OOS avg R < 0 AND p > 0.05): NOT TRIGGERED

## Related
- [[ADR-004-Phase1-Validation-Framework]]
- Phase 1A results: `scripts/validation/results/STR-Q-crypto-phase1a.csv`, `STR-Q-stocks-phase1a.csv`
- Scanner: `scripts/validation/scanners/scanner_q_liquidity_sweep.py`
