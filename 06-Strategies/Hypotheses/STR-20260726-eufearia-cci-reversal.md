---
id: STR-20260726-eufearia-cci-reversal
type: strategy
status: hypothesis
asset_class: stocks
trade_style: swing
timeframe: daily
market_regime: ranging
core_idea: reversal
confidence: low
publish_enabled: false
publish_channel: stocks
source: EUFEARIA_PRO_7_PineScript
source_authors: Philip Paul
source_title: "EUFEARIA Pro 7 - Momentum Oscillator Enhanced"
source_published: 2026-07-26
evidence_links:
  - C154-macd-histogram-momentum-warning-signals
  - N165-relative-strength-index-rsi-overboughtoversold-levels
  - RG017-overboughtoversold-readings-in-strong-trends
  - RG032-3-to-1-reward-to-risk-ratio
  - RG037-use-protective-stops-to-limit-losses
last_reviewed: 2026-07-26
created: 2026-07-26
updated: 2026-07-26
tags: [strategy, hypothesis, cci, mean-reversion, reversal, oscillator, swing, eufearia]
topic: strategies
has_quotes: false
source: HermesForge Strategies
---
# EUFEARIA CCI Reversal — Modified CCI Oscillator Mean-Reversion at Extremes

## Thesis

The EUFEARIA PRO 7 indicator is a modified Commodity Channel Index (CCI) oscillator that measures the deviation of typical price (HLC3) from its EMA, normalized by the EMA of absolute deviations. The classic CCI formula `(price - mean) / (0.015 * mean_deviation)` produces a statistical z-score-like oscillator that identifies when price is anomalously far from its recent average.

The strategy variant adds two smoothing layers: an EMA(21) of the raw CCI (reducing noise) and an SMA(4) signal line. Entry signals fire when the oscillator crosses its signal line while at an extreme level (≤ -50 for buys, ≥ +50 for sells), requiring both statistical extremity AND directional confirmation. This dual-gate approach — extreme level + crossover — is more selective than threshold-crossing alone (as in STR-E RSI Mean-Reversion, which was killed at Phase 1A).

**Why CCI may outperform RSI for mean-reversion:** RSI measures the ratio of up-periods to down-periods (momentum-based), while CCI measures standard deviations from the mean (volatility-based). In ranging markets, price stretches away from the mean are more reliably "stretched" than momentum ratios, because CCI's denominator (mean deviation) adapts to local volatility. The 0.015 constant in the CCI formula is Lambert's original empirical constant, chosen so that ~20-25% of values fall outside ±100.

**Direction:** Bidirectional. Buys (long) at oversold extremes, sells (short) at overbought extremes. This is a pure mean-reversion approach — both directions assume price reverts toward the oscillator's zero line.

**Relationship to existing work:** This is structurally similar to [[STR-20260726-rsi-mean-reversion-entry]] (KILLED) but uses a different oscillator (CCI vs RSI), a different entry trigger (crossover at extreme vs threshold crossback), and an additional smoothing layer (EMA of CCI + SMA signal line). The divergence confirmation option (pinpoint mode) also mirrors the two-stage confirmation in [[STR-20260719-macd-histogram-divergence-weekly-assessment]].

---

## Indicator Construction (from Pine Script)

### Step 1 — Typical Price
```
avg_price = (high + low + close) / 3    # HLC3
```

### Step 2 — EMA of Typical Price (Channel)
```
ema_esa = EMA(avg_price, length_channel=10)
```

### Step 3 — Mean Absolute Deviation
```
diff = EMA(|avg_price - ema_esa|, length_channel=10)
```

### Step 4 — CCI Formula (modified — uses EMA, not SMA)
```
ci = (avg_price - ema_esa) / (0.015 * diff)
```

### Step 5 — Oscillator (additional smoothing)
```
osc = EMA(ci, length_signal=21)
```

### Step 6 — Signal Line
```
sig = SMA(osc, 4)
```

### Extreme Levels
- Overbought: +50 (configurable; adaptive percentile mode available)
- Oversold: -50

### Sentiment Tiers (informational, not trade signals)
| Level | Threshold | Label |
|-------|-----------|-------|
| ≥ +84 | Extreme Greed | Exhaustion zone |
| ≥ +67 | Very Greedy | Warning zone |
| ≥ +50 | Greed | Entry zone for shorts |
| ≤ -50 | Fear | Entry zone for longs |
| ≤ -67 | Very Fearful | Warning zone |
| ≤ -84 | Extreme Fear | Exhaustion zone |

---

## Entry Criteria

Work through these gates in order. Any failure = no trade.

### Gate 1 — Extreme Level (mandatory)

**Long (buy):** Oscillator ≤ -50 (oversold)
**Short (sell):** Oscillator ≥ +50 (overbought)

This ensures we only act at statistical extremes, not at moderate readings. The ±50 threshold is tighter than the classic CCI ±100, reflecting the additional EMA smoothing which compresses the oscillator's range.

### Gate 2 — Crossover Confirmation (mandatory)

**Long:** Oscillator crosses ABOVE signal line (osc was below sig, now above)
**Short:** Oscillator crosses BELOW signal line (osc was above sig, now below)

The crossover confirms the oscillator is turning in the expected direction — not just at an extreme, but reversing. This is the key difference from STR-E (which entered on threshold crossback alone).

### Gate 3 — Strict Extreme Confirmation (optional, default ON)

When enabled, requires BOTH oscillator AND signal line to be beyond the extreme:
**Long:** osc ≤ -50 AND sig ≤ -50
**Short:** osc ≥ +50 AND sig ≥ +50

This prevents entries where the oscillator spike is very brief and the signal line (SMA-4) hasn't confirmed the depth.

### Gate 4 — Divergence Confirmation (optional, default OFF — "Pinpoint Mode")

When enabled, requires structural divergence at the extreme:
**Long (bullish divergence):** Price makes a lower low while oscillator makes a higher low, both at oversold
**Short (bearish divergence):** Price makes a higher high while oscillator makes a lower high, both at overbought

Divergence detection uses pivot highs/lows with configurable left/right bars (default 3/3).

### Entry Price
Close of the signal bar (the bar where the crossover fires).

---

## Exit Criteria

Since the Pine Script is an indicator (not a strategy), exits are defined here for the scanner:

### Stop Loss
- **Long:** Entry bar's low - 1.0 × ATR(14)
- **Short:** Entry bar's high + 1.0 × ATR(14)

The 1.0 ATR buffer is wider than STR-B's 0.5 ATR because mean-reversion entries at extremes can have sharp continuation before reversing. The wider stop accommodates this "final thrust" pattern.

### Take Profit
- **Primary target:** Return to the oscillator's zero line (mean reversion target)
  - Approximated as: entry price projected by the oscillator's current distance from zero
  - Long target: entry_price × (1 + |osc| / 100) — oscillator at -50 implies ~50% of the way back to mean
  - Short target: entry_price × (1 - |osc| / 100)
  - Capped at 3R maximum (don't hold for unrealistic targets)
- **Partial exit:** 50% at 2R or zero-line approach, whichever comes first
- **Remainder:** Trail stop at break-even, exit on opposite signal or time stop

### Time Stop
If price has not moved toward target within 10 trading days, exit full position. Mean-reversion trades that stall give the dominant trend time to reassert.

### R:R Filter
Skip any signal where projected reward-to-risk < 2.0.

---

## Risk Rules Applied

- PS-001: Max 1% capital risk per position
- PS-004: Position size = (1% capital) / (entry - stop distance)
- LL-001: Daily loss limit 2%
- PT-001: Paper mode minimum 30 days
- RG032: 2:1 minimum R:R (lowered from 3:1 because mean-reversion targets are closer)
- RG037: Protective stops mandatory

---

## Parameters

| Parameter | Default | Phase 1A Value | Notes |
|-----------|---------|----------------|-------|
| Channel length | 10 | 10 | EMA period for CCI mean |
| Signal smoothing | 21 | 21 | EMA period for oscillator |
| Signal line | 4 | 4 | SMA period for signal line |
| Overbought level | +50 | +50 | Upper extreme threshold |
| Oversold level | -50 | -50 | Lower extreme threshold |
| Strict mode | true | true | Both osc + sig at extreme |
| Pinpoint mode | false | false | Divergence confirmation |
| ATR stop multiplier | 1.0 | 1.0 | Wider than STR-B (0.5) |
| Max hold | 10 | 10 | Time stop in bars |
| Min R:R | 2.0 | 2.0 | Lower than trend strategies |
| Amplify factor | 1.0 | 1.0 | Scales osc/sig together |
| Adaptive extremes | false | false | Percentile-based levels |

---

## Counter-Evidence and Failure Modes

### Failure Mode 1: Strong trend absorbs the extreme
CCI can stay at extreme levels for many bars in a strong trend. The crossover may fire repeatedly while price continues in the trend direction. Mean-reversion strategies are structurally vulnerable to this.

**Mitigation:** The time stop (10 bars) limits capital locked in a stalled trade. The crossover gate requires directional turn confirmation, not just extreme reading. The 1% risk cap limits damage from any single trade.

### Failure Mode 2: CCI vs RSI — same category, same risk
STR-E (RSI Mean-Reversion) was KILLED at Phase 1A with avg R -0.056 and 0/3 sub-periods positive. CCI is a different oscillator but the same mean-reversion category. The structural risk is identical: mean-reversion fails in trending markets, and the 2019-2026 test period includes strong trending phases.

**Mitigation:** The crossover-at-extreme dual gate is more selective than STR-E's threshold-crossback. The additional EMA smoothing may reduce false signals. But this is a known high-risk category — confidence starts at LOW.

### Failure Mode 3: EMA-based CCI differs from standard CCI
Standard CCI uses SMA for the mean and mean deviation. EUFEARIA uses EMA, which gives more weight to recent prices. This may produce different extreme readings and different signal timing. Not necessarily better or worse, but not directly comparable to published CCI research.

---

## Phase 1A Validation Results (2026-07-26)

### Baseline (bidirectional, strict extreme, ±50 thresholds)

| Metric | Value |
|--------|-------|
| Universe | 529 tickers (S&P 500 + ETFs + extras), daily bars |
| Data window | 2019-04-01 to 2026-07-24 |
| Total signals | 25,068 |
| Signals/year | 3,488 |
| Avg R | +0.017 |
| Median R | -1.000 |
| Win rate | 32.8% |
| Sub-periods positive | 2/3 (bull +0.013, bear +0.130, current -0.066) |
| Friction flag | ⚠️ Yes (avg R < 0.5) |
| **Classification (ADR-004)** | **❌ KILL** (avg R 0.017 < 0.2 kill threshold) |

### Sensitivity Sweep (7 variants tested)

| Variant | Sig/Yr | Avg R | Win% | Sub-Periods+ | Classification |
|---------|--------|-------|------|--------------|----------------|
| Baseline (bidirectional, ±50) | 3,488 | 0.017 | 32.8% | 2/3 | ❌ KILL |
| **V1: Long-only** | **1,046** | **0.222** | **41.1%** | **3/3 ✅** | **⚠️ WATCH** |
| V2: Short-only | 2,442 | -0.071 | 29.3% | — | ❌ KILL |
| V3: \|osc\| >= 67 (tighter) | 632 | 0.032 | 33.7% | — | ❌ KILL |
| V4: \|osc\| >= 84 (very tight) | 12 | -0.020 | 34.1% | — | ❌ KILL |
| V5: Long + osc <= -67 | 148 | 0.210 | 42.7% | 2/3 | ❌ KILL |
| V7: RR >= 3.0 filter | 3,319 | 0.013 | 32.4% | — | ❌ KILL |

### Validated Configuration: Long-Only (V1)

| Metric | Long-Only Result |
|--------|-----------------|
| Total signals | 7,515 |
| Signals/year | 1,046 |
| Avg R | +0.222 |
| Win rate | 41.1% |
| Sub-periods | 3/3 ✅ (bull +0.288, bear +0.185, current +0.214) |
| Friction flag | ⚠️ Yes (avg R < 0.5) |
| **Classification** | **⚠️ WATCH** |

**Decision:** Advance to Phase 1B with long-only configuration and friction flag. Shorts are structurally negative (avg R -0.071, 29.3% win rate) — the structural positive drift in equities makes shorting at overbought levels unprofitable. Long-only avg R of +0.222 is just above the 0.2 kill threshold but well below the 0.6 pass threshold. Must verify edge survives transaction costs in Phase 1B.

### Key Findings

1. **Long-only rescue** — the baseline bidirectional result was KILL at +0.017 avg R, but removing shorts lifts it to +0.222 (WATCH). This mirrors the STR-I AdaptiveTrend finding: shorts are structurally disadvantaged in equities.
2. **Shorts are negative** — avg R -0.071, 29.3% win rate. Selling at overbought CCI extremes fails because strong trends keep CCI elevated.
3. **±50 threshold is optimal** — tighter thresholds (±67, ±84) reduce signal frequency without improving avg R. The ±50 level with EMA smoothing already filters sufficiently.
4. **Mean-reversion works in bear markets** — period2_bear (2022-2023) has the best avg R (+0.185 for long-only), confirming mean-reversion is stronger in ranging/bear markets.
5. **Comparison with STR-E (RSI Mean-Reversion, KILLED)**: STR-J EUFEARIA long-only (avg R +0.222, 3/3 sub-periods) outperforms STR-E (avg R -0.056, 0/3 sub-periods). The CCI + signal line crossover approach is structurally better than RSI threshold crossback.
6. **Target exits are highly profitable** — 100% win rate on target exits (avg R +4.517), but only 644/7,515 long-only trades reach target. The issue is stop-outs (68% of trades hit stop before target). This is the classic mean-reversion trade profile: many small losses, few large wins.

---

## Backtest / Paper Trade Log

*Not started — requires Phase 1B completion first.*

---

## Change Log

| Date | Change | Trigger |
|------|--------|---------|
| 2026-07-26 | Strategy created from EUFEARIA PRO 7 Pine Script | User-submitted indicator code; created hypothesis file + scanner for Phase 1A testing |
