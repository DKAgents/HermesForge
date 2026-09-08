---
status: staged
source: web
edge_type: skewness_managed_anomalies
composite_score: 68.0
confidence: medium
regime_fit: ['risk_off', 'caution', 'neutral', 'risk_on']
created: 20260908
topic: academic
has_quotes: true
tags: [academic-paper, factor-investing, skewness, anomaly, cross-section, momentum, value, profitability, stage-3, external]
---

# Edge Candidate: Skewness-Managed Anomaly Portfolios — +5.45%/yr Enhancement to All Factors

## Source
**Academic Paper** — Gong, Lynch & Ogden (June 2026), "Skewness Managed Portfolios," SSRN. Covered by Alpha Architect (Aug 7, 2026) and Interactive Brokers Quant Blog (Aug 28, 2026).

### Key Finding
The authors studied **18 well-known anomalies** (value, size, momentum, profitability, investment, accruals, issuance, distress) and found that:

1. **Extreme right-tail returns dominate anomaly performance** — capping the 99th percentile observations substantially reduces returns and Sharpe ratios across ALL anomalies tested. A small number of outlier stocks do the heavy lifting.

2. **Skewness is forecastable** — using monthly cross-sectional regressions of realized skewness on lagged firm characteristics (volatility, momentum, prior return, size, industry, exchange indicators). The forecast is driven primarily by: low profitability, poor recent returns, and small market capitalization.

3. **Skewness management improves every anomaly tested:**
   - **Average improvement:** +5.45 percentage points annually in returns, +0.12 in Sharpe ratio
   - **During recessions:** +20.4% per year (vs +3.7% in expansions) — the edge STRENGTHENS in bad markets
   - **When volatility and credit spreads are elevated:** even larger improvements
   - **Mechanism:** Tilt long leg toward stocks with high expected skewness, short leg toward low expected skewness, within each anomaly sort

4. **The effect is NOT captured by standard linear factor models** — skewness represents an orthogonal dimension of returns.

| Metric | Value | Context |
|--------|-------|---------|
| Anomalies improved | 18/18 | Every anomaly tested |
| Avg annual return boost | +5.45% | Over standard sorts |
| Avg Sharpe improvement | +0.12 | Risk-adjusted |
| Recession boost | +20.4%/yr | vs +3.7% in expansions |
| Forecast drivers | Low profitability, poor returns, small cap | Cross-sectional |
| Data requirement | Daily returns from 5,000+ stocks | Minimum 2yr for reliable skewness |

## Signal
**A novel factor construction technique that enhances EVERY known anomaly by managing the skewness exposure of the long and short legs:**

1. Standard anomaly sorts (value, momentum, etc.) are implicitly exposed to lottery-stock skewness — rare extreme winners dominate returns.
2. By forecasting which stocks will have positively skewed returns (using the low-profitability, poor-recent-return, small-cap profile), you can tilt the long leg toward these stocks and the short leg away from them.
3. This produces systematically higher returns without changing the underlying anomaly signal — it's a portfolio construction technique, not a new anomaly.
4. **The edge is strongest in recessions and high-volatility regimes** — exactly when most factors decay and strategies fail.

## Hypothesis
**Skewness-managed anomaly portfolios systematically outperform standard anomaly portfolios because they capture the lottery-stock premium that linear factor models miss:**

1. **Transmission mechanism:** Investors overpay for positively skewed stocks (lottery demand) → these stocks have lower future returns → standard anomaly sorts inadvertently short these overpriced lottery stocks (because they're typically low profitability/small cap) → skewness management amplifies this by explicitly targeting them.

2. **Why it works in recessions:** During market stress, the lottery-demand premium intensifies (flight to fantasy — investors seek high-upside bets when broad market returns are poor). This makes skewness management even more effective.

3. **Our application:** We have 529 stocks via yfinance with daily data. We can compute realized skewness (rolling 60-day or 126-day), forecast next-month skewness using cross-sectional regression, and overlay this onto our existing momentum and value screens.

## Entry Rules
- **Not a standalone entry** — this is a portfolio construction overlay for existing anomaly-based strategies
- **Implementation:** For each existing stock signal (momentum long, value long, etc.), sort the long candidates into terciles by predicted skewness. Only take the top tercile (highest expected skewness).
- **For short signals:** Sort short candidates into terciles by predicted skewness. Only take the bottom tercile (lowest expected skewness — avoid shorting lottery stocks).
- **Alternatively:** Use skewness as a weighting scheme — weight long positions by predicted skewness score within the signal cohort.
- **Double-check:** Verify the predicted skewness signal is not just small-cap exposure (size-adjust the forecast)

## Exit Rules
- **Regime-based override:** When VIX > 25 (elevated vol regime), the skewness edge is strongest — increase allocation to skewness-managed vs standard portfolios
- **When VIX < 12 (complacent regime):** The skewness edge is weakest — reduce or revert to standard sorts
- **No explicit stop loss** — this is a portfolio construction technique, not a directional trade

## Score Breakdown
- **Composite:** 68.0
- **Signal Strength:** 22.0 / 30 — Rigorous academic study with strong empirical results. 18 anomalies tested, every one improved. The recession result (+20.4%/yr) is particularly compelling for current macro environment (yields surging, oil shock, potential recession).
- **Confidence:** Medium (16) — Academic papers often overstate significance (publication bias). Need to replicate with our data universe. The forecast model uses characteristics we don't directly have (institutional ownership, industry indicators may differ).
- **Data Quality:** 15 (moderate — daily returns for 529 stocks via yfinance is sufficient for computing realized skewness. Cross-sectional regression requires 60+ stocks minimum per month. 529 stocks gives reasonable sample.)
- **Actionable:** 13 (yes — can be implemented as an enhancement to our existing momentum screen (STR-Q, STR-L). Doesn't require new data feeds, just a new computation layer.)
- **Precedent:** 2 (some_evidence — skewness has been studied before. Skewness-managed portfolios is novel. The broad-factor improvement result is new.)

## Regime Fit
['risk_off', 'caution', 'neutral', 'risk_on'] — The edge is REGIME-ADAPTIVE by design. It works in ALL regimes but is strongest in risk_off/caution (recessions, high vol). This is its key advantage: it doesn't require regime prediction, it's a structural improvement to HOW we construct portfolios regardless of regime.

## Testability
✅ **Fully testable with free data:**
- 529 stocks via yfinance (2014-2026 daily data gives 12 years × 529 = ~6,300 stock-years)
- Compute realized skewness: rolling 60-day skew of daily returns for each stock
- Cross-sectional forecast: regress next-month realized skewness on lagged characteristics (size, prior 6-month return, volatility, profitability proxy)
- Apply to existing STR-Q (momentum) and STR-L (relative strength) long/short universes
- Compare: standard momentum long/short vs skewness-enhanced momentum long/short
- Test across VIX quintiles to validate the recession-strengthening result

## Overlap with Existing Candidates
- **CAND-20260818-factor-crowding-decay.md:** COMPLEMENTS in reverse. The decay candidate shows that crowded factors underperform. The skewness candidate shows HOW to improve factors even when crowded (by managing their lottery-stock exposure).
- **STR-Q (Momentum):** DIRECTLY APPLICABLE — can enhance STR-Q by skewness-weighting the long universe.
- **All 18 anomaly categories tested:** The paper tests value, momentum, profitability, investment, accruals, issuance, distress — this covers our entire factor suite.

## Recommended Pipeline Action
**PROMISING** — Stage for pipeline processing. Priority: HIGH:

1. **Phase 0:** Implement realized skewness computation in our data pipeline (rolling 60-day skew on daily returns for all 529 stocks)
2. **Phase 1A:** Cross-sectional regression to validate forecast power of characteristics (size, momentum, vol) in our universe
3. **Phase 1B:** Backtest skewness-enhanced STR-Q vs standard STR-Q (2014-2026)
4. **Phase 2:** Deploy as structural overlay if walk-forward confirms significance

This is NOT a new strategy — it's a structural improvement to HOW we build strategies. If validated, it enhances our ENTIRE factor-based approach.