---
status: backtest_failed
source: combined
edge_type: narrowing_leadership_breadth_divergence
composite_score: 67.0
confidence: medium
regime_fit: ['caution', 'risk_off']
created: 20260913
processed: 20260913
phase1a_results:
  signals: 462
  mean_r: -0.088
  p_value: 0.014
  classification: KILL
  notes: >
    Phase 1A run 2026-09-13. Signal detected real regime (p=0.014) but directionally
    opposite to hypothesis for SPY/QQQ shorts. RSP longs showed positive edge (+0.098
    avg R, 59.7% WR) but overwhelmed by negative short-side signals. Narrowing leadership
    actually favors mega-caps (SPY/QQQ rally), confirming thesis but making short
    strategy unprofitable. RSP mean-reversion component viable for future re-test
    as standalone with tighter entry filter. Recommend re-testing RSP long-only signal
    with 10-week MA < ratio (not ratio < MA) as a separate edge candidate.
tags: [breadth, equal-weight, leadership, divergence, external, macro, backtest_failed]
---

# Edge Candidate: Narrowing Leadership Breadth Divergence — Equal-Weight vs Cap-Weight Gap Signal

## Source
**Combined: Web research (Sep 11-13, 2026)**

### Key Sources
- **Lance Roberts / RIA Advisors (Sep 12, 2026):** Bull Bear Report — "When the average stock falls three times as hard as the index, leadership is narrowing, not broadening." Equal-weight S&P fell 1.87% vs cap-weighted -0.68% (nearly 3x). Small caps -2.38%. Tech/Nasdaq held up (-0.52%).
- **Charles Schwab Weekly Trader's Outlook (Sep 11, 2026):** SPX at 7,656, testing 50-DMA at 7,600. Technical composite at 68.63 — "overbought reversing." MACD bearish cross on equal-weight index. Breadth contracting.
- **MTC (Sep 9, 2026):** Russell 2000 flat-to-red, lagging as 10Y near cycle highs. "The cleanest tell on whether the market is truly leaning hawkish."
- **thetrading.tools (Sep 10, 2026):** Median SI = 3.3% with 5.4% of stocks >20% SI. High-SI stocks have 5.78% squeeze rate (3x normal) — elevated squeeze potential when catalyst hits.
- **Self-calculated:** RSP/SPY ratio can be tracked daily on yfinance to quantify the divergence magnitude.

### What Is NEW vs Existing Engine Sources

| Dimension | Engine Has | This Edge Adds |
|-----------|-----------|----------------|
| Breadth | A/D line vs price, >80%/<20% overbought/oversold, NH/NL ratio | **Equal-weight vs cap-weight relative performance** — measures leadership concentration directly |
| Short interest | Individual tickers >20% SI + DTC >5 | **Macro aggregate SI context** + squeeze regime setup (15-year high notional + +50% squeeze rate × record options expiry) |
| Regime | VIX, F&G, correlation, VRP, funding | **MFBR (Money Flow/Breadth Ratio)** rolling over from 80%→70% — 25-year backtest shows this combination leads to below-average returns |
| Catalyst | Economic events | **Record quad witching (Sep 18) + FOMC (Sep 15-16) + CLARITY Act vote (Sep 15)** — once-in-years catalyst cluster on a fragile tape |

## Signal
**The RSP/SPY ratio (equal-weight vs cap-weight S&P 500) declining below a trailing threshold signals narrowing leadership and elevated downside vulnerability.**

Key data points for the current signal (week ending Sep 11, 2026):
- SPY (cap-weighted): -0.68% for the week, at 7,666
- RSP (equal-weight): -1.87% for the week  
- RSP/SPY ratio: At or near multi-week low
- SPXEW MACD: Bearish cross (Aug 20), histogram negative
- SPX technical composite: 68.63, "overbought reversing"
- MFBR: 70% (down from 80% peak 4 weeks ago) — triggering risk-off interpretation per 25-year backtest

Supporting context:
- Median SI = 3.3% across 5,463 stocks (up from 3.2%)  
- 5.4% of stocks have >20% SI — squeeze potential elevated
- 10Y at 4.844% (approaching 5%), WTI at $94-100, FOMC hike odds 56-60%
- Record options expiration on Sep 18 (quad witching)

## Hypothesis
**When the RSP/SPY ratio declines below its 10-week moving average AND the weekly change is negative, the market is in a "narrowing leadership" regime. This regime favors mega-cap/large-cap strategies and disfavors equal-weight, small-cap, and broad-based long strategies. The regime amplifies downside when negative catalysts hit, and creates asymmetric squeeze potential when positive catalysts hit individual high-SI names.**

1. Equal-weight underperforming cap-weight means gains are concentrated in the largest names
2. Narrow leadership = fragile market — fewer stocks are carrying the index
3. When the broad market is weak (equal-weight down), a catalyst-induced break in the mega-caps creates outsized downside
4. Conversely, high aggregate short interest + narrow leadership + catalyst cluster = elevated squeeze potential in oversold names
5. This is a regime overlay, not a standalone trade — use to adjust strategy mix and position sizing

## Entry Rules
1. **Regime detection (weekly):** Calculate RSP/SPY ratio daily. Signal triggers when:
   - RSP/SPY ratio < 10-week MA of itself AND
   - RSP/SPY ratio week-over-week change is negative
2. **When regime is active:**
   - Reduce position sizing on STR-I, STR-R, STR-V, STR-W, STR-X, STR-Y (broad-based stock strategies) by 30%
   - Favor STR-B (MACD divergence), STR-Q (liquidity sweep) — these work on individual mega-caps too
   - Do NOT add new equal-weight or small-cap focused positions
   - For crypto: Increase 0.5x due to potential for positive catalyst (CLARITY Act) overwhelming the narrowing-leadership regime
3. **Squeeze watch:** When regime is active AND high-impact catalyst arrives (FOMC, CPI, CLARITY vote):
   - Scan high-SI names (>20% SI) for bullish volume divergence — these have 5.78% chance of +50% squeeze
   - Prepare defined-risk long positions in high-SI names that show relative strength

## Exit Rules
1. Regime exit: RSP/SPY ratio back above 10-week MA for 2 consecutive weeks
2. Squeeze exit: +15% target or +5 days, whichever comes first
3. If regime persists >4 weeks: re-evaluate (can persist for months — 2022 analog lasted Q2-Q3 2022)

## Testability Assessment

| Criterion | Assessment |
|-----------|-----------|
| **yfinance data** | ✅ Yes — SPY, RSP both available. Standard weekly/daily OHLCV |
| **Backtestable** | Yes — RSP/SPY ratio from 2018-present (RSP launched Apr 2018). Can measure forward returns in narrow vs broad leadership regimes |
| **Walk-forward** | Yes — threshold re-estimation annually (10-week MA is robust) |
| **Overlap with existing** | Complements STR-LOWCORR (low-correlation regime stock picker). Narrow leadership is NOT the same as low correlation — they can coexist |
| **Historical analog** | 2022 Q2-Q3 (breadth narrowed as mega-caps held up while equal-weight fell) |
| **Squeeze regime overlay** | Testable via: track forward 63-session returns on high-SI quintile during narrow-leadership regimes vs broad-leadership regimes |

## Scoring Breakdown
| Dimension | Score | Max | Rationale |
|-----------|-------|-----|-----------|
| Signal Strength | 15/30 | 30 | Narrowing clearly measurable but modest magnitude so far (1.87% vs 0.68%) — more signal if this persists |
| Confidence | 15/25 | 25 | Multiple independent sources confirm; Lance Roberts' MFBR has 25-year backtest |
| Data Quality | 15/20 | 20 | Real-time market data (SPY, RSP, volumes) from yfinance |
| Actionability | 15/15 | 15 | Directly testable: RSP/SPY ratio thresholds, squeeze scan, regime overlay |
| Precedent | 7/10 | 10 | Some evidence (2022 analog, MFBR studies) |
| **Composite** | **67/100** | 100 | PROMISING — proceed to Phase 1A |

## Recommended Pipeline Action
**PROMISING** — proceed to Phase 1A quick backtest:

1. **Phase 1A (this week):** Test forward 5-day returns for SPY, RSP, and QQQ when the narrowing-leadership signal is active vs inactive. Minimum 50 signal windows needed.
2. **If Phase 1A passes:** Test the squeeze regime overlay — do high-SI quintile stocks outperform during narrow-leadership + catalyst periods?
3. **Deployment:** If validated, deploy as a **regime overlay filter** that suppresses equal-weight strategies and favors mega-cap strategies (not as a standalone scanner). Update in `regime_strategy_selector.py`.
4. **Reference existing candidates:** CAND-20260910-macro-triple-headwind (same regime: caution/risk_off — partial signal overlap but different edge mechanism)

## Priority
MEDIUM — This is a regime refinement, not a crisis alert. The narrowing leadership could persist for weeks. Monitor weekly.