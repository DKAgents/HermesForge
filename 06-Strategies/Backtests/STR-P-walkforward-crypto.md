---
type: backtest-result
strategy_id: STR-P
strategy_name: Cross-Sectional Factor
phase: walk-forward
asset_class: crypto
direction: bidirectional
universe: 42 crypto symbols (full), 10 (optimization sample)
period_start: 2019-01-01
period_end: 2026-12-31
verdict: WATCH
verdict_reason: "Walk-forward shows statistically significant positive edge (p=0.03, CI excludes zero) but magnitude is small (OOS R=0.12 with costs). Positive in 4 of 5 windows. Edge is real but thin — needs monitoring. Below PASS threshold (R >= 0.6)."
data_limitations: "Daily bars, 42 crypto universe (Hyperliquid top), survivorship bias, batch scanner validation"
produced_by: "Walk-Forward Framework"
tags: [backtest, walkforward, STR-P, crypto, watch]
topic: strategies
confidence: high
has_quotes: false
source: HermesForge Strategies
---
# STR-P Walk-Forward Validation Results (Crypto)

## Method
Batch-mode walk-forward validation. 5 rolling windows (2-year train, 1-year test).
Optimization on 10-coin sample, testing on full 42-coin universe.
Transaction costs applied: 5bp round-trip (crypto).

## Results

### In-Sample (Full Period, Default Params)
- **938 signals**, avg R = 0.0739 (with costs)

### Out-of-Sample Per Window

| Window | Train R | Train N | OOS R | OOS N | Win Rate |
|--------|---------|---------|-------|-------|----------|
| 2022   | +0.1718 | 22      | **-0.0417** | 144   | 39%      |
| 2023   | +0.0265 | 56      | **+0.1285** | 150   | 37%      |
| 2024   | +0.1090 | 92      | **+0.2560** | 198   | 40%      |
| 2025   | +0.0289 | 136     | **+0.0620** | 228   | 32%      |
| 2026   | +0.1935 | 170     | **+0.1789** | 140   | 39%      |

### OOS Significance (All Windows Combined)
- **N = 860 signals**
- **Mean R = 0.1199** (with costs)
- **t-stat = 2.15, p-value = 0.0315**
- **95% CI = [0.0134, 0.2364]**
- **Verdict: ROBUST EDGE** (p < 0.05, CI excludes zero)

### Per-Window Verdict
- 2022: NO EDGE (negative R)
- 2023: FRAGILE EDGE (positive but small)
- 2024: ROBUST EDGE (highest R, 198 signals)
- 2025: POSSIBLE EDGE (positive but small, lowest win rate)
- 2026: FRAGILE EDGE (positive)

## Assessment

### Strengths
- Statistically significant positive edge after costs (p=0.03)
- Positive in 4 of 5 OOS windows
- High signal count (860 OOS signals = ~123/year)
- CI lower bound excludes zero (0.0134)

### Weaknesses
- Small magnitude (0.12R per trade with costs)
- Only marginally significant (p=0.03, not p<0.01)
- 2022 was negative (crypto bear market)
- Win rate below 40% in most windows
- Thin margin — small changes in costs or slippage could erase the edge

### Verdict: WATCH
Per ADR-004 Amendment 1:
- Walk-forward shows ROBUST EDGE (statistically significant)
- But OOS R = 0.12 is well below the 0.6 PASS threshold
- Edge is real but thin — monitor in live deployment
- Positive in 4/5 windows (meets the 2/3 sub-period requirement)
- The edge comes from factor timing (MOM12, LIQUID, PRICEMOM) which is theoretically grounded

## Related
- [[STR-20260801-crosssectional-factor|STR-P Strategy]]
- [[ADR-004-Phase1-Validation-Framework]]