---
id: STR-20260920-wintermute-mm-pattern
type: strategy
status: hypothesis
asset_class: crypto
venue: hyperliquid
trade_style: swing
timeframe: daily
confidence: medium
last_reviewed: 2026-09-20
hypothesis_id: HYP-11
gates_passed: [G0, G3]
fee_tier_assumed: taker
---

# Wintermute MM Pattern (HYP-11)

## Thesis

Market makers (Binance/Wintermute) run predictable 3-wave cycles on crypto
majors. Each wave is a directional move followed by a ~50% pullback. After
3 waves complete, the total range pulls back 50%, providing a high-probability
entry at a level where the market maker is likely to defend.

Pattern described by MartyParty (Sep 23, 2025).

## Entry Criteria

1. Detect 3 completed waves, each: directional move ≥150 bps, pullback 35-65%
2. Current price near 50% retracement of total 3-wave range
3. Quality score ≥40 (pullback precision + wave consistency)
4. Direction: dominant recent wave direction

## Exit Criteria

- Stop: 61.8% retracement of total range (below the entry zone)
- Target: prior structure high/low (the peak of the 3-wave structure)
- Time stop: 21 bars (~1 month on daily)

## Risk Rules Applied

- Position size: 1.0% risk (1% cap)
- Venue-correct costs: 12 bps crypto perps
- Cost drag: ~0.04R (2.7% risk at 12bps → negligible)
- Min R:R: 1.5:1 after costs

## Supporting Evidence

- G0 pass: daily moves 138-294 bps vs 54 bps needed (BTC/ETH/SOL)
- G3: cost drag negligible due to wide stops (2.7% risk)
- Wave detection: 183 waves found in BTC history, pattern fires on majors
- Source: MartyParty Twitter thread, Sep 23 2025

## Counter-Evidence

- Pattern is theoretical — not backtested yet (needs Phase 1a)
- Quality threshold (40/100) is arbitrary first-pass
- Market makers may change behavior
- 3-wave pattern can be post-hoc fitted

## Change Log

- 2026-09-20: Created from MartyParty tweet analysis. Registered HYP-11.