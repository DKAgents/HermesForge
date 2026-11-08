---
hypothesis_id: HYP-27
source: internal (HYP-26 follow-up: sub-daily cascade, the part HYP-26's daily op missed)
venue: hyperliquid
instruments: native HL perps, primary BTC (near-full 5m feed) + ETH/SOL where coverage allows
horizon: intraday — 5m / 30m / 1h / 2h forward returns
signal: liquidation CLUSTER — a 5m bucket with unusually large net forced-sell (or forced-buy) notional
data_dependencies:
  - liquidations: ~/.hermes/market_data/hl_liquidations_hf/data/fills/*.parquet (tick-level)
  - 5m bars: ~/.hermes/market_data/hl_bars/bars_5m.db (35 tickers, ~2026-06-15 -> now; BTC near-full)
cost_hurdle_bps: realistic 4.5bps/leg taker + adverse slip (funding is negligible intraday)
counterparty: over-leveraged longs being force-closed into a falling tape (and vice-versa)
topic: structural
confidence: low
has_quotes: false
tags: []
---
# HYP-27 — Intraday liquidation cascade (sub-daily continuation)

## Motivation

HYP-26 tested liquidation flow at the DAILY horizon and found REVERSAL
(exhaustion), |IC| ~0.02 — too weak to trade. But the pre-registered prior was
that the CASCADE (continuation) is INTRADAY and mechanical: a wave of forced
selling pushes price DOWN, triggers the NEXT liquidation, self-reinforcing. The
daily operationalization could not see it. This test measures the cascade AT
the intraday resolution where it should live.

## Pre-registered operationalization (fixed)

- Aggregate liquidation FILLS to 5m buckets of NET notional per market
  (buy notional − sell notional). A long-liquidation = forced sell = downward.
- Detect a CLUSTER as a 5m bucket whose |net liquidation notional| is in the
  top-decile of that market's own recent distribution (fixed rule, pre-committed).
- Test the forward return over the next {1, 6, 12, 24} 5m-bars (5m/30m/1h/2h):
  - H1 CASCADE / continuation: net forced-sell cluster -> price continues DOWN;
    net forced-buy cluster -> continues UP.
  - H2 exhaustion: the opposite. Report BOTH arms.
- Universe: BTC first (near-full 5m feed); ETH/SOL second if 5m coverage is
  adequate at their liquidation dates. The 5m store covers ~2026-06-15 -> now,
  so this is a DATA-CONSTRAINED FIRST LOOK (~5 months) — flag that explicitly.
- Cost: realistic 4.5bps/leg taker + adverse slip; funding ~0 at this horizon.
- Timing: fill at the first bar AFTER the cluster bar closes (no look-ahead).

## Prior (recorded)

The cascade is real, mechanical, and FAST (minutes). It is also the most
well-known, most crowded effect in crypto microstructure — the liquidator flow
itself is the counterparty profiting from it. Net-tradeable edge at a horizon WE
can actually fill (after the cluster is observable + cost) is unlikely, but this
is the first time we measure it at the right resolution on real forced-flow data.

## Falsification / promotion

- Report continuation vs reversal net per horizon (5m-2h), on the ~5-month first look.
- Promote only if a cell is economically motivated, beats any control, and would
  clear cost at a fillable horizon. If the cascade is confirmed real-but-fast
  (positive at 5m, gone by 1-2h, dead after cost), that is the honest structural
  answer, not a tradeable edge — and it CLOSES the liquidation class definitively.

## Note

This is the last question on the liquidation data: does the sub-daily cascade
exist, and is it harvestable, or is it exactly the fast-and-crowded effect the
prior predicts?