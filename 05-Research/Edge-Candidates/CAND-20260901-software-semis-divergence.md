---
status: validation_failed
source: web
edge_type: software_semis_divergence_september_effect
composite_score: 60.0
confidence: medium
regime_fit: ['neutral', 'caution']
created: 20260901
topic: research
has_quotes: true
tags: [sector-rotation, software, semiconductors, seasonality, september-effect, external, processed-rejected]
pipeline_verdict: REJECT — IGV and SOXX not in the 529-stock universe/cache. Cannot build scanner without these core tickers. Candidate rates SPECULATIVE with Sept 15 entry (2 weeks out), making it low priority for immediate processing. Would require adding tickers to universe through swarm process.
---

# Edge Candidate: Software vs Semiconductors Record Divergence + September Effect

## Source
Web / Yahoo Finance (Sep 1, 2026) — Chart of the Day analysis:

- **Yahoo Finance / Jared Blikre (Sep 1):** "Software stocks crushed chips in August. History says September gets tougher: Chart of the Day" — IGV +16% in Aug (2nd-best month since 2002), SOXX +1% (gave back mid-month rally)
- **Yahoo Finance (Aug 31):** "Software is crushing chips by a record margin"
- **Yahoo Finance AlphaSpace (Sep 1):** Since Aug 17, 58 of 61 semiconductor stocks fell — wiped $1.1T in market value
- **Yahoo Finance (Sep 1):** Software stocks: TEAM nearly doubled in Aug (best month ever), PLTR +50%, CRM +40%

### Key Data

| Metric | August Return | Context |
|--------|---------------|---------|
| **IGV (Software ETF)** | +16% | 2nd-best month since 2002 |
| **SOXX (Semiconductor ETF)** | +1% | Gave back 10% mid-month gain |
| **S&P 500** | +2.5% | Modest gain |
| **Software S&P Sub-Index** | +14% | Strongest August since 1990 |
| **Semiconductors (58/61 stocks)** | Fell since Aug 17 | -$1.1T market value wiped |

### The Divergence

| Period | IGV (Software) | SOXX (Semis) | Delta |
|--------|----------------|---------------|-------|
| **Aug 1 - Aug 17** | Strong rally | Strong rally (~+10%) | ~Even |
| **Aug 17 - Aug 31** | Continued rally | Gave back all gains | IGV outperformed SOXX by ~15%+ |
| **Full August** | +16% | +1% | RECORD DIVERGENCE |

The physical AI build-out trade (semiconductors, electrical equipment, power infrastructure, networking) rolled over in mid-August while software kept climbing. This is a **structural rotation within tech**.

### Historical September Pattern

Yahoo Finance analyzed the 12 strongest August rallies in software since 1990:
- Through Sept 15: Software median +1%, Semiconductors -1%
- Sept 15-30: Software median -1%, SPY -2%, Semiconductors -3.5%

September is the weakest month for the S&P 500 (avg -0.6%, positive only 45% of the time). Volatility tends to spike.

## Signal
**Record divergence between software (IGV +16%) and semiconductors (SOXX +1%) in August presents a mean-reversion opportunity for September.**

Two complementary hypotheses:

**H1: Software Momentum Continues (Near-Term)**
- Software had its strongest August since 1990
- Institutional rotation into software may continue through mid-September
- History: software holds +1% through Sept 15
- Entry: Long IGV, hold through Sept 15

**H2: Both Weaken in Late September**
- History: after strong August software rallies, both software and semis decline in late September
- Semiconductors fall hardest (-3.5% median from Sept 15-30)
- The September effect + record divergence = mean reversion risk
- Entry: Short SOXX (or long SOXS) from Sept 15 through month-end

## Entry Rules
- **Strategy A (Software Long):** Long IGV while above 20MA. Exit Sept 15 or when IGV shows 3 consecutive red days.
- **Strategy B (Semiconductor Short):** Short SOXX starting Sept 15, targeting -3.5% through Sept 30. Stop at +2% from entry.
- **Strategy C (Pair Trade):** Long IGV / Short SOXX (market-neutral). This expresses the rotation thesis without directional market risk.
- **All strategies:** Position size 0.5% risk (seasonal strategy — lower conviction than pure signal)

## Exit Rules
- **Strategy A exit:** Sept 15 or IGV 20MA break
- **Strategy B exit:** Sept 30 or SOXX +2% from entry
- **Strategy C exit:** When the IGV:SOXX ratio reverts to its 50-day average

## Score Breakdown
- **Composite:** 60.0
- **Signal Strength:** 18.0 / 30 — Record divergence quantifiable (IGV +16% vs SOXX +1%), September effect well-documented, 12 historical observations, specific expiration dates for the trade
- **Confidence:** Medium (15) — Record divergence increases probability of mean reversion but sample size is small (12 observations). September effect reliable but magnitude varies.
- **Data Quality:** 15 (real-time — IGV, SOXX via yfinance)
- **Actionable:** 10 (yes — IGV/SOXX are liquid ETFs, pair trade is practical)
- **Precedent:** 2 (some_evidence — software August rally → September performance is a known seasonal pattern; record divergence adds edge)

## Regime Fit
['neutral', 'caution'] — This is a sector rotation within tech during a period when the overall market faces headwinds from bond yields and oil. Software may hold up better than semis because software is less rate-sensitive (higher margins, less capex, no supply chain exposure).

## Testability
✅ **Fully testable with free data:**
- IGV, SOXX, SPY via yfinance
- Test: IGV August returns vs forward September returns (all years since 2000)
- Test: IGV:SOXX ratio divergence magnitude vs forward convergence speed
- Test: Post-strong-August-software-rally (top 5 years) → September sector performance

## Overlap with Existing Candidates
- Engine has a **sector rotation scanner** but this specific software-vs-semis divergence is a NEW development (Aug 17-31). The record divergence has no prior candidate.

## Recommended Pipeline Action
**SPECULATIVE** — Stage as medium-priority. This is a seasonal strategy with moderate backtest support:

1. **Build scanner:** `scanner_software_semis_divergence.py` — tracks IGV:SOXX ratio, flags when monthly divergence exceeds 15%
2. **Backtest:** August software rally → September sector performance (IGV vs SOXX vs SPY)
3. **Deploy as:** Seasonal overlay on existing strategies (reduce tech exposure in September, tilt toward software over semis)
4. **Priority: MEDIUM** — The setup is forming but the entry is September 15 (2 weeks out). No immediate action required.

## Risk Note
- This is a low-conviction seasonal strategy. Do not size above 0.5% risk.
- The record divergence makes mean reversion more likely but also introduces the risk that "this time is different" (software-led AI revolution structurally superior to semis capex). Pair trade (long IGV / short SOXX) reduces this risk.
- Monitor the bond yield surge (CAND-20260901-global-bond-yield-surge.md) — if yields keep rising, semis (long-duration, capex-heavy) will underperform software (high margins, less rate-sensitive), which would actually ACCELERATE the divergence rather than mean-revert it.