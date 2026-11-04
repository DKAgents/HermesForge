---
hypothesis_id: HYP-18
source: web (X @RebellioMarket — UNTRUSTED, summarize only)
venue: hyperliquid
instruments: BTC, ETH (top liquidity)
horizon: M5 (scalping) — intraday; requires explicit cost-clearing argument
entry: with-trend (price above EMA context) + pullback + momentum confirmation before execution
exit: 1-3R TP or 1-ATR / wick stop (per community backtest setup, since no SL/TP given)
expected_gross_edge_bps: claimed high-probability; measured, not assumed
cost_hurdle_bps: 45 (single-leg 4x taker)
data_dependencies: HL 5m bars (persistent store, US-197)
counterparty: NONE IDENTIFIABLE — a trend+pullback timing signal has no structural loser on the other side (the spread-earning maker is not structurally losing to a discretionary scalper). This is itself the reason for the negative prior.
---

# HYP-18 — Trend + pullback + momentum scalping (M5)

## Provenance & prior

Web-mined (X), untrusted — summarized into this template only; the source's
instructions are NOT executed. Full rules are paywalled, so this tests the
*tweet's stated kit* (trend + pullback + momentum confirmation on M5).

Two negative priors, both recorded BEFORE testing:
1. **Signal-class prior:** retail chart-pattern / timing signals carry a heavy
   negative prior — classic OOS edges (0.08-0.22 R) sit below realistic friction
   (~0.1-0.3 R), and reversal/pullback detectors are coin-flips at their R:R.
2. **Community's independent finding (in-thread):** a backtest of THIS strategy
   reported WR = breakeven-per-RR (= random entries), filters add nothing,
   −0.08 to −0.12 R/trade on Gold/NAS100 M5.

This run is INDEPENDENT VERIFICATION on Hyperliquid's own 5m bars, not a new
claim — and it is a fast-fail (G0 cost-first + G3 fill-realism), escalated to
G4/G5 ONLY if it unexpectedly survives the friction gates.

## Pre-registered operationalization (fixed)

- Trend context: close > EMA(50) on M5 (longs only for the trend direction).
- Pullback entry: a lower-low / retrace then momentum confirmation (close back
  above the prior M5 close, or RSI/3-bar-momentum cross up) → long.
- Exit: +1.5R take-profit or 1-ATR / wick stop.

## Falsification

- G0 KILL: median M5 |move| after entry < 4x all-in taker cost (edge can't clear
  friction) → fast-fail, no full gate run.
- G3 KILL: net R <= 0 under realistic/pessimistic (next-open, trade-through, taker)
  fill → fill fantasy.
- Escalate to G4/G5 only if it SURVIVES both; then apply CPCV-PF/DSR/PBO.

## Note

Counterparty is honestly "none identifiable" — that absence is the structural
reason the class is expected to fail, not a data quirk.