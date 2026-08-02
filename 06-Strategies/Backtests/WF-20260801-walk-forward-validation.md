---
id: WF-20260801-walk-forward-validation
type: backtest_result
strategy: [STR-B, STR-I, STR-J, STR-L]
method: walk_forward
date: 2026-08-01
windows: 5
train_period: 2y
test_period: 1y
transaction_costs: true
gap_risk: true
---

# Walk-Forward Validation — August 1, 2026

First rigorous out-of-sample validation of all active strategies.

## Method
- 5 rolling windows: train 2yr → test 1yr (unseen data)
- Parameter optimization on 30-ticker sample (S&P 100 subset)
- OOS testing on full universe (529 stocks, 42 crypto)
- Transaction costs: 12bp stocks (5bp spread + 1bp commission × 2), 5bp crypto
- Gap risk: next-bar open fills if stop is gapped through
- Significance: one-sample t-test (H0: mean R = 0) + 5000-sample bootstrap CI

## Results

| Strategy | In-Sample R | OOS R | OOS N | t-stat | p-value | 95% CI | Verdict |
|----------|------------|-------|-------|--------|---------|--------|---------|
| STR-B MACD Div | 0.78 | 1.25 | 2035 | 10.60 | <0.0001 | [1.01, 1.48] | **ROBUST EDGE** |
| STR-I AdaptiveTrend | 0.22 | 0.24 | 1834 | 5.60 | <0.0001 | [0.15, 0.32] | **ROBUST EDGE** |
| STR-J EUFEARIA CCI | -0.003 | 0.002 | 15793 | 0.15 | 0.88 | [-0.02, 0.03] | **NO EDGE** |
| STR-L ATR Contraction | -0.54 | n/a | 0 | n/a | n/a | n/a | **INSUFFICIENT DATA** |

## Per-Window OOS R (Stocks, After Costs)

| Strategy | 2022 | 2023 | 2024 | 2025 | 2026 |
|----------|------|------|------|------|------|
| STR-B | +2.00 | +0.96 | +0.83 | +1.21 | +2.08 |
| STR-I | -0.13 | +0.50 | +0.30 | +0.42 | +0.30 |
| STR-J | +0.25 | -0.03 | -0.12 | -0.06 | -0.06 |
| STR-L | n/a | n/a | n/a | n/a | n/a |

## Key Findings

1. **STR-B has strong, real edge** — OOS R (1.25) exceeds in-sample R (0.78), meaning no curve-fitting. Statistically significant at p<0.0001.

2. **STR-I has real but smaller edge** — One negative window (2022 bear market transition), but recovered. Edge is fragile in regime transitions.

3. **STR-J has NO edge** — 25,150 signals with avg R ≈ 0. Walk-forward confirms the strategy generates signals but they have no predictive power. Killed.

4. **STR-L cannot be validated** — Only 6 signals in 7 years. Walk-forward needs 3+ signals per training window to optimize. Too low-frequency for this method.

5. **Transaction costs matter but don't change rankings** — 12bp round-trip reduces R by ~0.02-0.05 per trade. STR-B and STR-I survive costs. STR-J was already at zero.

6. **2022 was the hardest window** — Bear market transition. Only STR-B survived cleanly. STR-I went negative. This suggests regime transitions are the Achilles heel of trend-following strategies.

## Decisions

- STR-J: KILLED (no edge confirmed)
- STR-B: Confidence increased to HIGH
- STR-I: Keep LIVE, monitor regime transitions
- STR-L: Keep WATCH, needs alternative validation
