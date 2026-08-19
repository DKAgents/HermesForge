---
id: US-120
type: user-story
epic: EPIC-009
status: backlog
priority: medium
effort: L
created: 2026-08-19
assigned_to: unassigned
tags: [backlog, story, options, strategies, discord]
---

# US-120: Advanced Options Strategies (Iron Condors, Straddles, Calendars)

## Story
**As a** swing trader,
**I want** the options recommender to suggest advanced multi-leg strategies beyond single-leg and vertical spreads,
**So that** I can choose from iron condors, straddles, strangles, calendar spreads, and diagonal spreads when they offer better risk/reward than basic strategies.

## Context
The initial options recommender (deployed 2026-08-19, commit `19d5cd1`) supports:
- Long Call / Long Put (single-leg)
- Bull Call Spread / Bear Put Spread (debit verticals)
- Bull Put Spread / Bear Call Spread (credit verticals)

This story adds the next tier of sophistication.

## Proposed Strategies

### 1. Iron Condor
- **When:** High-IV environment, stock near a key level, expected range-bound
- **Structure:** Sell OTM call + buy further OTM call + sell OTM put + buy further OTM put
- **Use case:** Earnings season, consolidation patterns, when stop and target are symmetric around entry

### 2. Long Straddle / Strangle
- **When:** Low-IV environment expecting a big move but unsure of direction
- **Structure:** Buy ATM call + buy ATM put (straddle) or OTM call + OTM put (strangle)
- **Use case:** Breakout setups (STR-V triangles, STR-W flags) where direction is confirmed but magnitude is large

### 3. Calendar Spread
- **When:** Near-term volatility expected to drop, longer-term IV to persist
- **Structure:** Sell near-term option, buy longer-term option at same strike
- **Use case:** When DTE is very short and theta decay favors the seller

### 4. Diagonal Spread
- **When:** Combining directional bias with theta capture
- **Structure:** Buy longer-term option, sell shorter-term option at different strikes
- **Use case:** Swing trades where we want to roll the short leg weekly

### 5. Ratio Back Spread
- **When:** Strong directional bias with asymmetric risk/reward
- **Structure:** Buy 2 OTM options for every 1 ITM option sold
- **Use case:** When the target is very far from entry and we want cheap exposure

## Acceptance Criteria
- [ ] `options_recommender.py` generates iron condors when IV rank is high
- [ ] Generates straddles/strangles for breakout-type signals
- [ ] Generates calendar spreads when near-term DTE is < 15 days
- [ ] Each strategy shows: legs, net debit/credit, max profit, max loss, breakeven(s), ROI
- [ ] Strategy selection logic is documented (when to suggest each type)
- [ ] Embed field stays within Discord 1024-char limit (may split across fields)
- [ ] Backtested against historical options data if available

## Dependencies
- IV rank data (yfinance provides impliedVolatility per contract — need to compute historical IV rank)
- May need a paid options data source for historical IV (yfinance is real-time only)

## Notes
- Remind Dan about this story after US-118 and US-119 are resolved
- This is a "nice to have" enhancement — the current 3-strategy recommender covers the main use cases
- Priority should increase if Dan starts actively using the options ideas in the embeds