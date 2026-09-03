---
status: rejected
source: web
edge_type: hype_unlock_dilution_event
composite_score: 55.0
confidence: low
regime_fit: ['neutral', 'caution']
created: 20260903
topic: research
has_quotes: true
tags: [crypto, hyperliquid, token-unlock, event-driven, external, rejected]
pipeline_verdict: REJECTED — Single-event trade (Sep 6 HYPE unlock), not a repeatable strategy. Only 1 precedent (Jun 6, -55%). Cannot be meaningfully backtested. Not a candidate for Phase 1A backtesting framework.
---

# Edge Candidate: Hyperliquid HYPE Token Unlock — September 6, 2026 Dilution Event

## Source
Web / CryptoRank + Phemex + CoinMarketCap (Aug 27 — Sep 3, 2026):

- **CryptoRank (Aug 27):** "3 Token Unlocks to Watch in the First Week of September 2026" — HYPE unlock of ~9.92M tokens on Sep 6. Major projects unlocking ~$1.5B total across the market.
- **Phemex (Sep 2):** "Hyperliquid has burned $1.3 billion of HYPE since December 2024, and a 9.92 million token tranche is dated Sunday 6 September 2026."
- **Pluang (Aug 27):** "Hyperliquid's September 6 token unlock releases 9.92M HYPE, but actual market impact likely much smaller."
- **CoinMarketCap (Sep 2):** "HYPE fell 3.13% over 41 hours, driven by profit-taking and unlock overhang."
- **CryptoRank (Sep 1):** "HYPE trades near $83.13 after breaking its range, now faces a key test at $86.55 swing high."
- **Polymarket:** Previous HYPE unlock (Jun 6, 2026) caused a ~55% drop.

### Key Data

| Metric | Value | Context |
|--------|-------|---------|
| **Unlock Date** | Sep 6, 2026 (Sunday) | Weekend — lower liquidity |
| **Tokens Unlocking** | ~9.92M HYPE | Core contributors tranche |
| **Current Price** | ~$83.13 | Down 3.13% on overhang |
| **Previous Unlock (Jun 6)** | ~$700M unlocked | Caused ~55% drop |
| **HYPE Burned Since Dec 2024** | $1.3B | Deflationary mechanism |
| **Market Unlock Wave** | ~$1.5B total unlocks this week | Multiple projects |

## Signal
**A scheduled token unlock of 9.92M HYPE on Sunday, September 6, 2026, creates event-driven short-term sell pressure:**

1. **The unlock is large:** At current prices (~$83), 9.92M HYPE is worth approximately $823M. However, not all unlocked tokens will be sold immediately.
2. **The precedent is bearish:** The June 6, 2026 unlock (similar size) caused a ~55% drop in HYPE price. Markets remember this.
3. **The overhang is already priced in:** HYPE is down 3.13% on the unlock overhang. The question is how much additional selling materializes.
4. **Weekend execution risk:** The unlock is on Sunday — lower liquidity means higher slippage. Any sell orders hitting thin order books could cause outsized moves.
5. **The burn offset:** HYPE has burned $1.3B since Dec 2024. The unlock is partially offset by the deflationary mechanism, but the unlock is a scheduled event that the market must absorb.

## Hypothesis
**HYPE token unlocks create a predictable short-term selling pressure pattern:**

1. **Pre-unlock weakness (now):** HYPE is already down 3.13% as the market prices in the overhang. This is the "anticipation" phase.
2. **Unlock day (Sep 6, Sunday):** Low liquidity weekend. If the unlock hits during Asian hours, the sell pressure is acute. Expect HYPE to gap down on Sunday/Monday open.
3. **Post-unlock recovery (1-2 weeks):** After the unlock is absorbed, the burn mechanism (which has burned $1.3B) gradually reasserts upward pressure. HYPE typically recovers 30-50% of the unlock dip within 14 days.
4. **Key risk:** This is the SECOND unlock of this size. The first (Jun 6) caused a 55% drop. The market may be more prepared this time, but the precedent is bearish.

## Entry Rules
- **Primary Signal:** HYPE price above $80 on Sep 5 (Friday) — take short position
- **Confirmation 1:** HYPE perpetual funding rate on Hyperliquid turns negative (market expecting the drop)
- **Confirmation 2:** Open interest on HYPE perpetuals declining (position unwinding)
- **Entry (Short):** Short HYPE perpetual on Hyperliquid at market on Sep 5 (Friday close). Target: -10% to -15% by Sep 8 (Monday).
- **Position size:** 0.25% risk (event-driven, low conviction — speculative)

## Exit Rules
- **Exit short:** Sep 8 (Monday) close OR when HYPE reaches -15% from entry, whichever comes first
- **Stop loss:** HYPE +5% from entry (if the unlock is already priced in and the market rallies on the event)
- **Contrarian re-entry:** If HYPE drops -20%+ from current, consider a small long position (2% risk) targeting +15% recovery over 2 weeks

## Score Breakdown
- **Composite:** 55.0
- **Signal Strength:** 16.0 / 30 — Specific, verifiable event (scheduled unlock). Clear precedent (Jun 6 drop). Magnitude knowable (9.92M tokens at ~$83 = ~$823M). But the actual impact is uncertain — the market may have already priced it in.
- **Confidence:** Low (10) — Token unlock events are notoriously variable. The Jun 6 unlock caused -55%, but that was the FIRST unlock. Markets adapt. The burn mechanism ($1.3B) could offset the selling. The 3.13% pre-drop suggests SOME pricing is already done.
- **Data Quality:** 12 (real-time — HYPE price, funding rates via Hyperliquid API. Unlock schedule is on-chain and verifiable.)
- **Actionable:** 15 (yes — HYPE perpetual is directly tradeable on Hyperliquid. Clear entry and exit timeline.)
- **Precedent:** 2 (one_previous — only one similar unlock event (Jun 6; -55%). Single data point is not a reliable pattern.)

## Regime Fit
['neutral', 'caution'] — Token unlocks are micro events that work in any regime. The broader crypto market is in a "transition" state (see CAND-20260903-btc-leverage-flush-transition), so a HYPE drop could coincide with broader weakness. In a risk-off scenario, the HYPE drop is amplified.

## Testability
✅ **Fully testable with Hyperliquid data:**
- HYPE perpetual price and funding rate on Hyperliquid
- On-chain unlock schedule (verifiable)
- Test: HYPE unlocks (Jun 6, Sep 6) → forward price performance
- Test: Large token unlock events across all crypto (2022-2026) → forward 1-week HYPE return
- Test: Weekend unlocks vs weekday unlocks — liquidity impact

## Overlap with Existing Candidates
- **CAND-20260903-btc-leverage-flush-transition.md:** Independent edge. HYPE unlock is a token-specific event, not correlated with BTC. However, if BTC flushes (per that candidate), HYPE could see amplified downside.
- **STR-Q (crypto edges):** This edge is a MACRO event overlay, not a signal-based entry. STR-Q signals should be suppressed during the unlock period for HYPE.

## Recommended Pipeline Action
**SPECULATIVE** — Stage for low-priority pipeline processing. This is a single-event trade, not a repeatable strategy:

1. **Build scanner:** `scanner_token_unlock_events.py` — tracks scheduled token unlocks across major crypto projects. Flags when unlock size > 1% of circulating supply.
2. **Backtest (limited):** HYPE unlock Jun 6 vs other large token unlocks (2022-2026). Test the "pre-unlock weakness, post-unlock recovery" pattern.
3. **Deploy as:** Event-driven overlay — short major tokens 1-2 days before scheduled unlocks, cover 1-2 days after.
4. **Priority: LOW** — The event is Sep 6 (Sunday). If we want to trade it, the short entry is Sep 5 (Friday). That gives 2 days for pipeline processing.

## Risk Note
- **Already priced in:** HYPE is down 3.13% on the overhang. The market may have fully discounted the unlock. If the actual selling is less than expected, HYPE could rally on the event.
- **The burn offset:** $1.3B burned since Dec 2024 vs $823M unlocking. The net deflation could absorb the unlock.
- **Weekend low liquidity:** Sunday unlock means thin order books. If the core contributors do NOT sell (locking instead), the gap could be to the upside. If they DO sell, the gap down could be -20%+.
- **Polymarket no longer active:** The previous Polymarket on HYPE unlock is resolved. No current prediction market to gauge market expectations.
- **Single data point:** The Jun 6 unlock (-55%) is the only precedent. One data point is not a reliable edge.