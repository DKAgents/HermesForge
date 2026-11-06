---
hypothesis_id: HYP-20
source: internal (evidence-directed — cross-sectional positioning)
venue: hyperliquid
instruments: native HL perps (dex == '') with sufficient OI history
horizon: daily rebalance; also report 5d holding to reduce turnover
entry: cross-sectional rank by trailing 7d OI change; long top-decile, short bottom-decile
exit: next rebalance
expected_gross_edge_bps: unknown (measured, not assumed); prior = momentum (rising OI -> relative strength)
cost_hurdle_bps: 45 (both legs, fail-closed taker)
data_dependencies: HF OI dataset (~/.hermes/market_data/hl_oi_hf/, hourly OI+mark, 3.5y x 553 mkts); funding store (~400d) if locatable for H2
counterparty: cross-sectional — the relative-value repricing of capital flows across the perp complex; no single named loser (diversified relative-value)
topic: general
confidence: medium
---

# HYP-20 — Cross-sectional positioning momentum (OI, + funding)

## Motivation (why this, why now)

Every falsified hypothesis so far was a SINGLE-ASSET, TIME-SERIES timing signal
("buy when *this* coin's oscillator/OI is at an extreme"). Those are the most
arbitraged-away edges. HYP-16 tested OI the wrong way — a coin's OI vs its OWN
history (time-series, null). The UNTESTED question is CROSS-SECTIONAL: does a
coin's OI (positioning) RELATIVE TO OTHER COINS right now predict its RELATIVE
future return?

Cross-sectional is the ONLY signal class that cleared G3 so far (xsmom), and we
now finally hold 3.5y x 553 markets of OI to test it. Funding is a second view of
the same underlying quantity (where capital/leverage is positioned).

## Pre-registered operationalization (fixed; no post-hoc tuning)

- **Universe:** native HL perps (dex == ''). Resample hourly OI+mark -> daily per
  coin (OI = last hourly reading; close = last mark).
- **Signal (H1):** cross-sectional rank of trailing 7d OI % change (log change).
  Long top-decile, short bottom-decile, rebalanced daily. Prior = MOMENTUM
  (rising OI -> relative strength); report the sign honestly either way.
- **Signal (H2):** cross-sectional rank of current funding rate, IF the funding
  store has usable history (~400d). Test BOTH directions (continuation, per
  HYP-17's funding finding; and the fade) — the direction that wins is reported,
  not assumed.
- **Variant (V-A, pre-committed):** 7d -> 30d OI change (slower signal).
- **Holding:** 1d (daily rebalance) primary; 5d holding reported separately to
  show cost-sensitivity to turnover.

## Falsification (kill rules)

- H1 KILL: top-minus-bottom spread return <= 0 NET of 45bps both-legs fail-closed
  taker, OR G4 CPCV 10th-pct PF < 1.0 / G5 PBO > 0.30 / DSR < 0.95.
- H2 KILL: same, if data available.
- If neither cross-sectional OI nor funding produces a cost-surviving spread,
  reject the "relative positioning -> relative return" thesis across the whole
  perp complex.

## Notes

- This is NOT another time-series OI test (HYP-16 falsified that). It is
  cross-sectional relative value — a structurally different question.
- Counterparty is honest: diversified relative-value repricing, not a single
  named loser. The cross-sectional spread must be positive net of both-legs cost.
- Base rate is low; a null here is still a real negative (it closes the
  cross-sectional-positioning class on real data).
