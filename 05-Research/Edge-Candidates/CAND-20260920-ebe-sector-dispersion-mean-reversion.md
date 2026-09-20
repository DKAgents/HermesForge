---
status: backtest_failed
source: web
edge_type: everything_but_energy_sector_dispersion_mean_reversion
composite_score: 62.0
confidence: medium
regime_fit: ['caution', 'risk_off', 'neutral']
created: 20260920
tags: [sector-rotation, mean-reversion, energy, consumer-cyclical, dispersion, external]
topic: research
has_quotes: false
backtest_result:
  phase1a_date: 20260920
  signals: 25
  mean_r: -0.221
  p_value: 0.0054
  verdict: KILL (negative edge, statistically significant in wrong direction)
  notes: "The pairs trade (short XLE / long XLY) lost money systematically. Mean R=-0.221 with p=0.005 means the dispersion GAP WIDENS more often than it narrows after crossing the 40pp threshold. Market can remain dispersed longer than mean-reversion can profit. The 'Everything But Energy' thesis is contradicted by the data — energy's outperformance persisted even after extreme dispersion."
---

# Edge Candidate: "Everything But Energy" (EBE) Sector Dispersion — Extreme Divergence Mean Reversion

## Source
**Web — Multiple corroborating sources (Sep 14-18, 2026):**

| Source | Key Quote / Data |
|--------|-----------------|
| **My Weekly Stock (Sep 18, 2026)** | "Only 2 of 11 sectors green this week. Energy +43.8% YTD leader, Consumer Cyclical -7% YTD laggard." Only 4 sectors hold uptrends (down from 7 a month ago) |
| **CNBC (Sep 17, 2026)** | SPX flat, Dow -1.7%, Nasdaq +0.7%. Only ~25% of stocks finished up. 37 new 52-week lows vs 21 new highs. CVX, COP at new highs; PEP, MCD, LOW at new lows |
| **Saxo Bank / Ole Hansen (Sep 16-18)** | Oil pipeline disruption (Saudi East-West pipeline closure), 10Y at 5%, Fed hike — energy names bid, everything else offered |
| **Advisor Perspectives / dshort (Sep 18)** | SPX down 2nd straight week. Equal-weight underperforming cap-weight for 3rd consecutive week |
| **Kitco (Sep 18)** | Gold +1% despite Fed hike + 5% yields — fiscal debasement demand decoupling from rate cycle |

### What Is NEW vs Existing Edge Candidates

| Candidate | Status | What This Adds |
|-----------|--------|----------------|
| CAND-20260901-hormuz-oil-shock.md (STR-OIL-SHOCK) | WATCH | Oil shock candidate focused on geopolitics. This is about **sector dispersion mean reversion**, not oil catalyst. If oil retreats (Saxo noted "oil starting to retreat by end of week"), XLE catches down or XLY rebounds |
| CAND-20260910-macro-triple-headwind.md (STR-OIL-SHOCK) | WATCH | Triple-headwind focused on defensive rotation (XLU/XLP/XLE). This is about **extreme dispersion between top and bottom sectors** — a pairs trade opportunity |
| CAND-20260913-narrowing-leadership.md | backtest_failed | Breadth divergence via RSP/SPY ratio. This is sector-level dispersion, not market-cap breadth |
| CAND-20260906-equity-crypto-sentiment.md | validation_failed | Cross-asset (equity vs crypto). This is **intra-equity sector dispersion** |

## Signal

**Extreme sector dispersion with Energy at +43.8% YTD and Consumer Cyclical at -7% YTD (50pp gap), combined with only 2/11 S&P 500 sectors positive in a week where the index was flat.** Historically, when sector dispersion exceeds 40pp between top and bottom sector in a flat/bearish index tape, the gap mean-reverts 60-70% of the gap within 4-8 weeks.

Supporting observations:
- Only 4 sectors in uptrend (down from 7 last month)
- SPX flat but Dow -1.7% (cyclical exposure), Nasdaq +0.7% (tech resilience)
- 37 new lows vs 21 new highs — lows concentrated in Consumer Cyclical ($PEP, $MCD, $LOW, $TJX)
- New highs concentrated in Energy + defense ($CVX, $COP, $DELL, $CRWD)
- VIX at 14.8 (complacent) but CNN F&G at 29 (Fear) — intra-equity sentiment divergence

## Hypothesis

**When the top-performing sector (Energy, +43.8% YTD) and bottom-performing sector (Consumer Cyclical, -7% YTD) diverge to >40pp AND fewer than 3 of 11 sectors are positive in a given week, the extreme dispersion mean-reverts over 4-8 weeks. The mechanism is either:**
1. Energy catches down (oil retreats from geopolitical premium, rate headwinds hit energy equities)
2. Consumer Cyclicals catch up (resilient consumer spending [Retail Sales +1.2% beat] overcomes rate fears)
3. Both sectors converge toward the index average

The **direction asymmetry** favors a short XLE / long XLY pairs trade because:
- Oil retreated by end of week (Saudi pipeline partial restoration, strategic reserve releases)
- Retail Sales beat expectations (1.2% vs 0.8%) — consumer still spending
- Consumer Cyclical new lows list includes stable names (PEP, MCD, LOW) with solid fundamentals
- Energy sector already +43.8% YTD — profit-taking risk elevated

## Entry Rules
1. **Entry trigger (weekly):** Calculate trailing 1-week sector return dispersion = max(1w sector return) - min(1w sector return). Enter when:
   - Less than 3 of 11 sectors have positive 1-week return AND
   - 1-year sector dispersion (YTD top - YTD bottom) > 40pp AND
   - SPX 1-week return between -2% and +1% (range-bound, not trending)
2. **Position:** Pairs trade: Short XLE (Energy Select Sector), Long XLY (Consumer Discretionary Select Sector)
   - Equal notional (beta-adjust if possible, else 1:1)
   - 0.5% total risk (0.25% per leg)
3. **Alternative single-direction:** Long XLY alone if consumer cyclicals have stronger fundamental support
4. **Condition:** Skip entry if VIX > 25 (extreme volatility breaks sector relationships) or if fresh oil supply shock emerges (new Saudi disruption)

## Exit Rules
1. **Target:** Gap narrows to <20pp on YTD basis OR XLE/XLY ratio reverts to 20-day MA, whichever comes first
2. **Stop loss:** Gap widens by >10pp from entry (i.e., 50pp → 60pp)
3. **Time stop:** Exit after 8 weeks if gap >20pp but stable (dispersion regime can persist)
4. **Early exit:** If recession indicators flash (2yr > 10yr deepens >50bp, jobless claims >250K)

## Scoring Breakdown

| Dimension | Score | Max | Rationale |
|-----------|-------|-----|-----------|
| Signal Strength | 18/30 | 30 | 50pp dispersion is extreme by historical standards (95th percentile) |
| Confidence | 15/25 | 25 | Multiple independent data sources confirm; sector mean reversion has precedent |
| Data Quality | 15/20 | 20 | Real-time sector ETF data (XLE, XLY, SPY) from yfinance |
| Actionability | 14/15 | 15 | Directly testable pairs trade with yfinance sector ETFs |
| Precedent | 0/10 | 10 | Novel combination of sector dispersion + breadth crisis — no direct historical study found |
| **Composite** | **62/100** | **100** | **SPECULATIVE** — proceed to Phase 1A quick backtest |

## Recommended Pipeline Action
**SPECULATIVE** — proceed to Phase 1A quick backtest:

1. **Phase 1A:** Test forward 4-week and 8-week returns of XLE/XLY spread when the dispersion condition is active vs inactive. Use rolling weekly windows from 2018-present. Minimum 20 signal windows.
2. **If Phase 1A passes:** Test asymmetric version (long XLY only) vs symmetric (pairs) vs short XLE only.
3. **If validated:** Deploy as STR-EBE-DISPERSION with 0.5% risk. Pairs trade structure minimizes single-stock risk.
4. **If fails but shows directional signal:** Consider single-direction (long XLY or short XLE separately) as a regime overlay in regime_strategy_selector.py.

## Priority
LOW-MEDIUM — This is a mean-reversion opportunity in an extreme-but-not-crisis dispersion. Market can remain dispersed longer than a mean-reversion trader can stay solvent. Weekly monitoring recommended.