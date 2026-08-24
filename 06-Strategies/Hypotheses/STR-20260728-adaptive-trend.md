---
topic: strategies
confidence: high
has_quotes: false
tags: []
source: HermesForge Strategies
created: 2026-08-24
---
---
id: STR-20260728-adaptive-trend
type: strategy
status: live
asset_class: multi
trade_style: trend
timeframe: 6h_crypto_daily_stocks
market_regime: trending
core_idea: momentum
direction: bidirectional
confidence: high
publish_enabled: true
publish_channel: crypto
source: arxiv_2602.11708
source_authors: Duc Bui, Thanh Nguyen
source_title: "Systematic Trend-Following with Adaptive Portfolio Construction: Enhancing Risk-Adjusted Alpha in Cryptocurrency Markets"
source_published: 2026-02-12
evidence_links:
  - arxiv_2602.11708
  - Table1_OOS_Performance
  - Table2_Regime_Conditional
  - Table3_Ablation
  - Table5_Timeframe_Comparison
  - Table6_Statistical_Significance
last_reviewed: 2026-07-28
created: 2026-07-28
updated: 2026-07-28
tags: [strategy, hypothesis, momentum, trend-following, atr, trailing-stop, crypto, 6h, bidirectional]
topic: strategies
has_quotes: false
source: HermesForge Strategies
scanner_module: scanner_i_adaptive_trend
scanner_alias: scan_i

strategy_id: STR-I-adaptive-trend
scanner_alias: scan_i---

# AdaptiveTrend — Systematic Momentum + ATR Trailing Stop on 6-Hour Bars

## Thesis

Cryptocurrency markets exhibit pronounced momentum effects and regime-dependent volatility. AdaptiveTrend exploits this through an intermediate-frequency (6-hour) momentum signal combined with a dynamic ATR-based trailing stop that adapts to local volatility regimes. The trailing stop is the strategy's most critical component — the ablation study shows removing it drops Sharpe from 2.41 to 1.68 and increases max drawdown from -12.7% to -22.4%.

The 6-hour timeframe is optimal because it balances signal fidelity against transaction costs. Higher frequencies (H1, H4) suffer excessive turnover; lower frequencies (H8, H12, D1) miss short-lived crypto momentum. H6 also aligns with the 8-hour funding rate cycle on perpetual swap markets.

The strategy is bidirectional (long + short), with an asymmetric 70/30 long-short capital allocation reflecting crypto's structural positive drift. The original paper reports Sharpe 2.41, annualized return 40.5%, max drawdown -12.7% over 36 months out-of-sample (2022-2024), statistically significant vs. all benchmarks (p < 0.05).

## Implementation Scope (Phase 1A)

**Phase 1A implements the signal generation module only** — momentum entry + ATR trailing stop per-asset scanning. The portfolio-level components (market-cap filtering, Sharpe-ratio selection, 70/30 allocation, monthly rebalancing) are deferred to Phase 1B/2.

### Data Requirements

- **Timeframe:** Daily OHLCV bars (for both stocks and crypto in Phase 1A)
  - Original paper uses 6h bars; deferred to Phase 1B (Hyperliquid 2h → 3:1 resample)
  - Daily bars chosen for maximum history (7+ years) and pipeline consistency
- **Universe (Stocks):** 529 tickers (full S&P 500 + ETFs + extras) via yfinance
- **Universe (Crypto):** 42 Hyperliquid perpetual markets (fetched separately)
- **History:** Back to 2019 (stocks) / 2020 (crypto)
- **No market-cap data required for Phase 1A** (deferred to Phase 1B)

## Entry Criteria

### Momentum Signal (every 6-hour bar)

Compute momentum over lookback window L:

```
MOM_t = (P_t - P_{t-L}) / P_{t-L}
```

- **Long entry:** MOM_t > theta_entry
- **Short entry:** MOM_t < -theta_entry

Parameters L (lookback) and theta_entry (threshold) are optimized monthly in the full strategy. For Phase 1A, parameters were optimized via grid sweep (320 combinations on 19-ticker representative sample, 2026-07-26):
- L = 10 (≈ 2 weeks of daily bars; swept from [10, 20, 30, 50])
- theta_entry = 0.20 (20% momentum threshold; swept from [0.05..0.20])
- alpha = 2.0 (tighter stop = smaller losses; swept from [2.0..3.5])
- max_bars = 120 (longer hold for trends to develop; swept from [40..120])
- SMA200 trend filter (long above, short below)
- LONG_ONLY = True for stocks (shorts structurally negative: -0.135 avg R, 29.4% win rate)

### ATR Computation

- ATR computed over k = 14 periods on 6-hour bars
- Used for both trailing stop distance and risk-per-unit calculation

### Initial Stop (at entry)

- **Long:** Stop = P_{t0} - alpha * ATR_t0
- **Short:** Stop = P_{t0} + alpha * ATR_t0
- alpha = 2.5 (optimal per paper; robust range 2.0-3.5)

### Target Price (for R:R calculation)

The strategy does not use a fixed target — exits are via trailing stop only. For Phase 1A R:R calculation, use a notional target based on the momentum projection:
- **Long target:** P_t0 * (1 + |MOM_t| * 3) (3x the momentum that triggered entry)
- **Short target:** P_t0 * (1 - |MOM_t| * 3)

This is a proxy for Phase 1A signal quality measurement only. The actual exit is the trailing stop.

## Exit Criteria

### Dynamic ATR Trailing Stop

Once a position is opened at t0:

**Longs:**
```
S_t = max(S_{t-1}, P_t - alpha * ATR_t)
Exit when P_t < S_t
```

**Shorts (symmetric):**
```
S_t = min(S_{t-1}, P_t + alpha * ATR_t)
Exit when P_t > S_t
```

Key properties:
- Stop level monotonically tightens during favorable moves (locks in profit)
- Stop distance adapts to local volatility via ATR (tighter in low-vol, wider in high-vol)
- No fixed target — the trail determines the exit

### Phase 1A Scanner Output

For Phase 1A, the scanner simulates the full position lifecycle per-asset:
1. Find all momentum entry signals in the 6h history
2. For each entry, simulate the trailing stop until exit
3. Record entry, exit, and realized R:R
4. Return the most recent signal (if today's bar triggered an entry)

## Position Sizing

- Risk per trade: 1% of equity (HermesForge hard rule ceiling)
- Portfolio heat limit: 5% (deferred to Phase 1B)
- Equal weighting within legs (deferred to Phase 1B)

## Risk Management

- Primary risk control = dynamic ATR trailing stop
- Monthly parameter re-optimization (deferred to Phase 1B)
- Market-cap + Sharpe asset selection (deferred to Phase 1B)
- Hard per-trade risk: 1% of equity
- Portfolio heat: 5% max (deferred)

## Key Parameters

|| Parameter | Symbol | Phase 1A Value | Full Strategy |
||-----------|--------|----------------|---------------|
|| Timeframe | - | Daily (6h deferred to 1B) | 6h |
|| Momentum lookback | L | 10 (swept) | Optimized monthly |
|| Entry threshold | theta | 0.20 (swept) | Optimized monthly |
|| ATR multiplier | alpha | 2.0 (swept) | 2.5 (re-optimized) |
|| ATR periods | k | 14 | 14 |
|| Trend filter | - | SMA200 (long above, short below) | N/A (market-cap filter) |
|| Direction | - | Long only (stocks) | Long + Short |
|| Max bars held | - | 120 (swept) | Trailing stop only |
|| Allocation | lambda | N/A (per-asset) | 0.70 (70/30) |
|| Long candidates | K_L | All 529 (no filter) | Top 15 by mkt cap |
|| Short candidates | K_S | Disabled (long-only) | Bottom 15 by mkt cap |
|| Sharpe gate (Long) | gamma_L | N/A | >= 1.3 |
|| Sharpe gate (Short) | gamma_S | N/A | >= 1.7 |
|| Rebalance | - | None | Monthly (1st day) |
|| MIN_RR | - | 1.5 | N/A (trailing stop exit) |

## Published Performance (Full Strategy, 2022-2024 OOS, net of costs)

| Metric | AdaptiveTrend (70/30) |
|--------|----------------------|
| Annualized Return | 40.5% |
| Annualized Volatility | 16.8% |
| Sharpe Ratio | 2.41 |
| Maximum Drawdown | -12.7% |
| Calmar Ratio | 3.18 |
| Sortino Ratio | 3.62 |

### Regime-Conditional

| Regime | Ann. Return | Sharpe | Max DD |
|--------|-------------|--------|--------|
| Bull | +68.3% | 3.42 | -7.1% |
| Sideways | +18.7% | 1.87 | -9.4% |
| Bear | -4.2% | -0.31 | -12.7% |

### Ablation (contribution of each component)

| Configuration | Sharpe | MDD |
|--------------|--------|-----|
| Full AdaptiveTrend | 2.41 | -12.7% |
| w/o Dynamic Trailing Stop | 1.68 | -22.4% |
| w/o Market Cap Filter | 2.05 | -17.8% |
| w/o Sharpe Selection | 1.92 | -19.1% |
| w/o Asymmetric Allocation | 2.12 | -14.3% |
| Fixed Parameters (no opt.) | 1.34 | -28.6% |

## Graph Properties

produced_by:: [[Backtester]]
validated_by:: [[ADR-004-Phase1-Validation-Framework]]
governed_by:: [[RISK_RULES]], [[ADR-001-Model-Routing-Strategy]]
regime_node:: [[REGIME-trending]]
correlates_with:: [[STR-20260726-eufearia-cci-reversal|STR-J (uncorrelated diversifier)]]
tested_in:: [[STR-I-phase1a]], [[STR-I-phase1b2-stocks]], [[STR-I-phase1b2-crypto]]

## Phase 1A Validation Results (2026-07-26)

| Metric | Stocks (529 tickers, daily) |
|--------|---------------------------|
| Total signals | 1,730 |
| Signals/year | 266.3 |
| Avg R | +0.231 |
| Median R | -0.230 |
| Win rate | 43.2% |
| Sub-periods positive | 3/3 (bull +0.172, bear +0.193, current +0.305) |
| Best trade | INTC +11.09R (Apr 2026) |
| Classification | ⚠️ WATCH |

**Decision:** Advance to Phase 1B with caution flag (friction: avg R < 0.5, verify after costs).

**Key findings:**
1. Long-only is essential for stocks — shorts had avg R = -0.149 (29.4% win rate) even with trend filter
2. SMA200 trend filter is critical — eliminates counter-trend noise
3. Theta=0.20 (20% momentum) is optimal for daily bars — lower values generate too much noise
4. Alpha=2.0 (tighter stop) outperforms 2.5 — smaller losses when wrong
5. Max_bars=120 allows trends to fully develop — shorter windows cut winners short
6. Top performers: NVDA (+1.15 avg R), HOOD (+1.06), INTC (+0.91), MRNA (+0.90)

## Limitations & Caveats

1. Phase 1A uses optimized-but-fixed parameters — the full strategy re-optimizes monthly. Paper ablation shows fixed params drop Sharpe to 1.34.
2. Phase 1A does not implement market-cap filtering or Sharpe-ratio selection — all 529 stocks scanned equally. Bottom-tier stocks (F, KLAC, FIX) drag down average.
3. Phase 1A does not implement the 70/30 portfolio allocation — each asset scanned independently.
4. Daily bars used instead of 6h — the paper found H6 optimal (Sharpe 2.41 vs 1.63 for daily). 6h deferred to Phase 1B.
5. Transaction costs not modeled in Phase 1A (deferred to backtest module).
6. Strategy is long-only for stocks — bidirectional (long+short) deferred to Phase 1B with crypto.
7. Friction flag active (avg R = 0.231 < 0.5) — must verify edge survives commission + slippage in Phase 1B.

## Open Questions

1. ~~Should Phase 1A use theta=0.02 as a reasonable default, or sweep multiple thresholds?~~ → Resolved: theta=0.10-0.20 optimal via grid sweep
2. ~~Is alpha=2.5 appropriate for all 42 markets, or should it vary by asset volatility?~~ → Resolved: alpha=2.0-2.5 optimal; varies quarterly via walk-forward
3. ~~Should the scanner simulate full trailing stop lifecycle in Phase 1A, or just report entry signals with initial stop?~~ → Resolved: full lifecycle simulation
4. ~~How to handle the 70/30 allocation in the per-asset scanner model?~~ → Resolved in Phase 2: long-only for both stocks and crypto (shorts proven negative)

## Phase 1B/2 Validation Results (2026-07-26)

### Implementation

- **Walk-forward backtest:** Quarterly parameter re-optimization (L, theta, alpha, max_bars) using trailing 6-month window
- **Asset selection:** Sharpe-ratio gate (≥0.3 long, ≥0.5 short) + dollar-volume ranking (market-cap proxy), top 15 selected
- **Portfolio construction:** Long-only for both stocks and crypto (shorts proven negative in Phase 1A)
- **Risk management:** 1% risk per trade, 15% max portfolio heat, ATR trailing stop
- **Transaction costs:** Stocks 0.15%/side, Crypto 0.07%/side
- **Monthly rebalance:** Universe re-selection and parameter update without closing existing positions
- **Backtest engine:** `scripts/validation/run_phase1b2.py`

### Stocks Performance (2020-01 to 2026-07, 6.55 years)

| Metric | Phase 1B/2 Result | Paper (Full Strategy) |
|--------|-------------------|----------------------|
| Annual return | +5.8% | +40.5% |
| Annual volatility | 7.2% | 16.8% |
| Sharpe ratio | 0.815 | 2.41 |
| Sortino ratio | 0.940 | 3.62 |
| Max drawdown | -10.2% | -12.7% |
| Calmar ratio | 0.564 | 3.18 |
| Win rate | 44.5% | N/A |
| Total trades | 238 | N/A |
| Avg hold | 21.2 days | N/A |
| Final equity | $144,542 | N/A |

### Crypto Performance (2020-01 to 2026-07, 5.94 years)

| Metric | Phase 1B/2 Result | Paper (Full Strategy) |
|--------|-------------------|----------------------|
| Annual return | +1.6% | +40.5% |
| Annual volatility | 15.6% | 16.8% |
| Sharpe ratio | 0.151 | 2.41 |
| Sortino ratio | 0.137 | 3.62 |
| Max drawdown | -38.9% | -12.7% |
| Calmar ratio | 0.042 | 3.18 |
| Win rate | 32.4% | N/A |
| Total trades | 373 | N/A |
| Avg hold | 13.4 days | N/A |
| Final equity | $110,190 | N/A |

### Phase 1B/2 Decision

**Stocks: ✅ PASS** — Sharpe 0.815 with -10.2% max drawdown over 6.5 years. Positive, stable, low-volatility edge. The daily-bar adaptation captures meaningful trend persistence in equities. The 5.8% annual return is modest but the risk-adjusted profile (Calmar 0.564, Sortino 0.940) is acceptable for a systematic strategy. Advance to Phase 3 (robustness testing).

**Crypto: ❌ KILL** — Sharpe 0.151 with -38.9% max drawdown. The strategy barely outperforms cash on crypto with daily bars. The paper's edge depends heavily on 6-hour bars (Sharpe 2.41 on H6 vs 1.63 on D1 per the paper's own ablation). Daily bars are insufficient to capture crypto momentum — the timeframe mismatch is structural, not parametric. No further daily-bar testing warranted for crypto.

### Key Findings

1. **Stocks edge survives portfolio construction + transaction costs** — the Phase 1A friction flag (avg R < 0.5) was a valid caution, but the edge persists after costs at the portfolio level with proper risk management.
2. **Crypto edge does not survive on daily bars** — the paper's Sharpe 2.41 was on 6h bars; daily bars only achieve Sharpe 1.63 per the paper's own ablation, and our daily-bar result (0.151) is even lower. The 6h timeframe is essential for crypto momentum.
3. **Long-only is correct for both asset classes** — shorts were negative in Phase 1A and would have worsened Phase 1B/2 results. The structural positive drift in both equities and crypto makes shorting unprofitable with this momentum approach.
4. **Quarterly re-optimization is sufficient** — monthly optimization showed no improvement over quarterly, consistent with the paper's finding that parameter stability is more important than frequency.
5. **Sharpe gate at 0.3 is effective** — the original paper's gate of 1.3 was too restrictive for daily bars (filtered out >90% of assets during bear/sideways periods). Lowering to 0.3 maintained quality without excessive filtering.
6. **Trailing stop order-of-operations matters** — checking the old stop before updating (matching the original scanner logic) is critical; updating before checking caused premature exits and turned a profitable strategy into a losing one.

### Gap vs. Paper

The paper reports Sharpe 2.41 / +40.5% annual return. Our stocks result (Sharpe 0.815 / +5.8%) is significantly lower. Key gaps:
1. **Timeframe:** Paper uses 6h bars (optimal for crypto); we use daily. Paper's own ablation shows daily drops Sharpe from 2.41 to 1.63 for crypto.
2. **Market-cap data:** We use dollar volume as a market-cap proxy. Direct market-cap data may improve selection quality.
3. **Parameter grid:** We use a reduced grid (2×2×2×2=16 combos) for speed; the paper optimizes monthly with a larger grid.
4. **70/30 allocation:** The paper's asymmetric allocation (70% long / 30% short) contributed Sharpe +0.29 in the ablation. We're long-only because shorts were negative on daily bars.

## Validation Pipeline

Phase 1A: Signal generation scanner ✅
Phase 1B/2: Walk-forward portfolio backtest ✅
Phase 3: Robustness (walk-forward, Monte Carlo, regime-conditional, parameter sensitivity) ← NEXT (stocks only)
Phase 4: Paper trading (60-90 days)
Phase 5: Live execution with kill-switch criteria
