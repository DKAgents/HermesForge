# RISK GUARDIAN FINAL DECISION — STR-Y and STR-AI (US-114 Re-Validation)

**Decider:** Risk Guardian, HermesForge Swarm
**Date:** 2026-08-16
**Scope:** Final disposition of two scanners that passed code audit (no look-ahead bias) but failed walk-forward validation
**Authority:** Final go/no-go on scanner trust status per US-114 ForgeLoop

---

## EXECUTIVE SUMMARY

| Scanner | Verdict | WF OOS p-value | Raw p-value | Key Finding |
|---------|---------|----------------|-------------|-------------|
| STR-Y (ADX/DMI) | PARAMETER SENSITIVITY TEST | 0.066 | 0.0435 | Edge is borderline significant; parameter perturbation could confirm or kill |
| STR-AI (Seasonal) | KILL | 0.163 | <0.0001 | Massive in-sample vs OOS gap reveals overfit; seasonal instability confirmed in year-by-year data |

---

## STR-Y (ADX/DMI) — VERDICT: B) PARAMETER SENSITIVITY TEST

### Evidence Reviewed

**Code:** scanner_y_adx_dmi.py — clean, no look-ahead bias (architect confirmed). Standard Wilder ADX/DMI implementation. Entry on +DI/-DI cross with ADX > threshold filter. Exit via stop/target/time-stop. All entries use bar-close data (no intrabar peeking).

**Walk-Forward OOS Results (provided):**
- OOS avg R: 0.228
- OOS PF: 1.439
- OOS p-value: 0.066 (vs 0.05 threshold — tantalizingly close)

**Raw Full-Sample Analysis (computed from STR-Y-stocks-phase1a.csv):**
- 241 trades across 18 stocks
- Win rate: 44.4%
- Avg R: 0.184
- PF: 1.352
- t-stat: 2.030, p-value: 0.0435 (SIGNIFICANT at 0.05)
- 95% CI: [0.006, 0.362] — lower bound just above zero

**Exit Distribution:**
- Stop: 122 trades (51%), avg R = -1.000
- Target: 21 trades (9%), avg R = +3.000
- Time: 98 trades (41%), avg R = +1.055

The time exits are what saves this strategy. 41% of trades exit via time stop with an average of +1.055R — these are trends that developed but didn't reach the 3R target within 20 bars. This is genuine trend-following behavior: the ADX filter identifies trending conditions, and even when the target isn't hit, the trend direction carries trades into positive territory.

**Year-by-Year Performance:**

| Year | Trades | Win Rate | Avg R | Sum R |
|------|--------|----------|-------|-------|
| 2018 | 12 | 0% | -0.928 | -11.1 |
| 2019 | 26 | 65% | +0.553 | +14.4 |
| 2020 | 30 | 50% | +0.152 | +4.6 |
| 2021 | 34 | 53% | +0.618 | +21.0 |
| 2022 | 32 | 38% | -0.015 | -0.5 |
| 2023 | 20 | 20% | -0.389 | -7.8 |
| 2024 | 32 | 38% | -0.070 | -2.3 |
| 2025 | 35 | 51% | +0.314 | +11.0 |
| 2026 | 20 | 55% | +0.756 | +15.1 |

Performance is cyclical, not monotonically degrading. Bad years (2018, 2023) are followed by recoveries. This is consistent with a trend-following strategy that struggles in choppy markets (2022-2023) and excels in trending markets (2019, 2021, 2025-2026). The edge is real but regime-dependent — which is expected for ADX/DMI.

### Reasoning

1. **The edge is borderline, not absent.** The raw full-sample p-value is 0.0435 (significant). The WF OOS p-value is 0.066 (not significant, but within striking distance). This is not a strategy with no edge — it's a strategy with a marginal edge that the current parameters may not be optimizing.

2. **The 2 ATR stop is generating 51% stops.** This is the highest stop-out rate among the "clean code" scanners. A wider stop means each loss costs 2R (in ATR terms), and with 51% of trades stopping out, the strategy needs its winners to compensate heavily. A tighter stop (1.5 ATR) would reduce per-loss cost but increase stop frequency; a wider stop (2.5 ATR) would reduce stop frequency but increase per-loss cost. The current 2.0 ATR may not be the optimal point on this tradeoff curve.

3. **The ADX threshold of 25 is the textbook default, but it may not be optimal.** Lowering to 20 would admit more trades (weaker trend filter), potentially capturing trends earlier but with more false signals. Raising to 30 would be more selective (stronger trends only), potentially improving win rate but reducing sample size. The current 25 may be slightly too permissive or slightly too restrictive — only a sweep can tell.

4. **The strategy logic is sound and well-established.** ADX/DMI is not a curve-fit indicator — it's Wilder's original trend-strength system from 1978, used by practitioners for decades. The DI cross + ADX filter is a canonical trend-following entry. The edge, if it exists, is structural (trend persistence) rather than statistical artifact.

5. **The WF gap is small.** Raw avg R = 0.184 vs WF OOS avg R = 0.228. The OOS performance is actually BETTER than the full-sample average, which means the strategy is not overfit to the in-sample period — the edge is consistent across folds. The p-value failure (0.066 vs 0.05) is a power issue (241 trades spread across WF folds reduces per-fold sample size), not an edge-absence issue.

### Parameter Sweep Specification

**Route to: Backtester**

**Parameters to sweep:**

| Parameter | Current | Test Values | Rationale |
|-----------|---------|-------------|-----------|
| ADX_THRESHOLD | 25.0 | 20.0, 22.0, 25.0, 28.0, 30.0 | Controls trade selectivity. 20 = more trades, weaker filter. 30 = fewer trades, stronger trends only. |
| STOP_ATR_MULT | 2.0 | 1.0, 1.5, 2.0, 2.5 | Controls stop width. 51% stop rate at 2.0 ATR suggests the stop may be too wide (each loss costs 2R) or too tight (gets stopped before trend develops). |

**Parameters held fixed:**
- ADX_PERIOD = 14 (Wilder canonical, not worth sweeping)
- TARGET_RR = 3.0 (standard across scanner suite, not scanner-specific)
- MAX_HOLD_BARS = 20 (standard across scanner suite)

**Total combinations:** 5 x 4 = 20 parameter sets, each requiring a full walk-forward run.

**Pass criteria (ALL must be met for at least 3 combinations):**
1. WF OOS p-value < 0.05
2. WF OOS avg R > 0.15
3. WF OOS PF > 1.30
4. No single year contributes > 50% of total OOS R (no concentration)

**Kill criteria:** If fewer than 3 combinations pass, STR-Y is KILLED. The edge is parameter-specific (overfit), not structural.

**Additional requirement:** Report per-combination trade count. Any combination generating < 100 OOS trades is excluded from the pass count (insufficient sample).

---

## STR-AI (Seasonal) — VERDICT: A) KILL

### Evidence Reviewed

**Code:** scanner_ai_seasonal.py — clean, no look-ahead bias (architect confirmed). Expanding window implementation is correct: at each bar, only completed prior months are used to compute positive/negative rates for the current calendar month. The `n < 5` minimum sample guard is sensible. No code issues.

**Walk-Forward OOS Results (provided):**
- OOS avg R: 0.140
- OOS PF: 1.260
- OOS p-value: 0.163 (vs 0.05 threshold — not close, 3.2x over)

**Raw Full-Sample Analysis (computed from STR-AI-stocks-phase1a.csv):**
- 264 trades across 18 stocks
- Win rate: 49.6%
- Avg R: 0.393
- PF: 1.885
- t-stat: 4.357, p-value: < 0.0001 (highly significant in-sample)
- 95% CI: [0.216, 0.570]

**The In-Sample vs OOS Gap:**

| Metric | Full Sample (In-Sample) | WF OOS | Degradation |
|--------|------------------------|--------|-------------|
| Avg R | 0.393 | 0.140 | -64% |
| PF | 1.885 | 1.260 | -33% |
| p-value | <0.0001 | 0.163 | Significance lost |

This is the textbook signature of overfitting. The strategy looks excellent in-sample (p<0.0001, PF=1.885) but collapses out-of-sample (p=0.163, PF=1.260). The edge was never real — it was an artifact of the specific sample period.

**Year-by-Year Performance (visible deterioration):**

| Year | Trades | Win Rate | Avg R | Sum R |
|------|--------|----------|-------|-------|
| 2023 | 15 | 93% | +1.560 | +23.4 |
| 2024 | 78 | 63% | +0.769 | +60.0 |
| 2025 | 109 | 42% | +0.074 | +8.1 |
| 2026 | 62 | 35% | +0.199 | +12.3 |

The strategy had a golden period in 2023-2024 (when the expanding window had accumulated just enough data and seasonal patterns happened to align with market conditions) and then degraded rapidly. Win rate crashed from 93% to 35%. Average R collapsed from 1.560 to 0.074-0.199. This is seasonal instability made visible in the data.

**November Dependency (concentration risk):**

| Month | Trades | Win Rate | Avg R | Sum R | % of Total R |
|-------|--------|----------|-------|-------|--------------|
| November | 51 | 69% | +0.902 | +46.0 | 44% |
| June | 30 | 60% | +0.723 | +21.7 | 21% |
| All other months | 183 | 44% | +0.20 | +36.1 | 35% |

November alone contributes 44% of total R. Without November, the strategy's total R drops from +103.8 to +57.8, and the avg R drops from 0.393 to 0.315 (still positive, but heavily reliant on one month's historical pattern). The "Sell in May" adage and November-January seasonality are well-known, which means they may already be priced in — and the data shows the edge is fading (2025 November: 3 stops, avg R=-1.0; 2026 has no November data yet).

**March/April Failure:**

| Month | Trades | Win Rate | Avg R | Sum R |
|-------|--------|----------|-------|-------|
| March | 31 | 26% | -0.243 | -7.5 |
| April | 28 | 29% | -0.224 | -6.3 |

March and April are generating losses despite qualifying on the >60% historical positive rate threshold. The expanding window determined that March and April historically had >60% positive monthly returns, so the strategy enters long — but the trades are losing. This is the core problem: historical monthly return patterns do not predict 20-bar forward returns reliably.

### Reasoning

1. **p=0.163 is not close to significance.** At 3.2x the 0.05 threshold, this is not a borderline case. The WF validation definitively rejects the null hypothesis of positive expectancy. Compare to STR-Y's p=0.066 (1.3x the threshold) — STR-AI is in a fundamentally worse position.

2. **The in-sample vs OOS gap is massive and diagnostic.** A 64% degradation in avg R from in-sample to OOS is not noise — it's overfitting. The strategy's in-sample performance (p<0.0001) was a statistical artifact of the specific 2023-2024 period, not a durable edge. The expanding window implementation is correct, but correct implementation of a flawed premise still produces a flawed strategy.

3. **Year-by-year deterioration is visible and accelerating.** The win rate dropped from 93% (2023) to 35% (2026). This is not a single bad year — it's a structural breakdown. Seasonal patterns that worked in 2023-2024 stopped working in 2025-2026. This is exactly the "seasonal instability" risk identified in the original risk audit.

4. **November concentration is a structural vulnerability.** 44% of all profits from one calendar month means the strategy is effectively a "buy in November" strategy with extra steps. If November seasonality breaks down (as it did in 2025: 3 stops, avg R=-1.0), the entire strategy collapses.

5. **March/April entries are actively destroying capital.** The strategy enters long in March and April because the expanding window says these months historically had >60% positive returns — but the trades are losing (-0.243R and -0.224R respectively). The historical pattern is not predicting forward returns. This is the fundamental flaw: monthly return history does not contain actionable signal for 20-bar trades.

6. **Parameter optimization would produce overfit results.** Even if a parameter sweep (e.g., raising POS_THRESHOLD to 0.70) found a combination that passes WF, it would be overfit to the 2023-2024 golden period. The structural problem (seasonal instability) cannot be solved by parameter tuning — it's a property of the strategy type, not the parameters.

7. **Opportunity cost.** Resources spent re-testing STR-AI (parameter sweep, re-running WF, re-auditing) would be better allocated to STR-Y parameter testing, which has a genuine borderline edge worth investigating.

### Disposition

STR-AI is KILLED. No further resource allocation. The scanner is removed from the trusted scanner pool. It will not be routed to paper trading, parameter testing, or conditional watch. The code is clean and the implementation is correct, but the strategy premise (monthly seasonality predicts 20-bar returns) is not supported by the data.

The scanner file should be archived (not deleted) with a header comment marking it as KILLED per US-114 Risk Guardian decision, including the p-value and degradation metrics, so future developers do not re-test it without new evidence.

---

## SUMMARY

| Scanner | Verdict | Next Action | Resource Cost |
|---------|---------|-------------|---------------|
| STR-Y (ADX/DMI) | PARAMETER SENSITIVITY TEST | Route to Backtester for 20-combination WF sweep | Moderate (20 WF runs) |
| STR-AI (Seasonal) | KILL | Archive with KILLED marker. No further testing. | Zero |

**Final trusted scanner count after this decision:** Unchanged from pre-decision state. STR-Y is not yet trusted (pending sweep results). STR-AI is explicitly untrusted (killed). Only the 8 previously trusted scanners (X, Z, AA, AC, AD, AE, AF, AJ) remain trusted.

---

*Decision rendered by Risk Guardian, HermesForge Swarm. This decision is final per US-114 ForgeLoop authority. Override requires explicit human approval with documented rationale.*
