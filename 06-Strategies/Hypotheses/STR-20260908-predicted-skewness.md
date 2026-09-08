---
status: watch
strategy_id: STR-20260908-SKEW-PREDICTED
scanner_alias: scan_skewp
scan_mode: batch
asset_class: stock
regime_best: [neutral, caution, risk_off]
regime_avoid: [risk_on]
base_risk: 0.25
---

# STR-20260908-SKEW-PREDICTED: Cross-Sectional Predicted Skewness Factor

## Source
Gong, Lynch & Ogden (June 2026), "Skewness Managed Portfolios," SSRN.

## Hypothesis
Cross-sectional forecasts of return skewness improve anomaly portfolio performance. Skewness is forecastable from firm characteristics (low profitability proxied by log price, poor recent returns, high volatility). By predicting next-period skewness and going long high-predicted-skewness stocks / short low-predicted-skewness stocks, the strategy captures a systematic edge orthogonal to standard factor models.

## Signal Rules
1. Compute 63-day rolling realized skewness for each stock
2. Fit cross-sectional OLS at the start of each 12-month block:
   - Target: future (21-day forward) realized skewness
   - Features: log price (size proxy), 6-month momentum, 1-month momentum, 20-day volatility, prior skew
3. Predict next-month skewness for all stocks
4. Long the top quintile (highest predicted skewness), short the bottom quintile
5. Monthly rebalance; 2x ATR stop, 1:2 risk:reward target

## Phase 1A Results
- Signals/yr: 2,512
- Mean R: 0.079 (p = 0.0, t = 6.79)
- Win rate: 40.6%
- Sub-periods positive: 3/3
- **Friction flagged** (avg R < 0.5)

## Walk-Forward Results
- OOS overall: mean R = 0.0457 (p = 0.0005) → **ROBUST EDGE** (verdict)
- Per-window OOS: 2022/2023/2026 = NO EDGE; 2024/2025 = ROBUST EDGE
- 3/5 windows statistically flat; edge concentrated in 2024-2025 bull regime

## Deploy Status
- **Status:** WATCH (experimental, 0.25% risk)
- **Rationale:** Statistically significant but economically tiny. Friction-flagged. Deployed at minimal risk as an overlay for later combination with other factors.
- **Risk:** 0.25% per position (below SOUL.md 1% maximum)
- **Regime:** Best in neutral/caution where skewness premium is strongest

## Files
- Scanner: `scripts/validation/scanners/scanner_skew_predicted.py`
- Sizing: `position_sizing.py` → `size_strategy_skewp`
- Registry: `regime_strategy_selector.py` → `STR-SKEWP`
- Candidate: `05-Research/Edge-Candidates/CAND-20260908-skewness-managed-anomalies.md`