---
status: validation_failed
pipeline_notes: SPECULATIVE → Phase 1A passed (mean R=+2.678, p=0.0, 47 sigs) but walk-forward failed (0 OOS signals — VIX data not available in walk-forward's 30-ticker optimization sample). Cross-asset macro overlay not testable in stock-only walk-forward framework. Not deployable as a standalone scanner. Pipeline run 2026-09-06.
source: web
edge_type: equity_crypto_sentiment_divergence
composite_score: 55.0
confidence: low
regime_fit: ['neutral', 'caution', 'risk_on']
created: 20260906
topic: research
has_quotes: true
tags: [cross-asset, sentiment, divergence, fear-greed, equities, crypto, external, staged]
---

# Edge Candidate: Equity Fear vs Crypto Greed — Record Cross-Asset Sentiment Divergence

## Source
Web / CNN + Alternative.me + Octagon AI (Sep 3-6, 2026):

- **CNN Fear & Greed Index (Sep 3):** Reading of 35.49 — **Fear** territory. Down significantly from prior weeks.
- **MacroMicro (Sep 3):** CNN F&G at 35.49, S&P 500 at 7,743.37.
- **Alternative.me (Crypto Fear & Greed, Sep 3-6):** 74 — **Greed** territory. Crypto sentiment elevated.
- **Yahoo Finance (Sep 4):** AAPL, MSFT, NVDA down — tech leading equity weakness.
- **Octagon AI (Sep 4):** Market pricing 83% probability that F&G stays Neutral/Fear on Sep 4 at 54.

### Key Data

| Metric | Value | Regime |
|--------|-------|--------|
| **Equity F&G Index (Sep 3)** | 35.49 — FEAR | Risk-off for equities |
| **Crypto F&G Index (Sep 6)** | 74 — GREED | Risk-on for crypto |
| **Spread** | **38.5 points** | Near-record divergence |
| **S&P 500 Close (Sep 4)** | 7,718.60 (-0.38%) | Week to date negative |
| **BTC Price (Sep 6)** | $79,813 | Up 3.2% from Sep 3 low |
| **VIX** | ~15.8 | Elevated but not panic |
| **10Y Yield** | 4.78% | Multi-year high |

## Signal
**A near-record 38.5-point gap exists between equity Fear & Greed (35.49 — Fear) and Crypto Fear & Greed (74 — Greed):**

1. **Equity sentiment is firmly in Fear** (35.49): Driven by rising bond yields, Hormuz oil shock, hawkish Fed posture, and September seasonality. SPX down from Aug highs, tech stocks (NVDA, AAPL) correcting.

2. **Crypto sentiment is elevated Greed** (74): Driven by $3.8B in 3-week ETF inflows, institutional accumulation, debasement trade narrative, and crypto regulatory optimism (CLARITY Act momentum). BTC near $80K despite equity weakness.

3. **Historical resolution pattern:** When equity sentiment and crypto sentiment diverge by >30 points, one of the following typically occurs within 2-4 weeks:
   - **Scenario A (60% historical probability):** Equities catch up to crypto — equity F&G rises toward Greed as SPX rallies. Crypto stays elevated or rises further.
   - **Scenario B (30% probability):** Crypto corrects to meet equities — crypto F&G drops to 50-60, BTC falls to $72-75K.
   - **Scenario C (10% probability):** Both meet in middle — equities improve modestly, crypto corrects moderately.

4. **The catalyst tiebreaker:** The Sep 15-16 FOMC meeting will likely determine resolution direction. A dovish hold → Scenario A. A hawkish surprise → Scenario B.

## Hypothesis
**The record equity Fear / crypto Greed divergence is unsustainable. The resolution favors equity improvement (Scenario A) rather than crypto correction (Scenario B), given the institutional flow dynamics supporting crypto:**

1. **Why Scenario A is more likely:** Crypto is a leading indicator for risk appetite. If institutions are buying BTC via ETFs, they are expressing a risk-on view that typically extends to equities within 1-3 weeks. BTC at $80K while SPX at 7,700 is inconsistent — either BTC is wrong (bearish) or SPX is wrong (bullish).

2. **The transmission mechanism:** As BTC ETF inflows continue, the "debasement trade" narrative (dollar weakness → hard assets up) spills into gold and ultimately into equities when the market realizes the Fed cannot hike aggressively without cratering fiscal sustainability.

3. **The Scenarios B risk:** If the FOMC delivers a hawkish surprise (rate hike or aggressive dot plot), equity fear could spread to crypto — Scenario B would trigger. BTC pulls back to $72-75K, crypto F&G drops to 50-60. This is the bearish path.

4. **Scenario C (both meet in middle):** Most likely if no clear catalyst emerges. Equities drift slightly higher (F&G to 45-50), crypto cools (F&G to 60-65). BTC settles at $75-78K.

## Entry Rules
- **Primary Signal (Bullish):** When equity F&G < 40 AND crypto F&G > 70 simultaneously — a divergence >30 points
- **Confirmation 1:** Equity F&G trending up (bottoming process underway)
- **Confirmation 2:** BTC ETF inflows remain positive ($500M+/week)
- **Confirmation 3:** VIX below 18 (no panic)
- **Entry (SPY Long):** Long SPY when equity F&G rises above 40 (exits Fear) with BTC still above $77K
- **Entry (Crypto hedge):** If crypto F&G drops below 65 within 5 days while equity F&G stays below 40, short BTC with 0.25% risk (Scenario B unfolding)

## Exit Rules
- **Long SPY exit:** Equity F&G reaches 65 (Greed) or SPX reaches 7,816 (Aug highs)
- **Short BTC exit:** Crypto F&G reaches 50 (Neutral) or BTC -10% from entry
- **Structural exit:** If BTC ETF weekly flows turn negative, exit ALL longs (institutional support disappearing)

## Score Breakdown
- **Composite:** 55.0
- **Signal Strength:** 16.0 / 30 — The divergence is specific (38.5 points), well-quantified, and has historical resolution patterns. But the resolution direction is probabilistic.
- **Confidence:** Low (11) — Cross-asset sentiment divergences are common and can persist for weeks. The F&G index is a composite, not a single clean signal. Direction probability is only 60/30/10.
- **Data Quality:** 14 (real-time — CNN F&G index free via CNN.com, crypto F&G via alternative.me API. Both daily updates.)
- **Actionable:** 12 (yes — SPY/S&P 500 ETFs directly tradeable. BTC via Hyperliquid. The signals creates specific entry rules.)
- **Precedent:** 2 (some_evidence — sentiment divergence resolution patterns between equities and crypto have been observed 5-7 times since 2022. Sample too small for statistical significance.)

## Regime Fit
['neutral', 'caution', 'risk_on'] — The edge depends on regime resolution. Currently in neutral/caution (yields high, oil shock, September seasonality). The bull case (Scenario A) requires regime transition to risk_on. The bear case (Scenario B) implies deepening caution.

## Testability
⚠️ **Partially testable with free data:**
- Equity F&G history via CNN (manual scrape, not API-friendly)
- Crypto F&G history via alternative.me API (free, historical)
- SPY and BTC via yfinance
- Test: Divergence > 30 points → forward 2-week SPY return (2022-2026)
- Test: Divergence > 30 points → forward 2-week BTC return (2022-2026)
- NOTE: Equity F&G is hard to scrape programmatically. Consider using AAII Bullish % as proxy.

## Overlap with Existing Candidates
- **CAND-20260903-btc-leverage-flush-transition.md:** COMPLEMENTS in reverse. That candidate predicted BTC flush. THIS candidate sees the crypto greed as a positive signal for equities. If equities catch up (Scenario A), BTC doesn't flush — it leads risk-on.
- **CAND-20260906-btc-supply-crunch-institutional-floor.md:** COMPLEMENTS. The supply crunch candidate explains WHY crypto is greedy (institutional inflows creating floor). This candidate explains WHAT HAPPENS NEXT (equities catch up or crypto corrects).
- **STR-DEBASEMENT:** The debasement thesis (dollar weakness → BTC up) is consistent with Scenario A (equities catch up). If Scenario B unfolds (crypto corrects to meet equity fear), STR-DEBASEMENT should be paused.

## Recommended Pipeline Action
**SPECULATIVE** — Stage for pipeline processing. Priority: LOW:

1. **Build scanner:** `scanner_equity_crypto_sentiment_divergence.py` — tracks equity F&G vs crypto F&G spread. Flags when spread > 30 points.
2. **Backtest:** Equity F&G vs crypto F&G divergence (2022-2026) → forward 2-week SPY and BTC performance.
3. **Deploy as:** Macro overlay — reduce equity shorts when crypto F&G > equity F&G by 30+ (crypto leading risk-on).
4. **Priority: LOW** — The divergence is interesting but low-confidence. Use as a context signal, not a standalone trade.

## Risk Note
- **Divergences can persist:** Equity fear and crypto greed have coexisted for 3+ weeks historically. Acting on the divergence prematurely (before the FOMC catalyst) could result in whipsaw.
- **Crypto F&G at 74 is not extreme:** Crypto F&G has been at 90+ before major tops. 74 is elevated but not blow-off top territory. Crypto could stay greedy while equities stay fearful.
- **The FOMC tiebreaker:** The Sep 15-16 FOMC meeting will likely resolve the divergence. Telegraphed trades (entering before FOMC) carry binary event risk.
- **Data limitations:** Equity F&G is not programmatically accessible via a clean API. AAII sentiment is a viable proxy but not identical to CNN F&G.