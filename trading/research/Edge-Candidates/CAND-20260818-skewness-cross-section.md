---
status: backtest_failed
source: web
edge_type: cross_sectional_return_skewness
composite_score: 58.0
confidence: medium
regime_fit: ['neutral', 'risk_on', 'caution']
created: 20260818
topic: research
has_quotes: false
tags: [factor, skewness, cross-sectional, academic, external]
---
# Edge Candidate: Cross-Sectional Return Skewness as a Hidden Factor

## Source
Web / academic research —
- "Skewness as a Hidden Driver of Anomaly Returns" (Alpha Architect summary, Aug 7 2026; original in 2026 Journal of Investing). The paper shows many anomaly portfolios carry latent **skewness** exposure not captured by standard Fama-French factors.
- "Skewness Effect in Commodities" (QuantPedia strategy): long the 3 assets with the *lowest* (most negatively skewed) returns outperforms — established precedent that low-skewness assets carry a premium.
- "Cross Asset Skew — A Trading Strategy" (Dean Markwick, Feb 2024): cross-sectional skew sorting is a tradeable, look-ahead-free signal across assets.
- 2026 meta-finding: a paper testing 153 documented equity anomalies finds an 8-factor coalition explains most, but several retain significant alpha — skewness is a candidate axis to disentangle which anomalies are real vs. artifacts of latent skew.

## Signal
- Compute rolling **historical return skewness** (e.g., 60-day / 120-day window of daily log returns) for every asset in the universe.
- Rank the cross-section each rebalance; the *lowest-skewness* (most negatively skewed) names have historically delivered a risk premium (compensation for crash risk), while *highest-skewness* (lottery-like, positively skewed) names underperform — consistent with the "betting against beta / lottery preference" literature.
- Current market context makes this timely: S&P 500 at all-time highs (SPX ~7,814), VIX ~15.3, F&G 62 (Greed). Complacent/low-vol regimes are exactly when positive-skew (lottery) assets get bid up and the low-skew premium widens — a skewness screen would tilt away from crowded momentum lottery names.

## Hypothesis
Investors systematically overpay for lottery-like (high positive skew) return profiles and underprice crash-insurance-like (negative skew) assets. Sorting the cross-section on realized skewness and going **long low-skew / short high-skew** captures this premium as a standalone factor, and — per the Aug 2026 paper — it also explains *part* of the alpha in existing anomalies (momentum, low-vol, etc.) that our factor screener already tests.

If true, this means:
1. Skewness is an **orthogonal** factor to the 10 currently screened (RSI14, REV1, LOWVOL, ATR_PCT, BB_WIDTH, PRICEMOM, VOL_ROC, ADX_TREND, LIQUID, MOM12_1) — none of which measure third-moment (skew) directly.
2. It can serve as a **new standalone factor** AND as a **confound-check** on existing significant factors (e.g., the stock screener found RSI14/REV1/LOWVOL/ATR_PCT/BB_WIDTH all SIGNIFICANT with *negative* annualized returns — could these be partially skew-driven?).

## Entry Rules
- **Strategy A (Long-Short Skew):** On a weekly rebalance, rank all liquid assets by 120-day return skewness. Long the bottom quintile (most negative skew), short the top quintile (most positive skew). Equal or inverse-vol weighting. Hold 1 week.
- **Strategy B (Skew-Filtered Long-Only):** As a screen overlay: from any buy list, exclude the top quintile of skewness (lottery names) — improves the quality of existing long-only / breakout entries.
- **Strategy C (Crypto Skew):** Apply the same ranking to the 35-asset Hyperliquid crypto universe. Crypto returns are heavily positively skewed (lottery demand), so the low-skew long leg may carry an especially clean premium. Note the existing crypto factor screener found RSI14 and REV1 ROBUST (negative returns) — a skewness factor is a natural complement.

## Exit Rules
- **Strategy A:** Weekly rebalance; exit all positions at next rebalance. No fundamental stop — purely systematic. Optional vol-target overlay.
- **Strategy B:** Exit when the underlying strategy's exit triggers OR the asset migrates into the top skewness quintile.
- **Strategy C:** Weekly rebalance, same as A.

## Score Breakdown
- Composite: 58.0
- Signal Strength: 11.0 (newly published academic backing + QuantPedia precedent; skewness is a distinct statistical moment not in our current screener)
- Confidence: medium (15 pts) — peer-reviewed + QuantPedia replication, but we have not yet confirmed in our own universe
- Data Quality: 15 (daily OHLC from yfinance 529 stocks + Hyperliquid 35 crypto; skewness is computed, no external feed needed)
- Actionable: 12 (weekly-rebalance long-short is straightforward; long-only overlay is trivial to add)
- Precedent: 10 (some_evidence — QuantPedia commodity skewness strategy + multi-asset skew literature; well-established behavioral basis)

## Regime Fit
['neutral', 'risk_on', 'caution'] — the low-skew premium is most pronounced in complacent/risk-on regimes (lottery demand peaks) but the long-short is designed to be regime-robust. Suppress in 'risk_off' (correlations unify, short leg squeezes).

## Testability
✅ **Fully testable with free data.** Skewness = third standardized moment of the daily log-return series over a rolling window — a one-liner in pandas (`returns.rolling(120).skew()`). No new data source required. Our existing factor_screener framework already ranks cross-sections and computes t-stats/p-values; adding a `SKEW` factor is a low-effort extension. Run the same pipeline (1806+ day stock history, 2159-day crypto history) and check significance.

**Overlap with engine:** Engine factor screener tests 10 factors, NONE of which is skewness. This is a genuinely new axis. It may also help explain *why* several existing factors show negative expected returns (possible latent-skew contamination).

## Recommended Pipeline Action
**PROMISING →** Add a `SKEW` factor (120-day rolling skewness, cross-sectional rank) to `scripts/validation/factor_screener.py` (or the research factor screener), run the standard significance test against the 529-stock and 35-crypto universes, and compare against the 10 existing factors for orthogonality (correlation of factor portfolios). If t-stat |≥2| and factor-portfolio correlation < 0.5 to existing factors, proceed to walk-forward long-short backtest. If it explains part of the RSI14/REV1/LOWVOL alpha, document as a confound. Highest-leverage new factor candidate of this cycle.

## Pipeline Results (20260818)
- **Scanner:** `scripts/validation/scanners/scanner_skew_crosssectional.py`
- **Phase 1A (Crypto, 35 assets):** 3622 signals, mean_r = -0.001, p_value = 0.9362, win_rate = 49.8%
- **Result:** BACKTEST FAILED — mean R ≤ 0. No edge found in weekly-rebalanced long-short skewness sorting on the crypto universe.
- **Stock backtest:** Timed out (529 stocks × weekly rebalance × skewness computation too slow). Crypto result sufficient to fail per pipeline rules.
- **Analysis:** The skewness factor may have academic validity as a slow-moving factor (monthly/quarterly rebalance), but at weekly rebalance with ATR stops, the edge is absent. The ATR-based stop mechanism may be incompatible with a factor that works via drift, not timing. A pure factor-mimicking portfolio (no stops, quarterly rebalance) might show different results — worth researching if revisited.
