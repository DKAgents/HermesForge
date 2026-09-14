---
id: G3-REPORT-2026-09-14
type: report
analyzed: STR-Q-liquidity-sweep
gates: [G0, G3]
method: gauntlet
generated_utc: 2026-09-14
display_tz: America/Los_Angeles
---

# G3 Execution-Realism Report — STR-Q Liquidity Sweep

Re-runs STR-Q backtest results through the gauntlet's cost model, with
venue-correct cost assumptions. Two findings that materially change the
picture for US-121.

## Method

- G0 (cost screen): median |move| over horizon vs gross-capture-needed (4× all-in cost)
- G3 (execution realism): apply per-trade cost drag = all-in-cost-bps / risk-as-fraction-of-price, compute net R, PF, edge retention.
- Pass G3 = realistic retains ≥60% of optimistic edge AND pessimistic net PF > 1.0

## Cost models (venue-correct)

| Venue | All-in round trip | Rationale |
|---|---|---|
| US equities | 2.0 bps | zero commission + spread/slippage, no funding |
| Hyperliquid perps | 12.0 bps | 9.0 taker fees + 2.5 slippage + 0.5 funding |

## Results

### Stocks — PASS G3

| File | Trades | Med risk | Opt R | Net R | Retention | Net PF | Verdict |
|---|---|---|---|---|---|---|---|
| stocks-phase1a | 313 | 0.136% | +0.864 | +0.670 | 78% | 2.39 | ✅ PASS |
| stocks-deep-phase1a | 826 | 0.167% | +0.587 | +0.426 | 73% | 1.74 | ✅ PASS |

### Crypto — FAIL G3 (structurally dead)

| File | Trades | Med risk | Opt R | Net R | Retention | Net PF | Verdict |
|---|---|---|---|---|---|---|---|
| crypto-phase1a | 219 | 0.104% | +0.814 | −1.102 | −135% | 0.32 | ❌ FAIL |

## Root cause

STR-Q uses tight structure stops (median 0.10–0.17% of price). At 12-bps
crypto perp costs, the round trip consumes ~1.16 R in drag — more than the
entire risk unit. The optimistic +0.814 R edge cannot survive a cost that
exceeds the stop distance. At 2-bps equity costs the drag is only ~0.15 R,
so the stock strategy retains 73–78% of edge.

## Implications for US-121

1. **The size-increase question is moot for crypto STR-Q.** No position-size
   increase can rescue a strategy that is net −1.10 R after costs. Size is a
   multiplier; a negative-expectancy strategy loses more, faster, when sized up.

2. **Stock STR-Q remains the candidate.** Net +0.43 to +0.67 R after costs is
   a real, cost-robust edge. If US-121's evidence bar is ever met, it will be
   met by the stock strategy — not crypto.

3. **Unlock conditions still unmet.** Paper trades = 0 (no OOS sample),
   CONFIRMATION_BARS not frozen, quality weights unvalidated, no ADR.

## Recommended next steps (evidence accumulation, not implementation)

- Drop STR-Q-crypto from the paper-trading queue (G3-fatal).
- Run STR-Q-stocks in paper trading to begin the ≥200 OOS trade sample.
- Freeze CONFIRMATION_BARS at a single value before the paper run begins.

## Status

US-121 remains **blocked**. This report is evidence, not implementation.
No position-sizing code changed.