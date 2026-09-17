---
status: reject
source: web
edge_type: quad_witching_gamma_squeeze_setup
composite_score: 62.0
confidence: medium
regime_fit: ['risk_on', 'neutral', 'caution']
created: 20260917
topic: research
has_quotes: false
tags: [options, gamma, quad-witching, event-driven, advisory, rejected]
rejection_reason: "Not a backtestable scanner — one-time event advisory. Candidate explicitly states this (see 'Not a backtestable scanner' paragraph, Precedent score 0/10). Event is Sep 18 — staged for manual advisory, not pipeline scanning."
---

# Edge Candidate: Record Quad Witching Gamma Squeeze — Sep 18, 2026

## Source
**Web / multiple outlets (Sep 14-17, 2026):**

- **CNBC / multiple (Sep 14-17):** "Wall Street is heading into its biggest ever 'Triple Witching' options reset" — ~$5.5 trillion in options exposure expiring on Sep 18.
- **Investopedia (Sep 17):** Stock market today — tech shares power indexes higher ahead of quad witching.
- **Market Maulers (Sep 17):** "September: The Only Month With a Losing Record" — Sep 18 quad witching combines with FOMC aftermath for concentrated event cluster.
- **Kibot / Bitget:** Quad witching involves simultaneous expiration of index futures, index options, stock options, and single-stock futures on the same day.

### What Makes This NEW vs Existing Engine

| Dimension | Engine Has | This Edge Adds |
|-----------|-----------|----------------|
| Options expiry | No scanner | **Record $5.5T notional expiry with 35% of outstanding U.S. options OI rolling off** |
| Dealer gamma | No scanner | **Gamma positioning changes create directional bias based on dealer hedging flows** |
| Event clusters | FOMC/CPI/NFP | **Quad witching is NOT in the economic scanner — it's an options market structure event** |
| Catalyst timing | Sep 18 calendar | **Combined with post-FOMC relief rally = asymmetric gamma setup** |

### Key Data

| Metric | Value | Context |
|--------|-------|---------|
| **Notional options expiring** | ~$5.5T | Largest in history — 35% of outstanding U.S. options OI |
| **Date** | Sep 18, 2026 (Friday) | Tomorrow — immediate |
| **Context** | Post-FOMC (Sep 16) | Relief rally underway (futures +0.8%+) |
| **VIX** | ~17 (est, down from 18+ pre-FOMC) | Elevated but declining — favorable for gamma compression |
| **10Y** | Back below 5% (~4.96%) | Sell-the-news on bonds, risk-on rotation |
| **Oil (WTI)** | Retreating from $100+ | $105 Brent — supply fears easing |
| **Nasdaq futures** | +1.1% | Tech leading the relief rally |
| **BTC** | ~$76K | Recovering from CLARITY Act failure sell-off |

## Signal
**The Sep 18 quad witching coincides with the largest options expiration in history (~$5.5T notional, 35% of outstanding OI) AND the post-FOMC relief rally. This creates a unique gamma dynamics setup:**

1. **Dealer gamma positioning:** Before quad witching, dealers are typically short gamma (hedging delta). As options expire worthless, dealer hedging flows reverse — buying gamma turns into delta unwinds. This can amplify the directional move.

2. **The post-FOMC tailwind:** With futures up +0.8%+ on Sep 17, the market is entering quad witching with positive momentum. If this holds through Friday, dealers who are short calls face gamma pressure to buy more as the market rises.

3. **The record notional amplification:** $5.5T is unprecedented. The dealer hedging flows will be proportionally larger than any previous quad witching event.

4. **The September effect:** September is historically the only month with a net negative return for SPY. However, post-FOMC relief rallies tend to persist for 3-5 days. The question is whether the negative seasonal effect outweighs the post-catalyst momentum.

## Hypothesis
**The combination of record options expiry, post-FOMC relief momentum, and declining yields/oil creates an asymmetric bullish gamma squeeze setup for Sep 18. The most likely outcome is an intraday rally driven by dealer gamma hedging, with a potential reversal in the final hour as options roll off and dealers unwind positions:**

1. **Pre-market (Thu close → Fri open):** Futures rallying into quad witching = bullish open bias
2. **Morning session (Fri 9:30-11:30):** Dealer gamma buying as market holds above key strike levels
3. **Midday (11:30-2:30):** Range-bound as max pain zone attracts price
4. **Final hour (3:00-4:00):** High volatility as options expire — gamma unwinds create sharp reversals
5. **Key level:** SPY max pain = options strike with highest OI. Identify from open interest data pre-market Friday.

### Risk Note
- **The September effect is real:** SPY has net negative historical return in September. The relief rally could fade by Friday afternoon.
- **Quad witching reversals:** The final hour is notorious for sharp reversals as dealers unwind. Any long entry on Friday morning should have a tight stop for the 3pm mark.
- **Not a backtestable scanner:** Like the CLARITY Act candidate, this is a one-time event that doesn't generate a repeatable mechanical signal. Stage as an advisory, not a pipeline scanner.

## Entry Rules
1. **Thursday (Sep 17):** No pre-positioning. Monitor futures close to gauge Friday open bias.
2. **Friday (Sep 18) morning:** If SPY futures are +0.3%+ at 9am, prepare for gamma squeeze.
3. **Entry (long SPY):** Enter on first 30-min candle above VWAP with volume > 20d avg. Target 0.5% risk.
4. **Alternative (QQQ):** Tech leading (Nasdaq +1.1% futures) — QQQ may outperform SPY.
5. **Position size:** 0.5% risk — this is a high-volatility event with binary outcome risk.
6. **No crypto exposure:** Quad witching is equity-specific. Hyperliquid crypto positions are unaffected but may see cross-asset volatility spillover.

## Exit Rules
1. **Take profit:** SPY +1.0% from entry (intraday target for gamma squeeze)
2. **Stop loss:** SPY closes below VWAP on 30-min basis (gamma squeeze invalidated)
3. **Time stop:** Exit ALL positions by 3:30pm ET — the final 30 min of quad witching has highest reversal risk
4. **No hold through weekend:** Quad witching day should not be held overnight — gap risk for Monday

## Score Breakdown

| Dimension | Score | Max | Rationale |
|-----------|-------|-----|-----------|
| Signal Strength | 16/30 | 30 | Record notional ($5.5T) + post-FOMC tailwind = strong setup. But gamma dynamics are probabilistic, not deterministic. |
| Confidence | 15/25 | 25 | Medium — the mechanics are well-understood (dealer hedging, gamma squeeze) but the outcome depends on Friday's open direction which isn't known yet. |
| Data Quality | 17/20 | 20 | Real-time — futures prices, OI data (via CBOE/OPRA if available), VIX. Max pain levels published free pre-market. |
| Actionability | 14/15 | 14 | Directly actionable: SPY/QQQ on yfinance. Clear intraday rules. But the edge expires by 4pm Friday. |
| Precedent | 0/10 | 10 | No precedent for $5.5T expiry size. Previous record was ~$5.0T in Dec 2025. This is literally the largest ever. |
| **Composite** | **62/100** | 100 | **PROMISING — stage for real-time Friday advisory.** Not suitable for scanner backtest but actionable as an intraday event overlay. |

## Overlap with Existing Candidates
- **CAND-20260915-fed-hike-certainty-contrarian.md (backtest_failed):** COMPLEMENTS. That candidate predicted post-FOMC SPY long would work, which it IS (futures +0.8% today). The quad witching edge extends the post-FOMC thesis into Friday — the relief rally may continue through quad witching, or the gamma unwind may reverse it. If the Fed hike candidate's thesis holds (post-FOMC SPY positive), the quad witching gamma skews bullish.
- **CAND-20260915-10y-5percent-regime.md (promising):** COMPLEMENTS. The 10Y pulling back below 5% post-FOMC reinforces the relief rally narrative. If yields stay below 5% through Friday, the risk-on rotation supports the gamma squeeze.
- **CAND-20260913-narrowing-leadership-breadth.md (backtest_failed):** COMPLEMENTS. The narrowing leadership (RSP underperforming SPY) makes QQQ the preferred long for quad witching — mega-cap tech leads.

## Recommended Pipeline Action
**PROMISING — Stage for real-time advisory (event tomorrow):**

1. **Immediate (Sep 17 PM):** Monitor futures close. If positive, prepare for bullish open Friday.
2. **Friday morning (Sep 18):** Check max pain levels for SPY. Identify nearest gamma strike levels.
3. **Intraday:** Execute long SPY/QQQ per entry rules if conditions met.
4. **Post-hoc:** Log outcome to evaluate gamma squeeze mechanics for future quad witching events.
5. **Long-term:** Consider adding a "quad witching proximity" rule to the regime filter (not a scanner, but a regime modifier for Sep/Dec/Mar/Jun quarterly expirations).

## Priority
**HIGH (TIME-SENSITIVE)** — Event is tomorrow. This edge is a same-day advisory. Not suitable for pipeline scanning but actionable for intraday positioning.

## Core Thesis
The record $5.5T quad witching combined with the post-FOMC relief rally creates an asymmetric gamma setup favoring upside through mid-session, with elevated reversal risk in the final hour. Trade the gamma, respect the 3:30pm exit.