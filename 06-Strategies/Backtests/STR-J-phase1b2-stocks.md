---
type: backtest-result
strategy_id: STR-20260726-eufearia-cci-reversal
strategy_name: EUFEARIA CCI Reversal
phase: 1B/2
asset_class: stocks
direction: long-only
universe: "Top 15 by Sharpe + dollar volume"
period_start: 2020-01-01
period_end: 2026-07-31
sharpe: 0.491
annual_return: 1.5
max_drawdown: -3.5
sortino: 0.379
calmar: 0.428
win_rate: 40.3
trade_count: 159
avg_hold_days: 8.4
equity_final: 110164
verdict: WATCH
verdict_reason: "Sharpe 0.491, exceptionally low MDD -3.5%. Edge survives costs. Diversification value vs STR-I."
data_limitations: "Daily bars, survivorship bias, quarterly re-optimization"
produced_by: "[[Backtester]]"
tags: [backtest, phase1b2, STR-J, stocks, watch]
---

# STR-J Phase 1B/2 Results (Stocks)

## Exit Breakdown

| Exit Reason | Count | % |
|-------------|-------|---|
| Stop (ATR) | 85 | 53.5% |
| Time (10 bars) | 61 | 38.4% |
| Target (mean reversion) | 13 | 8.2% |

## Comparison with STR-I

| Metric | STR-J | STR-I |
|--------|-------|-------|
| Sharpe | 0.491 | 0.815 |
| Annual return | +1.5% | +5.8% |
| Max drawdown | -3.5% | -10.2% |
| Trades/year | 24 | 36 |

STR-I is stronger, but STR-J has significantly lower drawdown. Structurally uncorrelated: STR-I is trend-following, STR-J is mean-reversion.

## Related
- [[STR-20260726-eufearia-cci-reversal|STR-J Strategy]]
- [[STR-J-phase1a]]
- [[STR-I-phase1b2-stocks]]
- [[REGIME-ranging]]
- [[ADR-004-Phase1-Validation-Framework]]
