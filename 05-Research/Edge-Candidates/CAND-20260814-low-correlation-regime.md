---
status: watch
source: correlation
edge_type: low_correlation_regime
composite_score: 74.2
confidence: high
regime_fit: ['risk_on', 'neutral']
created: 20260814
topic: research
has_quotes: false
tags: []
---
# Edge Candidate: Diversified market: avg correlation 0.21 (stock-picking environment)

## Source
correlation scanner

## Signal
Avg 30d correlation = 0.208

## Hypothesis
Low correlation = individual stock edge matters. Best time for stock-specific strategies (STR-A, STR-B, STR-I). Sector rotation and factor strategies work well here.

## Entry Rules
Run stock-picking scanners (MACD divergence, adaptive trend, pullback to MA). Focus on stocks with idiosyncratic catalysts.

## Exit Rules
Continue until correlation rises above 0.5.

## Score Breakdown
- Composite: 74.2
- Signal Strength: 9.2
- Confidence: high (25 pts)
- Data Quality: 15
- Actionable: 15
- Precedent: 10

## Regime Fit
['risk_on', 'neutral']

## Recommended Pipeline Action
PROMISING — proceed to full backtest and walk-forward validation.

## Pipeline Results (20260818)
- **Scanner:** `scripts/validation/scanners/scanner_lowcorr_regime.py`
- **Phase 1A (529 stocks):** 31,464 signals, mean_r = 0.092, p_value = 0.0000, t_stat = 15.62, win_rate = 50.6%
- **Sub-periods positive:** 3/3 (bull, bear, current)
- **In-sample with costs:** avg_r = 0.072 (survives 12bp transaction costs)
- **Walk-forward:** INCOMPLETE — 529-stock pairwise correlation matrix is compute-bound, timed out. OOS validation deferred.
- **Deployment:** WATCH status, 0.5% risk per trade. Deployed to paper trading.
- **Vault note:** `06-Strategies/Hypotheses/STR-20260818-lowcorr-regime.md`
- **Analysis:** Edge is real but small (friction_flag True). The strategy identifies idiosyncratic stocks during low-correlation regimes — the hypothesis that stock-picking matters more when correlations are low is supported by the data. However, the small mean R (0.072 after costs) means the edge is marginal. Walk-forward OOS validation is needed when the scanner is optimized for compute.
