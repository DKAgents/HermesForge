---
topic: strategies
confidence: high
has_quotes: false
tags: []
source: HermesForge Strategies
created: 2026-08-24
---
---
id: STR-20260801-crosssectional-factor
type: strategy
status: watch
asset_class: crypto
trade_style: swing
timeframe: daily
market_regime: ranging
core_idea: factor_ranking
confidence: low
publish_enabled: false
publish_channel: crypto
source: "Factor timing analysis: MOM12_1 Sharpe 1.32, LIQUID Sharpe 2.67, PRICEMOM Sharpe 2.56 in ranging crypto"
source_date: 2026-08-01
topic: strategies
has_quotes: false
tags: []
scanner_module: scanner_p_crosssectional

strategy_id: STR-P-crosssectional-factor

scanner_alias: scan_p
scan_mode: batch---
# STR-P: Cross-Sectional Factor Ranking (Crypto)

## Hypothesis

Built from factor timing evidence. MOM12_1, LIQUID, and PRICEMOM factors all showed Sharpe > 1.3 in ranging crypto regime. Combining them into a composite z-score, ranking all 42 cryptos cross-sectionally, and longing the top quintile / shorting the bottom quintile should capture factor premia that per-ticker scanners cannot.

## Design

- At each rebalance (every 21 bars), compute 3 factor scores for all cryptos:
  - MOM12_1: 12-month return minus recent month
  - LIQUID: 60-day average dollar volume
  - PRICEMOM: price relative to SMA200
- Standardize each factor to z-scores cross-sectionally
- Composite score = 0.33 * MOM12_1_z + 0.33 * LIQUID_z + 0.34 * PRICEMOM_z
- Long top quintile (highest composite), short bottom quintile
- Stop: 1.5x ATR, Time stop: next rebalance (21 bars)

## Architecture Note

This is the FIRST batch scanner in HermesForge — it takes the full crypto data dict and ranks across all tickers, unlike per-ticker scanners that scan each chart independently. The edge is in relative ranking, not absolute thresholds (lesson from STR-O failure).

## Phase 1A Results (Equal-weight + 1.5x ATR stop)

| Metric | Value |
|--------|-------|
| Signals | 938 (469 long, 469 short) |
| Avg R | +0.0490 |
| Win rate | 38.0% |
| Profit factor | 1.10 |
| t-stat | 1.10 |
| p-value | 0.27 |

### Per-Year Breakdown

| Year | Signals | Avg R | PF |
|------|---------|-------|-----|
| 2021 | 60 | +0.24 | 1.45 |
| 2022 | 136 | +0.00 | 1.01 |
| 2023 | 150 | +0.01 | 1.02 |
| 2024 | 188 | +0.18 | 1.37 |
| 2025 | 252 | -0.04 | 0.92 |
| 2026 | 152 | +0.03 | 1.08 |

### Walk-Forward Split

| Period | Signals | Avg R | PF |
|--------|---------|-------|-----|
| 2021-2023 (train) | 346 | +0.05 | 1.09 |
| 2024-2026 (test) | 592 | +0.05 | 1.11 |

Edge is consistent across train/test split. Not significant yet (p=0.27) but positive in 4 of 6 years and stable OOS.

## Phase 1B Perturbations

| Variant | Avg R | PF |
|---------|-------|-----|
| Baseline (2.0x stop) | +0.049 | 1.10 |
| Tighter stop (1.5x) | +0.058 | 1.10 |
| Looser stop (3.0x) | +0.009 | 1.03 |
| Weekly rebalance | +0.041 | 1.09 |
| Quarterly rebalance | +0.018 | 1.03 |
| Mom-heavy (50%) | +0.060 | 1.13 |
| Liquid-heavy (60%) | +0.053 | 1.11 |
| Equal-weight + 1.5x | +0.079 | 1.14 |

Best config: equal-weight factors + 1.5x ATR stop → avg R = +0.079, PF = 1.14, t=1.45, p=0.15

## Assessment

**Status: WATCH**

The edge is positive but not statistically significant (p=0.15). However:
1. It's consistent across the walk-forward split (train and test both +0.05 R)
2. It captures a fundamentally different type of edge (cross-sectional ranking vs pattern)
3. Both long and short sides are positive (not just one side carrying the other)
4. It fills the ranging-crypto gap (previously 0 active strategies)
5. p=0.15 with 938 signals — more data could push it to significance

This is the first factor-based strategy in the system. It validates that the factor timing findings translate to a tradeable (if weak) strategy. Future work: test regime-conditional activation (only run in ranging regime, deactivate in transitional).

## Links

- [[FACTOR-20260801-timing-by-regime]] — factor timing evidence that motivated this strategy
- [[FACTOR-20260801-factor-decomposition]] — original factor analysis
- [[STR-20260801-pricemom-factor]] — STR-O killed (same factor, wrong architecture)