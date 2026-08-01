---
type: backtest-result
strategy_id: STR-20260728-adaptive-trend
strategy_name: AdaptiveTrend
phase: 1B/2
asset_class: stocks
direction: long-only
universe: "Top 15 by Sharpe + dollar volume"
period_start: 2020-01-01
period_end: 2026-07-31
sharpe: 0.815
annual_return: 5.8
max_drawdown: -10.2
sortino: 0.940
calmar: 0.564
win_rate: 44.5
trade_count: 238
avg_hold_days: 21.2
equity_final: 144542
verdict: PASS
verdict_reason: "Sharpe > 0.5, acceptable MDD, edge survives transaction costs"
data_limitations: "Daily bars (paper uses 6h), survivorship bias, quarterly re-optimization"
produced_by: "[[Backtester]]"
tags: [backtest, phase1b2, STR-I, stocks, pass]
---

# STR-I Phase 1B/2 Results (Stocks)

## Implementation

- Walk-forward backtest: Quarterly parameter re-optimization (L, theta, alpha, max_bars) on trailing 6-month window
- Asset selection: Sharpe-ratio gate (>=0.3) + dollar-volume ranking, top 15 selected
- Transaction costs: Stocks 0.15% per side
- Monthly rebalance without closing positions

## Performance

| Metric | Phase 1B/2 | Paper (Full Strategy) |
|--------|-----------|----------------------|
| Annual return | +5.8% | +40.5% |
| Sharpe | 0.815 | 2.41 |
| Max drawdown | -10.2% | -12.7% |
| Win rate | 44.5% | N/A |

## Critical Bug Fix

Trailing stop order-of-operations bug found and fixed: scanner was updating ATR stop BEFORE checking if it was hit, causing premature exits. Fix: check old stop first, then update.

## Related
- [[STR-20260728-adaptive-trend|STR-I Strategy]]
- [[STR-I-phase1a]]
- [[STR-I-phase1b2-crypto]]
- [[ADR-004-Phase1-Validation-Framework]]
- [[REGIME-trending]]
