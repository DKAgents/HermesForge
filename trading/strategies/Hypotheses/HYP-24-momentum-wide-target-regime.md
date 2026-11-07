---
hypothesis_id: HYP-24
source: internal (combines HYP-22 regime finding + HYP-23 target finding)
venue: hyperliquid
instruments: native HL perps (dex == '')
horizon: target-dependent (3R target, 2x ATR stop)
entry: cross-sectional 7d price momentum — long top-decile, short bottom-decile
stop: 2x ATR (= 1R)
target: 3R (fixed — HYP-23 showed wide target > tight for net)
cost_hurdle_bps: realistic 4.5bps/leg taker + funding + adverse entry slip
data_dependencies: HF OI/mark (~/.hermes/market_data/hl_oi_hf_clean/ for cleaned BTC regime; hl_oi_hf/ for mark returns)
counterparty: none claimed (methodology-combination test)
topic: general
confidence: low
---

# HYP-24 — momentum x wide-target x regime (combined)

## Motivation

Two findings, not yet tested TOGETHER:
- HYP-23: a WIDE (3R) target beats a tight (1R) target for net — the tight target
  is a fee tax on the momentum signal's weak drift; the wide target lets it run.
- HYP-22 + conditional grid: REGIME conditions the signal (funding -> bear
  continuation / bull reversal; xsmom/OI-level showed regime structure).

The open question: does momentum with a WIDE target become NET-POSITIVE in a
specific REGIME (e.g. risk-on), combining the two levers?

## Pre-registered operationalization (fixed)

- Signal: cross-sectional 7d momentum, long top-decile / short bottom-decile.
- Stop: 2x ATR; Target: 3R (the HYP-23 wide target). Fixed — not re-tuned here.
- Regime split: BTC 200d SMA (risk-on = BTC above + rising; risk-off = below;
  range = within band) — the pre-registered taxonomy + the CLEANED BTC series.
- Report net multi-R, PF, win-rate per regime (and per top asset), full matrix.

## Prior (recorded)

Momentum's unconditional drift is weak (t < 1). The wide-target gain is partly
log-normal geometry, not alpha. So the prior is: even combined, no regime cell
turns net-positive after the geometry is accounted for — but this is the natural
test of the two levers together, and a real regime cell (economically motivated +
sample-adequate + surviving a zero-drift control) would be a genuine finding.

## Falsification

- If no regime cell is net-positive (after funding+fees, with adequate sample and
  a zero-drift control discounting the geometric tilt), the combined levers still
  don't produce a tradeable edge -> close the momentum direction.
- A net-positive cell is promoted ONLY if economically motivated + robust.

## Note

This is the last assembly of the pieces on the momentum signal: wide target +
regime conditioning together. If it's still null, momentum is closed as a
tradeable-edge source and we move to the data-gated classes (liquidations, L2,
basis, vol).