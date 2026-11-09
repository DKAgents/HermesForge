---
hypothesis_id: HYP-37
source: web (Tokenomist + Keyrock unlock event studies; scheduled fundamental supply events)
venue: hyperliquid
instruments: HL perps on tokens with a scheduled unlock >= threshold (1%/2%/5% of circulating supply)
horizon: swing — short T-30 -> T-1 and T-14 -> T+3 (pre-registered, no tuning)
signal: short the token into a scheduled token-unlock supply overhang; NOT a price signal — a scheduled fundamental supply event
data_dependencies:
  - D-7 unlock calendar (token, date, amount, % of circulating supply) — Tokenomist / DefiLlama emissions (VERIFY API tier vs budget)
  - HL perp prices (mark/oracle) — ~/.hermes/market_data/hl_oi_hf_clean/*.parquet (2023-05+)
  - HL funding — ~/.hermes/market_data/hl_funding_hf/*.parquet (2023-05+)
  - BTC reference for beta-neutralization — crypto/BTC.parquet (2020-08+)
cost_hurdle_bps: taker ~4.5 bps/leg (2 legs ~9 bps) + funding P&L on the short (signed; small)
counterparty: unlock recipients + front-runners selling into a scheduled supply overhang; the other side is the passive bid that cannot absorb the sudden supply on an early thin-float token
topic: structural (scheduled fundamental supply event — NOT retail-TA / chart-pattern / ICT-SMC)
confidence: low-medium (prior literature reports a real median drift, but it is a data-gated, thin-float, small-capacity effect)
note: renumbered from directive §8. Collision chain: directive label "HYP-31" is taken (cross-venue basis); "HYP-36" is claimed in-flight by a concurrent agent (polymarket longshot overpricing, itself renumbered from a "HYP-28" collision). Assigned next free ID HYP-37.
---

# HYP-37 — Token-unlock pre-event drift (short)

## Motivation

Scheduled token unlocks are a *fundamental supply event*, not a price signal:
recipients and front-runners sell into the known future supply, and early
thin-float tokens cannot absorb it. The counterparty is the passive bid that
fails to absorb a sudden supply overhang. This is a structural, calendar-driven
edge source — a different class from the price/positioning/flow signals already
searched to null.

## Prior (recorded)

- Tokenomist event study: median ~1-month pre-event drift ~-14.7% vs BTC;
  large unlocks hit early thin-float tokens ~-15% while liquid tokens were
  largely unaffected.
- Keyrock ~16,000-event study: most unlocks carry negative pressure starting
  ~30 days before the event.
- Unlocks below ~1% of circulating supply show little impact (so the threshold
  is load-bearing).

## Pre-registered operationalization (fixed)

- EVENTS: token-unlocks with unlock size >= a pre-registered threshold of the
  token's circulating supply, on tokens that have HL perps. Three thresholds,
  reported separately: 1%, 2%, 5% of circulating supply.
- WINDOWS (pre-registered, no tuning): short T-30 -> T-1, and T-14 -> T+3.
- BTC-beta-neutral: return measured relative to BTC (token return minus
  beta*BTC return over the window). No leverage.
- FUNDING P&L on the short is included in net P&L (funding is signed: positive
  funding_rate = short receives; negative = short pays).
- LEAKAGE: use unlock schedules AS KNOWN AT THE TIME (schedules get revised);
  include delisted tokens (avoid survivorship).

## Falsification / promotion

- FALSIFY if: median BTC-relative return >= 0, OR 10th-percentile profit factor
  < 1.0 net of fees + funding.
- Promote only if the pre-event drift is negative, robust, and net-positive
  after cost + funding across the pre-registered thresholds, at small capacity.

## Data gate (blocking, first)

D-7 (the unlock calendar) is the binding dependency. It must provide, per
event, the token, the date, and the % of circulating supply, historically and
as-known-at-time. If only a paid tier (Tokenomist / DefiLlama emissions) is
reachable, the hypothesis is DATA-GATED — reported untested-not-rejected, like
HYP-33, and reopened automatically once the calendar is reachable (or
forward-accumulated).
