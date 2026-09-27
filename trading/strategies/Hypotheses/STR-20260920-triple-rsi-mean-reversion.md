---
id: STR-20260920-triple-rsi-mean-reversion
type: strategy
status: hypothesis
asset_class: stocks
venue: stocks
trade_style: swing
timeframe: daily
confidence: medium
last_reviewed: 2026-09-20
hypothesis_id: HYP-13
source: "@QuantifiedStrat (Oddmund Grotte)"
source_url: "https://x.com/quantifiedstrat/status/2101295243115000032"
gates_passed: [G0, G3]
eligible_assets: [SPY]
topic: strategies
has_quotes: false
tags: []
---
# Triple RSI Mean Reversion (HYP-13)

## Thesis

When SPY is in a long-term uptrend (above 200-MA) but experiencing
short-term capitulation (5-day RSI < 30, falling for 3 days), the
oversold condition mean-reverts with high probability once sellers
exhaust.

## Entry Criteria

1. 5-day RSI < 30
2. 5-day RSI falling for 3 consecutive days
3. 5-day RSI was < 60 three days ago (trend reset condition)
4. Close > 200-day moving average

## Exit Criteria

- Sell at close when 5-day RSI crosses above 50
- Stop: 2× ATR(14) below entry
- No time stop (RSI exit handles this)

## Backtest Results (SPY: 2018-10 to 2026-09)

| Metric | Value |
|--------|-------|
| Total trades | 18 |
| Win rate | 83.3% |
| Profit factor | 2.72 |
| Avg win | +131 bps |
| Avg loss | -241 bps |
| Max win | +517 bps |
| Max loss | -461 bps |
| Avg R (0.5% risk) | 1.38 |
| Signals/year | 2.3 |

## Gauntlet Status

- G0: ✅ median |return| 121 bps vs 8 bps threshold
- G3: ✅ cost drag 0.04R (2bps stock venue, negligible)
- G4: Not yet run (CPCV)
- Low signal frequency (2.3/yr) — ADR-004 borderline

## Discrepancy from Source

Tweet claims "~90% win rate." Our backtest shows 83.3%. Discrepancy
likely from different test period or exit rules. Our results are from
SPY daily bars via Alpaca, 2018-2026.

## Change Log

- 2026-09-20: Created from @QuantifiedStrat tweet. HYP-13 registered.
  Scanner built, backtest confirmed viable with 83% WR, 2.72 PF.