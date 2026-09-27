---
id: FACTOR-20260801-factor-decomposition
type: backtest_result
strategy: [STR-B, STR-I]
method: factor_decomposition
date: 2026-08-01
factors: [MOM12_1, REV1, LOWVOL, LIQUID, PRICEMOM]
transaction_costs: true
topic: strategies
confidence: high
has_quotes: false
tags: []
source: HermesForge Strategies
---
# Factor Construction & Decomposition — August 1, 2026

First factor-based analysis of HermesForge strategies.

## Part 1: Factor Premia

Long-short quintile portfolios, monthly rebalance, after transaction costs.

| Factor | Stock Ann.Ret | Stock p | Crypto Ann.Ret | Crypto p |
|--------|-------------|---------|---------------|---------|
| MOM12_1 | +1.63% | 0.87 | +9.07% | 0.58 |
| REV1 | -17.24% | 0.02 ** | -72.85% | 0.0007 *** |
| LOWVOL | -20.77% | 0.03 ** | -35.37% | 0.19 |
| LIQUID | +0.43% | 0.93 | +1.23% | 0.94 |
| PRICEMOM | +11.67% | 0.24 | +40.24% | 0.04 ** |

Key findings:
- **REV1 (1-month reversal) is robust in crypto** — winners keep winning, losers keep losing. Crypto is trending, not mean-reverting.
- **Low-vol anomaly is inverted** in our period — high-vol outperformed low-vol. Unusual, likely reflects 2019-2026 risk-on environment.
- **PRICEMOM (price vs SMA200) is significant in crypto** — trend factor works.
- **Classic 12-1 momentum has no premium** in our universe.

## Part 2: Strategy Decomposition (OLS Regression)

Regression: R = alpha + sum(beta_i * factor_i), factors standardized to z-scores.

### STR-B MACD Divergence (Stocks, 2732 signals)

| Term | Coefficient | t-stat | p-value | Significant? |
|------|-----------|--------|---------|-------------|
| Alpha | +0.8428 | 12.64 | <0.0001 | *** |
| MOM12_1 | -0.0949 | -1.04 | 0.298 | |
| REV1 | +0.1841 | 1.44 | 0.151 | |
| LOWVOL | +0.0663 | 0.98 | 0.326 | |
| LIQUID | -0.2018 | -3.02 | 0.0025 | *** |
| PRICEMOM | -0.0650 | -0.44 | 0.659 | |

R² = 0.0102 — factors explain only 1% of return variance.
**LIQUIDITY is the only significant factor.** Negative beta means less liquid stocks produce better signals.

### STR-I AdaptiveTrend (Stocks, 1613 signals)

| Term | Coefficient | t-stat | p-value |
|------|-----------|--------|---------|
| Alpha | +0.2219 | 6.13 | <0.0001 |
| LIQUID | +0.0729 | 1.87 | 0.0609 |
| All others | insignificant | | |

R² = 0.0031. Weak positive LIQUID exposure (opposite of STR-B).

### STR-I Crypto (528 signals)

| Term | Coefficient | t-stat | p-value |
|------|-----------|--------|---------|
| Alpha | +0.1448 | 1.44 | 0.15 |
| MOM12_1 | +0.2095 | 1.86 | 0.0623 |
| PRICEMOM | -0.2361 | -1.55 | 0.12 |

R² = 0.017. Weak momentum exposure, counterintuitive negative PRICEMOM.

## Key Conclusions

1. **Edge is idiosyncratic, not factor-driven.** R² of 0.3-1% across all strategies. Our pattern-based strategies find something factors don't capture.

2. **LIQUIDITY matters for STR-B.** Signals on less liquid stocks perform better (p=0.0025). Actionable: add liquidity filter to prioritize mid-cap signals.

3. **Crypto is trending.** REV1 is strongly negative (winners keep winning), PRICEMOM is significant. STR-I (trend-following) is well-suited for crypto.

4. **Factor premia are weak in stocks** during 2019-2026. Classic momentum has no premium. Low-vol anomaly is inverted. Factor-based stock strategies would underperform our pattern approaches.

5. **Alpha is real.** STR-B's alpha of 0.84R after controlling for all 5 factors confirms the walk-forward result. The edge is genuine.

## Links

- [[WF-20260801-walk-forward-validation]] — confirmed STR-B and STR-I edge out-of-sample
- [[STR-20260719-macd-histogram-divergence-weekly-assessment]] — STR-B hypothesis
- [[STR-20260728-adaptive-trend]] — STR-I hypothesis
