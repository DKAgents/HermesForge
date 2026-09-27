---
id: STR-20260920-liquidity-sweep-wide
type: strategy
status: hypothesis
asset_class: crypto
venue: hyperliquid
trade_style: intraday_5m
timeframe: 5m
confidence: low
last_reviewed: 2026-09-20
hypothesis_id: HYP-12
parent_strategy: STR-Q-liquidity-sweep
gates_passed: [G0]
gates_failed: [G3]
eligible_assets: [AVAX, LINK]
topic: strategies
has_quotes: false
tags: []
source: HermesForge Strategies
---
# STR-QW: Liquidity Sweep — Wider Stops (HYP-12)

## Thesis

STR-Q's sweep detection edge is real (51% WR, 2.85 PF), but 0.104% median
risk on crypto perps can't absorb the 12 bps cost structure. Wider stops
dilute the cost: 0.25% risk → cost drops from 38% to 16% of target.

Per-asset analysis reveals AVAX and LINK pass G3 individually even though
the overall average fails.

## Entry Criteria (same as STR-Q)
- Liquidity sweep at structure level
- Confirmation: wick ratio, volume surge, penetration depth
- Quality score ≥ 60

## Differences from STR-Q
- Stop: 2× wider (next-higher TF structure level)
- Target: 3R from wider stop (scales proportionally)
- Eligible: AVAX, LINK only

## Per-Asset Results (Phase 1a)
| Asset | Net R | Trades | Win Rate |
|-------|-------|--------|----------|
| AVAX  | +0.323 | 18 | 78% |
| LINK  | +0.191 | 20 | 55% |
| OP    | −0.019 | 19 | 47% |
| DOGE  | −0.102 | 29 | 24% |
| ARB   | −0.260 | 20 | 40% |
| SOL   | −0.427 | 44 | 57% |
| ETH   | −0.577 | 41 | 54% |
| BTC   | −1.724 | 46 | 39% |

## Change Log
- 2026-09-20: Created as STR-Q variant. Phase 1a shows net R −0.55R avg,
  but AVAX and LINK individually positive. Promoted on those two only.