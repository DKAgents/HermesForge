---
type: user-story
epic: EPIC-017
priority: P1
status: backlog
created: 2026-11-07
owner: coder
tags: [carry, funding, delta-neutral, paper-forward, structural, maker-only]
---

# US-229 — Paper-forward the delta-neutral funding carry (HYP-28/29 validated)

## Problem

The delta-neutral funding carry (long-spot / short-perp on liquid-spot majors) is
the FIRST strategy to clear the gauntlet to a real, net-positive, persistent
number: HYP-28 established ~15–21% unlevered APR (funding-true, not basis),
HYP-29 confirmed it survives G3 fill-realism at realistic maker fills (~10–12%
conservative) with ~$24.5M capacity. But the delta-neutral path in
`funding_carry.py` is currently **GATED OFF by default** (US-185 §F2), and there
is no paper-forward wiring or spot-basis accumulation. It must be stood up as a
PAPER-FORWARD strategy (emit signals, record PnL, no promotion, no go-live) and
begin accumulating the real spot basis.

## Fix

1. **Enable the delta-neutral carry path** in `funding_carry.py` for the liquid-
   spot majors only (BTC-PERP, ETH-PERP, SOL-PERP), honoring HYP-28/29:
   - Enter short-perp + long-spot ONLY when funding is sustained — rolling 24h
     mean APR >= 8% AND >= 75% of window hours positive; exit when the gate clears.
   - Trade ID `STR-FNDCARRY-<COIN>-MMDDS`.
2. **MAKER-ONLY execution (binding).** HYP-29: pessimistic/taker execution is
   decisively net-negative (−7% to −14% APR). The paper-forward leg MUST be
   post-only/maker on both legs; never a taker fill. This is a hard constraint,
   not a preference.
3. **No leverage** — unlevered carry (return on notional).
4. **Wire into the paper pipeline** (capture_signals / trade_log) as a paper-
   forward strategy: emit the carry entry/exit, record PnL = funding received
   − maker fees − basis, with the funding-vs-basis SPLIT preserved (basis is a
   separate, flagged column — never folded into the headline, per US-179).
5. **Spot-basis accumulation** — start a forward store of real BTC/ETH/SOL spot
   price vs oracle (oracle is the current proxy; the skill flags this as the one
   unmeasured input). Accumulate so the hedge stops being a proxy over the
   paper-forward window.

## Hard constraints (binding, do not relax)

- Paper-forward ONLY: `LIVE_TRADING_ENABLED` stays OFF; no promotion to Active/
  Live; no registry promotion — this is a paper-forward hypothesis per the
  gauntlet rule (accumulation must reach 6–12 months before any promotion).
- Maker-only, no leverage, delta-neutral only on the liquid-spot majors.
- No L2 spot book is held — the spot ask/bid spread is an ASSUMED input (HYP-29
  caveat); it must be re-validated live, never silently credited.
- Funding-vs-basis decomposition preserved (the HYP-28 "it lies too" check).
- Git: path-scoped commits only, never `git add -A`/`git add .`.

## Acceptance Criteria

- Delta-neutral carry path enabled for BTC/ETH/SOL with the sustained-funding gate.
- Paper-forward wiring emits carry signals + records PnL (funding − maker fees −
  basis) via the existing paper pipeline; maker-only enforced.
- Spot-basis accumulation (real spot vs oracle) running/defined for the majors.
- Funding vs basis reported as separate columns; headline = funding-only.
- LIVE off, no leverage; path-scoped commits.

## Owner / RACI
- Owner (A): coder · Responsible (R): coder · Consulted (C): backtester, risk-guardian · Informed (I): orchestrator