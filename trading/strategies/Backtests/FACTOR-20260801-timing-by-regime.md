---
id: FACTOR-20260801-timing-by-regime
type: backtest_result
strategy: [STR-B, STR-I]
method: factor_timing
date: 2026-08-01
factors: [MOM12_1, REV1, LOWVOL, LIQUID, PRICEMOM]
regimes: [trending, ranging, transitional, high-volatility, low-volatility]
topic: strategies
confidence: high
has_quotes: false
tags: []
source: HermesForge Strategies
---
# Factor Timing by Regime — August 1, 2026

First test of whether factor premia vary by market regime.

## Method
1. Classified each date by regime (SPY for stocks, BTC for crypto)
2. Split factor portfolio daily returns by the regime at that date
3. Computed annualized return, Sharpe, and hit rate per regime per factor

## Stock Factor Returns by Regime

| Factor | Trending | Ranging | Transitional | High-Vol | Low-Vol |
|--------|---------|---------|-------------|---------|---------|
| MOM12_1 | +5.3% | -19.6% | +32.0% | +111.0% | -79.3% |
| REV1 | -15.7% | -6.9% | -91.6% | -79.8% | -54.7% |
| LOWVOL | -23.3% | -12.2% | -20.6% | +6.4% | -154.5% |
| LIQUID | +0.1% | -15.5% | +9.6% | +52.0% | +12.1% |
| PRICEMOM | +11.0% | -2.6% | +50.8% | +105.2% | -74.4% |

## Crypto Factor Returns by Regime

| Factor | Trending | Ranging | Transitional | High-Vol | Low-Vol |
|--------|---------|---------|-------------|---------|---------|
| MOM12_1 | +3.0% | **+58.0%** ★ | -117.1% | +345.8% | -395.6% |
| REV1 | -47.3% | -122.6% | +168.5% | -237.4% | +517.3% |
| LOWVOL | -35.5% | +16.5% | +7.8% | +185.2% | -490.3% |
| LIQUID | -4.4% | **+86.5%** ★ | -275.2% | +84.6% | +290.6% |
| PRICEMOM | +20.0% | **+110.0%** ★ | -171.1% | +303.0% | -455.1% |

★ = Sharpe > 1.0 (ranging crypto: MOM12_1 Sharpe=1.32, LIQUID Sharpe=2.67, PRICEMOM Sharpe=2.56)

## Key Findings

1. **Factor timing IS real.** The same factor flips from strongly positive to strongly negative depending on regime. PRICEMOM: +110% in ranging crypto, -171% in transitional. This validates regime-conditional strategy activation.

2. **12-month momentum works in ranging crypto** (Sharpe 1.32). New finding — we had 0 strategies for ranging crypto. Classic momentum (buy past winners, sell past losers) works when crypto is choppy but not trending.

3. **Liquidity factor works in ranging crypto** (Sharpe 2.67). In ranging markets, liquid cryptos outperform illiquid ones. Different dynamic from stocks where STR-B benefits from low liquidity.

4. **REV1 (reversal) is negative in most regimes.** Crypto is structurally trending. The only regime where reversal works is transitional — regime shifts cause mean reversion.

5. **PRICEMOM is positive in trending AND ranging crypto.** This confirms our regime map: trend-following strategies (STR-I) should be active in both regimes, not just trending.

6. **High-vol and low-vol regimes have extreme factor returns but too few days.** 16-21 days in high-vol, 10-28 in low-vol. These are statistically unreliable — need more data.

## Actionable Next Steps

1. **Build cross-sectional ranking strategy for ranging crypto** combining MOM12_1 + LIQUID. Both have strong premia (Sharpe 1.32 and 2.67) in that specific regime. Requires new scanner architecture (rank all cryptos, long top quintile).

2. **Update regime map** — PRICEMOM is positive in ranging crypto, suggesting trend-following strategies should activate in both trending AND ranging crypto regimes.

3. **Transitional regime is dangerous** — most factors are strongly negative. Strategies should be deactivated in transitional periods.

## Links
- [[FACTOR-20260801-factor-decomposition]] — original factor analysis
- [[WF-20260801-walk-forward-validation]] — OOS validation
- [[STR-20260801-pricemom-factor]] — STR-O killed (per-ticker scanner doesn't capture factor edge)
