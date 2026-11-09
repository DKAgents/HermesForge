---
hypothesis_id: HYP-33
source: internal (crowd-direction contrarian positioning — the untested axis)
venue: okx (public long/short ratio; HL for tradeable price)
instruments: BTC/ETH (and majors where the ratio resolves)
horizon: daily-weekly
signal: crowd long/short ratio (account + taker + top-trader) — contrarian (fade the extreme crowd)
data_dependencies:
  - long/short ratio: OKX public `rubik/stat/contracts/long-short-account-ratio` + `taker-long-short-ratio` (+ any top-trader variant) — CHECK REACH (may be data-gated to ~3mo free)
  - price: existing HL mark/oracle
cost_hurdle_bps: realistic taker + funding
counterparty: the over-positioned retail crowd (fade them)
topic: positioning (contrarian)
confidence: low-medium (contrarian positioning is a documented edge, but likely partly arbitraged + may be data-gated)
has_quotes: false
tags: []
---
# HYP-33 — Crowd long/short ratio (contrarian positioning)

## Motivation

Everything nulled so far was a LEVEL signal (how much OI/funding). The untested
axis is the crowd's DIRECTION: the long/short ratio (retail account ratio, taker
ratio, top-trader ratio). Contrarian positioning — fade the extreme retail crowd
(heavily-long crowd -> short; heavily-short -> long), follow the top-traders — is
a documented edge and a genuinely different signal from OI level.

## Pre-registered operationalization (fixed)

- H1 RETAIL FADE: when the retail long/short ratio is in an extreme decile
  (heavily one-sided), fade it (short extreme-long, long extreme-short).
- H2 SMART-MONEY FOLLOW: when the top-trader ratio diverges from the retail
  ratio, follow the top-trader side.
- Universe: BTC/ETH. Cost realistic.

## Prior (recorded)

Contrarian positioning is real but well-known -> partly arbitraged, and it is
often a short-horizon/lagged signal. The honest open question is data reach (OKX
rubik may only serve ~3mo free) — if so, REPORT DATA-GATED rather than fabricate.

## Falsification / promotion

- Promote only a contrarian cell that is net-positive, leading, and robust. If
  the ratio is a coincident echo (like HYP-32's flow) or data-gated to a trivial
  window, report honestly and do NOT promote.

## Note

The data-reach question is load-bearing: if free history is ~3 months, this is
DATA-GATED, not testable — flag it and stop rather than test on an inadequate window.