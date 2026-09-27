---
status: backtest_failed
source: web
edge_type: global_bond_yield_surge_regime_risk
composite_score: 75.0
confidence: high
regime_fit: ['caution', 'risk_off', 'neutral']
created: 20260901
topic: research
has_quotes: true
tags: [macro, bonds, yields, fed, treasury, fed-hike, external, processed-backtest-failed]
pipeline_verdict: KILL — Phase 1A: 15 signals, avg R=-0.388, p=0.2456. Short QQQ / long defensive during yield surges has negative expected returns historically. The hypothesis (yield surge → equity weakness) is directionally confirmed but the ATR-based exit model adds friction that cancels the edge.
---

# Edge Candidate: Global Bond Yield Surge — Yields at 2008 Highs — Rate-Hike Regime Risk

## Source
Web / Yahoo Finance + Bloomberg (Aug 31 — Sep 1, 2026) — corroborated across multiple outlets:

- **Bloomberg (Aug 31):** "Global Bond Selloff Sends Yields to the Highest Level Since 2008" — Bloomberg gauge of global govt debt yield rose to 3.72%, highest since mid-2008. Link
- **Yahoo Finance (Sep 1):** "Stock market today: Dow, S&P 500, Nasdaq drop as rising bond yields, oil prices weigh on stocks" — US 10Y at 4.76% (highest intraday since Jan 2025)
- **Bloomberg (Aug 31):** Japan 10Y JGB yield climbed to 3% for first time since 1996
- **Yahoo Finance (Sep 1):** US 30Y at 5.27% (multi-decade high), pulled back to 5.24%
- **Reuters (Sep 1):** Dollar gains on rate hike expectations; ISM manufacturing still expansionary at 55.2
- **JOLTS Data (Sep 1):** "Low hire, low fire" labor market — layoffs rate 1%, quits 1.9%. Tight enough to keep Fed pressure.

### Key Data

| Metric | Value | Context |
|--------|-------|---------|
| **US 10Y Yield** | 4.76% (intraday high) | Highest since Jan 2025 |
| **US 30Y Yield** | 5.27% → 5.24% | Multi-decade high territory |
| **Global Govt Bond Yield** | 3.72% | Highest since mid-2008 |
| **Japan 10Y JGB** | 3.00% | First time since 1996 |
| **Dollar (DXY)** | Strengthening | Rate hike expectations |
| **VIX** | 15.83 (+6.10%) | Spiking from 14.43 on Aug 28 |
| **S&P Futures (Sep 1)** | 7,650.25 (-0.63%) | Pre-market down |
| **Nasdaq Futures (Sep 1)** | 29,147.50 (-1.24%) | Tech leading downside |
| **Gold** | $4,416.70 (-1.22%) | Declining |
| **Bitcoin** | $77,949 (-0.78% to -0.85%) | Declining |
| **Crude Oil (WTI)** | $88.16 (+2.80%) | Surging on Hormuz strikes |
| **Brent Crude** | >$92/bbl | War premium |

### The Catalyst Chain

1. **Aug 19:** Treasury doubles bond buyback to $4B → debasement trade (BTC +25%, Gold +10%)
2. **Aug 28:** Fed Chair Warsh's Jackson Hole debut — hawkish tone confirmed
3. **Aug 31 - Sep 1:** Global bond selloff accelerates — Warsh hawkishness + inflation persistence + fiscal concerns drive yields to generational highs
4. **Sep 1:** Hormuz oil strikes + Fed rate hike fears + bond selloff = triple headwind for equities

## Signal
**Global bond yields surging to levels not seen since 2008**, reversing the entire debasement trade thesis:

- Warsh's Jackson Hole speech successfully convinced markets he will hike rates further
- The bond market is now pricing in higher-for-longer rates globally
- This is the **inverse of the debasement trade** — yields rising = tightening financial conditions = headwind for risk assets
- The debasement trade (CAND-20260825, STR-DEBASEMENT) is now at risk of unwinding

The divergence is extreme:
- **NASDAQ futures -1.24%** while bond yields surge = tech is taking the hit
- **Gold declining** alongside bond selloff = the hard-asset debasement trade is reversing
- **Oil surging** on geopolitical risk = supply shock adding to inflation fears = more rate hike pressure

## Hypothesis
**Global bond yields at 2008 levels represent a regime transition from "debasement" to "tightening."** The market is repricing:

1. **Short-dated yields leading higher:** Warsh convinced markets rate cuts are off the table. Fed funds futures repricing higher.
2. **Long-dated yields following:** Fiscal concerns (Treasury buyback as yield suppression failure) + term premium expansion = 30Y at 5.27%
3. **Cross-asset confirmation:** Dollar up, gold down, BTC down, VIX up — all consistent with a tightening/risk-off regime, NOT a debasement regime
4. **Critical warning:** STR-DEBASEMENT (deployed Aug 25) was predicated on yields falling and dollar weakening. The exact opposite is happening. This strategy may need to be paused or reversed.

## Entry Rules
- **Primary Signal:** US 10Y closes above 4.75% (confirmed intraday Sep 1). Confirm with 30Y > 5.25%.
- **Confirmation 1:** VIX closes above 16 (currently 15.83) — fear entering the market
- **Confirmation 2:** DXY closes above 102 (rate hike expectations building)
- **Entry (Risk Reduction):** 
  - Reduce total equity exposure by 30%
  - Close STR-DEBASEMENT positions (BTC long, GLD long)
  - Move to cash or short-duration T-bills
- **Entry (Short Tech):** Short QQQ when Nasdaq futures continue below 29,000. Target: 28,000. Stop: reclaim 29,500.
- **Entry (Short Duration):** Long SHY (short-term bonds) as yields may continue up. Short TLT (long bonds).

## Exit Rules
- Exit risk reduction when US 10Y drops below 4.25% (confirm yield trend reversal)
- Exit QQQ short when VIX drops below 14 or 10Y below 4.25%
- Structural exit: If Warsh signals rate cut possibility (dovish pivot)

## Score Breakdown
- **Composite:** 75.0
- **Signal Strength:** 22.0 / 30 — Global yields at 2008 highs is a rare, high-impact event. Multiple corroborating sources. Cross-asset confirmation across bonds, FX, equities, commodities. The catalyst (Warsh hawkishness) is clearly identified.
- **Confidence:** High (25) — Bond yield surges of this magnitude are rare and historically reliable indicators of regime change. The cross-asset confirmation is strong (DXY up, gold down, equities down). The catalyst is known (Warsh Jackson Hole). 
- **Data Quality:** 15 (real-time — yields, VIX, DXY all available via yfinance or FRED)
- **Actionable:** 12 (clear risk-reduction action; directional short-tech trade requires monitoring; STR-DEBASEMENT close is directly actionable)
- **Precedent:** 6 (some_evidence — global yield surges to 2008 highs are rare; most recent analog is 2022 rate hike cycle; the 2008 analog is structurally different due to GFC context)

## Regime Fit
['caution', 'risk_off', 'neutral'] — This edge signals a potential regime transition from the brief "debasement" regime (risk_on) to a "tightening/caution" regime. If yields continue to surge, we enter risk_off. If yields stabilize at these levels, it's a neutral/caution regime.

## Testability
✅ **Fully testable with free data:**
- US 10Y (^TNX), US 2Y (^2YY), US 30Y (^TYX) via yfinance
- VIX (^VIX), DXY (DX-Y.NYB), SPY, QQQ via yfinance
- GLD, BTC-USD via yfinance
- Test: instances where 10Y rose >50bp in 2 weeks → forward SPY return over 1m, 3m
- Test: instances where 10Y > 4.75% AND 30Y > 5% simultaneously → equity sector performance

## Overlap with Existing Candidates
- **CAND-20260825-treasury-buyback-debasement-regime.md:** THIS IS THE INVERSE of that candidate. That candidate predicted BTC +25%, Gold +10% on Treasury buyback. This candidate warns the debasement trade is reversing. If this candidate is correct, STR-DEBASEMENT should be paused.
- **CAND-20260830-gold-collapse-risk-signal.md:** Already BACKTEST_FAILED — gold drops don't predict SPY weakness. But this edge is about BOND YIELDS as the mechanism, not gold.
- **CAND-20260827-jackson-hole-warsh-event-risk.md:** Correctly identified the risk. Warsh WAS hawkish. This edge is the POST-EVENT resolution.

## Recommended Pipeline Action
**PROMISING** — High priority. Stage for immediate pipeline processing:

1. **URGENT — Risk Management (TODAY):** STR-DEBASEMENT should be evaluated for immediate risk reduction. The debasement trade catalyst (yields falling, dollar weakening) is reversing. Warsh's hawkish Jackson Hole speech has triggered a global bond selloff.
2. **Build scanner:** `scanner_global_yield_surge.py` — tracks US 10Y, 30Y, global yield gauge, DXY, VIX. Flags when 10Y > 4.6% AND rising.
3. **Backtest:** 10Y yield surges >50bp in 2-week windows → forward SPY/QQQ returns
4. **Deploy as:** Risk-reduction overlay for ALL strategies when yields are at cycle highs
5. **Priority: HIGH** — The signal is active NOW (Sep 1). Yields are at generational highs and still rising.

## Critical Note
**This edge directly conflicts with CAND-20260825-treasury-buyback-debasement-regime.md.** Both cannot be correct simultaneously. The debasement thesis was predicated on yields falling and dollar weakening. If yields are surging and dollar strengthening, the debasement trade is invalidated. The pipeline should resolve this conflict by prioritizing the most recent data (Sep 1) over the Aug 19-25 setup. Recommend: pause STR-DEBASEMENT until the yield trend resolves.