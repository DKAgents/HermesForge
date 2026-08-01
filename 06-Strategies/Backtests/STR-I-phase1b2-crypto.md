---
type: backtest-result
strategy_id: STR-20260728-adaptive-trend
strategy_name: AdaptiveTrend
phase: 1B/2
asset_class: crypto
direction: long-only
universe: "Top 15 by Sharpe + dollar volume"
period_start: 2020-01-01
period_end: 2026-07-31
sharpe: 0.151
annual_return: 1.6
max_drawdown: -38.9
sortino: 0.137
calmar: 0.042
win_rate: 32.4
trade_count: 373
avg_hold_days: 13.4
equity_final: 110190
verdict: KILL
verdict_reason: "Sharpe 0.151, MDD -38.9%. Daily bars insufficient for crypto momentum. Paper edge depends on 6h bars."
data_limitations: "Daily bars (paper uses 6h), Hyperliquid perp markets, quarterly re-optimization"
produced_by: "[[Backtester]]"
tags: [backtest, phase1b2, STR-I, crypto, kill]
---

# STR-I Phase 1B/2 Results (Crypto)

## Decision: KILL

Daily bars are insufficient to capture crypto momentum. The paper's edge depends heavily on 6-hour bars (Sharpe 2.41 on H6 vs 1.63 on D1 per the paper's own ablation). The timeframe mismatch is structural, not parametric.

## Performance

| Metric | Phase 1B/2 | Paper (Full Strategy) |
|--------|-----------|----------------------|
| Annual return | +1.6% | +40.5% |
| Sharpe | 0.151 | 2.41 |
| Max drawdown | -38.9% | -12.7% |
| Win rate | 32.4% | N/A |

## Related
- [[STR-20260728-adaptive-trend|STR-I Strategy]]
- [[STR-I-phase1a]]
- [[STR-I-phase1b2-stocks]]
- [[FAIL-STR-I-crypto-daily-bars]]
- [[ADR-004-Phase1-Validation-Framework]]
