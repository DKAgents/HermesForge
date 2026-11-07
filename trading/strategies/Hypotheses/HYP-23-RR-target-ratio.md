---
hypothesis_id: HYP-23
source: human (coach-derived: "prefer 2:1 minimum, 3:1 preferred R:R")
venue: hyperliquid
instruments: native HL perps (dex == '')
horizon: target-dependent (exit at target, stop, or time-stop)
entry: cross-sectional 7d price momentum — long top-decile, short bottom-decile (simple, well-defined, KNOWN weak edge)
stop: 2x ATR (= 1R)
target: THE TEST VARIABLE — {1R, 2R, 3R}
cost_hurdle_bps: realistic 4.5bps/leg taker + funding + adverse entry slippage (NOT the 45bps/leg error)
data_dependencies: HF OI/mark (~/.hermes/market_data/hl_oi_hf/); funding as charge, not signal
counterparty: none claimed — this is a METHODOLOGY test (does the target ratio itself contribute edge), not a strategy candidate
topic: general
confidence: low (prior is invariance)
---

# HYP-23 — R:R target ratio does NOT change net expectancy

## Claim being tested

Coach's rule: "look for setups where we risk 1R for a possible 2+R gain — 2:1
minimum, 3:1 preferred." The question is whether the TARGET RATIO ITSELF
contributes net edge, or merely reshapes win-rate-vs-payoff (variance) while
net expectancy is invariant.

## Prior (recorded BEFORE the run)

R:R selects the breakeven win rate (3:1 -> 25%, 2:1 -> 50%/ish, 1:2 -> 67%),
not edge. For a FIXED signal + stop, net expectancy should be ~invariant to the
target; farther targets should HURT net because (a) the lower win rate amortizes
fixed per-trade fees worse, (b) longer hold pays more funding, (c) the realized
stop (worst-print ~-2.86R vs nominal -1R) dilutes the intended asymmetry MORE at
far targets. So prior: net(3R) <= net(2R) <= net(1R), i.e. "prefer 3:1" is a
variance taste, not an edge source, and at realistic cost it is net-hurting.

## Operationalization (fixed)

- Signal: cross-sectional 7d price momentum, long top-decile / short bottom-decile.
- Stop: fixed 2x ATR (1R).
- Target: {1R, 2R, 3R} — THREE runs, entry + stop identical, ONLY the target moves.
- Cost: realistic 4.5bps/leg taker + hourly funding + adverse entry slippage.
- Compare NET multi-R (after fills + funding) across the three targets, plus
  win-rate + time-in-trade (holding) so the fee/funding mechanism is visible.

## Falsification

- If net(3R) is MATERIALLY HIGHER than net(1R) and the gap survives robustness,
  the coach's R:R preference carries real edge -> revisit the prior.
- If net is FLAT or DECREASING in target (3R lowest), "prefer 3:1" is confirmed
  as variance-only and net-neutral-to-hurting at realistic cost.

## Note

This isolates the TARGET RATIO as the only free variable. It does not test
whether momentum has edge (already known weak); it tests whether raising the
target from 1R to 3R changes NET expectancy.