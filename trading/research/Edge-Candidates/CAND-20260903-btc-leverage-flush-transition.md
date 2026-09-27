---
status: backtest_failed
source: web
edge_type: btc_leverage_flush_transition
composite_score: 62.0
confidence: medium
regime_fit: ['neutral', 'caution', 'risk_off']
created: 20260903
topic: research
has_quotes: true
tags: [crypto, bitcoin, leverage, on-chain, glassnode, positioning, external, backtest_failed]
pipeline_verdict: REJECTED — Phase 1A: mean R = -0.395 (NEGATIVE), p = 0.0015 (statistically significant negative), 144 signals (25/yr), win rate 33.3%. BTC rallies in Greed+Flat regime rather than flushing. Simplified proxy tested (F&G > 65 + flat weekly price → short BTC). Full hypothesis (OI, funding rates) untestable without data pipeline expansion.
---

# Edge Candidate: Bitcoin Leverage Flush Setup — Glassnode "In Transition"

## Source
Web / SpendNode + Glassnode + CoinEx Research (Aug 31 — Sep 3, 2026):

- **Glassnode (Sep 1, 2026):** Bitcoin is "in transition" — institutional inflows (ETF + treasury buyers) are colliding with rising leverage and early short-term-holder (STH) distribution. BTC at $78,738, flat on the week.
- **CoinEx Research (Sep 2, 2026):** "Bitcoin's First Breakout Test" — post-breakout follow-through holding, but the next test is whether BTC can sustain without leverage becoming dominant. Funding rate at 36th percentile (not extreme), OI elevated relative to momentum.
- **Fortune / Yahoo Finance (Sep 3, 2026):** BTC at $77,310.17 — mild weakness. Slightly down from $78,738 on Sep 1.
- **Fear & Greed Index (Sep 3):** 74 — "Greed" territory. Optimism without follow-through in spot price.
- **CoinStats (Sep 3):** "Funding rates remain positive but moderate, with open interest elevated relative to price momentum, suggesting leverage-driven risk."

### Key Metrics

| Metric | Value | Context |
|--------|-------|---------|
| **BTC Price (Sep 3)** | $77,310 | Down from $78,738 Sep 1 |
| **Fear & Greed Index** | 74 (Greed) | Not extreme (90+), but elevated for flat price |
| **Funding Rate** | 0.0038% (36th percentile) | Moderate — not crowded |
| **Open Interest** | Elevated vs price momentum | Leverage accumulated post-breakout |
| **STH Distribution** | Early signs | Some recent buyers realizing gains |
| **ETF Inflows** | $238M pre-breakout | Institutional demand still present |
| **Weekly Price Action** | Flat (down 0.15%) | Choppy, no decisive breakout |

## Signal
**Bitcoin is in a "transition" state where three competing forces are poised for a resolution:**

1. **Institutional inflows (bullish):** Spot ETF demand remains. Treasury buyers are structural. This is the long-term bid.
2. **Rising leverage (bearish-short-term):** OI is elevated relative to price momentum. Traders are paying to stay long into a market that isn't rewarding them. This creates vulnerability to a flush.
3. **Short-term holder distribution (bearish):** Wallets that bought recently are starting to realize gains. This removes buyers from the order book at the same moment forced selling could hit.

The key insight: **None of these three forces is dominant yet.** That's what a transition looks like — no clean trend, just competing pressures waiting for one to win.

## Hypothesis
**A leverage flush in BTC (5-15% drop) is the most probable near-term resolution, creating a re-entry opportunity for the longer-term bull case:**

1. **The setup:** F&G 74 (Greed) + flat price = optimism without follow-through. This is the classic setup that leverage feeds on. When funding stays elevated and price fails to break higher, the market becomes top-heavy.
2. **The trigger:** Any macro shock (Hormuz escalation, Fed hawkish surprise, Sep 15-16 FOMC) could trigger a modest dip that cascades as leveraged longs get liquidated.
3. **The reset:** If ETF and treasury buying keeps showing up on down days, a leverage flush becomes a reset rather than a trend change. This is the "structural bid" that Glassnode refers to.
4. **The re-entry:** After the flush (BTC below $70K or -10% from current), the structural bull case re-asserts. The debasement trade catalyst (Treasury buyback) may be paused but the underlying dollar weakness thesis remains.

## Entry Rules
- **Primary Signal:** BTC closes below $72,000 (break of Aug 2026 range low) on >2x average volume
- **Confirmation 1:** Funding rate turns negative (longs getting squeezed)
- **Confirmation 2:** F&G drops below 30 (Fear) — sentiment reset
- **Confirmation 3:** ETF flows remain positive during the flush (institutional buying on dips)
- **Entry (Re-entry):** Long BTC when funding rate normalizes (returns to neutral/positive) AND price reclaims 20-day MA
- **Entry (Short):** Short BTC if funding rate is above 0.01% AND price breaks below $74,000 (leverage cascade confirmed)
- **Position size:** 0.5% risk for short, 1.0% for re-entry long

## Exit Rules
- Exit short when funding rate drops to 0.001% or below (flush exhausted)
- Exit long when BTC reclaims $80,000 or RSI > 75 (overbought)
- Structural exit: If ETF flows turn negative for 5 consecutive days (institutional bid disappearing)
- Time stop: Exit all positions after 21 days if no resolution

## Score Breakdown
- **Composite:** 62.0
- **Signal Strength:** 18.0 / 30 — Glassnode's "in transition" is a specific, well-reasoned framework. Three competing forces clearly identified. The signal is multi-sourced (Glassnode, CoinEx, CoinStats, Fortune).
- **Confidence:** Medium (15) — The leverage flush setup is well-understood, but the timing is uncertain. F&G 74 is not extreme (vs 90+ in past tops). The institutional bid is a real counterweight. The flush could be -5% or -15%.
- **Data Quality:** 15 (real-time — BTC price, funding rates, OI, F&G all available via Hyperliquid + yfinance)
- **Actionable:** 12 (yes — BTC can be traded via Hyperliquid. Clear entry and exit rules. The re-entry trade is the higher-conviction leg.)
- **Precedent:** 2 (some_evidence — BTC leverage flush patterns are well-documented. 2021 May crash, 2022 Nov FTX, 2024 Aug Yen carry trade. Each created a buy-the-dip opportunity for the structural bid.)

## Regime Fit
['neutral', 'caution', 'risk_off'] — This edge is a SHORT-TERM tactical setup within a longer-term structural bull case. The regime is oscillating between "debasement" (risk-on) and "tightening" (risk-off). The leverage flush mechanism is regime-agnostic — it works in any market where positioning gets extended.

## Testability
✅ **Fully testable with free data:**
- BTC-USD via yfinance
- Hyperliquid funding rates via their API (free)
- Fear & Greed Index via alternative.me API (free)
- Test: instances where BTC had F&G > 70 AND flat weekly price action AND OI elevated → forward 1-week return
- Test: instances where funding rate flipped negative after positive period → forward 1-week BTC return
- Test: BTC drawdowns > 10% during institutional inflow periods → recovery time

## Overlap with Existing Candidates
- **STR-Q (crypto edges):** This edge COMPLEMENTS STR-Q. STR-Q focuses on signal-based crypto entries. This edge is a MACRO setup that identifies when the best STR-Q entries will occur (post-flush).
- **CAND-20260825-treasury-buyback-debasement-regime.md:** This edge is the SHORT-TERM tactical counterpart to the structural debasement trade. The debasement trade is the "why" (dollar weakness → BTC up). This edge is the "when" (wait for flush, then buy).
- **CAND-20260901-hormuz-oil-shock.md:** The Hormuz escalation is a potential TRIGGER for the flush. If oil spikes to $100+ on further escalation, it could trigger a risk-off move that flushes BTC leverage.

## Recommended Pipeline Action
**PROMISING** — Stage for pipeline processing. Priority: MEDIUM:

1. **Build scanner:** `scanner_btc_leverage_flush.py` — tracks BTC funding rate, OI vs price momentum, F&G index, ETF flow (7-day SMA). Flags when F&G > 65 AND price flat (< 2% weekly change) AND OI above 90th percentile.
2. **Backtest:** BTC leverage flush setups (2018-2026) — test the re-entry hypothesis
3. **Deploy as:** Macro overlay on STR-Q — suppress STR-Q crypto entries when F&G > 70 AND OI elevated; deploy STR-Q aggressively after flush
4. **Priority: MEDIUM** — The setup is forming but not triggered. BTC is at $77K, F&G at 74. The flush trigger is missing. This is a "watch and prepare" edge.

## Risk Note
- **The "structural bid" counterargument:** If ETF/treasury buying is strong enough, the leverage flush may never happen — BTC could grind higher from current levels. This would make the edge a "waiting for a crash that never comes."
- **The debasement unwind risk:** If the yield surge continues (Waller was just one voice; Warsh is still Fed Chair), the structural bid disappears and BTC could drop to $60K+. This is not a flush — it's a trend change.
- **The Hormuz trigger:** A sharp oil spike could trigger a broad risk-off move that takes BTC down with everything else. In that case, the flush is a macro event, not a tactical opportunity.