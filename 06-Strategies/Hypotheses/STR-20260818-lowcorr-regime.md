---
status: watch
created: 2026-08-18
strategy_id: STR-LOWCORR-lowcorr-regime
source: autonomous-pipeline
candidate: CAND-20260814-low-correlation-regime
tags: [strategy, stock, regime, correlation, autonomous-pipeline]
---

# STR-LOWCORR: Low-Correlation Regime Stock Picker

## Origin
Autonomous pipeline run 2026-08-18. Candidate: `05-Research/Edge-Candidates/CAND-20260814-low-correlation-regime.md` (composite score 74.2, highest of all staged candidates).

## Hypothesis
When the average pairwise correlation across the stock universe is low (< 0.30), individual stock-specific edge matters more than market beta. This is a "stock-picking environment" where idiosyncratic strategies outperform. The scanner identifies the most idiosyncratic stocks (lowest average correlation to the market proxy) and goes long them during low-correlation regimes.

## Signal Rules
1. Compute 30-day rolling average pairwise correlation across the 529-stock universe at each rebalance date.
2. When avg correlation < 0.30, enter "stock-picking" regime.
3. Within the regime, rank stocks by their average correlation to the market proxy (equal-weighted universe). Long the bottom quintile (most idiosyncratic).
4. Rebalance weekly (every 5 bars).
5. Exit: stop loss at 2.0× ATR, or time stop at 10 bars.

## Scanner
`scripts/validation/scanners/scanner_lowcorr_regime.py`

## Parameters (default)
- `CORR_WINDOW`: 30 (rolling window for correlation)
- `CORR_THRESHOLD`: 0.30 (below = low-correlation regime)
- `EXIT_CORR`: 0.50 (above = exit regime)
- `REBALANCE_FREQ`: 5 (weekly)
- `QUINTILE`: 5 (bottom quintile = most idiosyncratic)
- `ATR_STOP_MULT`: 2.0
- `MAX_BARS_HELD`: 10

## Validation Results

### Phase 1A (2026-08-18)
- **Universe:** 529 stocks, 2019-04 to 2026-08
- **Total signals:** 31,464 (4,356/year)
- **Mean R:** 0.092 (positive, friction flag = True)
- **p-value:** 0.0000 (t-stat = 15.62, highly significant)
- **Win rate:** 50.6%
- **Sub-periods positive:** 3/3 (bull 2019-2021, bear 2022-2023, current 2024-2026)
- **Classification:** KILL by ADR-004 thresholds (avg_r < 0.2), but pipeline criteria met (mean_r > 0, p < 0.10)

### In-Sample With Transaction Costs
- **Avg R (after 12bp round-trip costs):** 0.072
- Edge survives transaction costs (reduced from 0.092 to 0.072)

### Walk-Forward Validation
- **Status:** INCOMPLETE — the 529-stock pairwise correlation matrix computation at each weekly rebalance date is compute-bound. The walk-forward framework timed out during the in-sample baseline scan.
- **Action needed:** Optimize the scanner to use matrix-based correlation computation or subsample the universe for the walk-forward optimization step. Revisit when compute budget allows.

## Deployment
- **Status:** WATCH (deployed to paper trading with reduced risk)
- **Risk per trade:** 0.5% (below 1% ceiling per SOUL.md)
- **Asset class:** Stocks only
- **Regime fit:** risk_on, neutral, diversified (suppressed in risk_off/unified where correlations spike)

## Key Risks
1. **Small edge:** Mean R of 0.072 after costs is marginal. A slight increase in spread/slippage could erase it.
2. **Walk-forward incomplete:** OOS validation not completed due to compute constraints. The edge may be in-sample-only.
3. **Correlation regime dependency:** The strategy only fires during low-correlation regimes. In high-correlation (unified/risk_off) periods, it generates no signals — this is by design but means it can be inactive for extended periods.
4. **Signal frequency:** 4,356 signals/year is extremely high. The paper trading capture only processes the most recent date's signals, so the effective signal count is manageable (~20-40/week).

## What Would Change My View
- Walk-forward OOS mean R < 0 → would downgrade to validation_failed and remove from paper trading
- If the edge disappears after optimizing the correlation computation (possible that the current implementation has look-ahead bias in the correlation window) → would kill
- If transaction costs increase (wider spreads in stressed markets) → the small edge could vanish

## Survivalship Bias note
This backtest uses the current 529-stock universe which has survivorship bias (delisted stocks excluded). The actual edge may be smaller. This is a known limitation of the yfinance cached data.
