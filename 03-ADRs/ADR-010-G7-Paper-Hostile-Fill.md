---
id: ADR-010
type: adr
status: proposed
created: 2026-11-02
deciders: [architect]
tags: [adr, gauntlet, gate-g7, forward-validation, hostile-fill]
topic: adrs
confidence: high
has_quotes: false
source: HermesForge ADR
---
# ADR-010: G7 Forward Validation on Paper with the Hostile Fill Model

## Status
**proposed** — records the G7 clarification BEFORE it takes effect.
No running gate code is altered by this ADR; the change is binding only after
human approval and path-scoped implementation (US-209).

## Context

G7 ("Forward validation") is the final gate before a strategy is promoted
Hypothesis → Active. Today its pass criteria are:

    ≥ 100 trades or 30 sessions · realised slippage ≤ 1.5× modelled ·
    live avg R ≥ 50% CPCV median

The problem is not the thresholds — it is the **ledger the "live" results are
scored against**. The existing forward path (`paper_trading/trades_log.csv`,
captured by the sweep/VRP forward scripts) records fills at the **optimistic
paper ledger**: signals are assumed to fill at a favorable price (typically the
signal/close price or mid), with no queue-position realism, no adverse
selection, no fee drag beyond a flat assumption. This is exactly the ledger that
the pipeline's own G3 gate exists to distrust — the *optimistic* mode of
`execution_sim.py`.

Scoring G7 forward results on the optimistic ledger means a strategy can "pass
forward validation" on fills it would never actually receive, then be promoted
with a paper edge that evaporates the moment it touches a real book. The memory
of STR-Q's −8,447 R bar-level reality vs. its frictionless chart-pattern
promotions is the canonical failure here: forward validation using the optimistic
ledger is not validation at all.

There is NO live venue approved yet (`LIVE_TRADING_ENABLED` is off, human-gated).
So G7 has no real-money path to validate against. The correct forward-validation
instrument is **paper**, but paper scored under the **Hostile Fill model** — the
bar-level realistic fill — not the optimistic ledger.

## Decision

G7 forward validation runs on **paper**, but every simulated fill is produced by
the **Hostile Fill (bar-level realistic) model**, never the optimistic paper
ledger, until a human explicitly approves a live venue.

### 1. What "Hostile Fill model" means (binding)

The Hostile Fill model for G7 is the **pessimistic / bar-level-realistic** fill
path already implemented for G3 and for PnL integrity:

- fills at the **aggressive (taker) side**, not mid — `execution_sim.PESSIMISTIC`
  ("always taker at the cross + one tick adverse selection");
- **bar-level** resolution: fills are constrained to the actual bar (no sub-bar
  favorable prices, no look-ahead to a better tick within the bar);
- fees applied via the **dynamic, fail-closed** `fee_source` (US-165) — never a
  flat favorable constant, never the optimistic zero-slippage assumption;
- funding accrued hourly across any settlement crossing.

Concretely this is the same fill engine the `hostile_fills*.py` PnL-accounting
path uses, applied to the forward signal stream. It is NOT `fill_mode=OPTIMISTIC`
and it is NOT the `trades_log.csv` close-price capture.

### 2. G7 pass criteria (thresholds unchanged, ledger changed)

The thresholds are unchanged; only the *source of truth for the realised series*
changes:

    ≥ 100 trades or 30 sessions · realised slippage ≤ 1.5× modelled ·
    live avg R ≥ 50% CPCV median

but `realised slippage`, `live avg R`, and the trade count are all computed from
Hostile-Fill (bar-level realistic) fills. A strategy that cannot produce a
non-negative realistic edge under these fills does not pass G7, regardless of
what the optimistic ledger would have said.

### 3. Human go-live terminates the paper-hostile requirement

The paper-hostile requirement applies **only until a human approves a live
venue**. The moment a live venue is approved (human-gated, ADR-002 / ADR-007),
G7 forward validation moves to live paper-capture against that venue's real
fills, and the paper-hostile path is retired for that strategy. Until that
approval, paper-hostile is the ONLY forward-validation instrument — there is no
"optimistic fallback."

## Rationale

- Forward validation exists to catch the gap between backtest edge and realized
  edge. If the forward ledger is optimistic, that gap is systematically hidden,
  and G7 becomes a rubber stamp.
- The Hostile Fill model is the same engine the pipeline already trusts for G3;
  reusing it for G7 removes the inconsistent "two different ledgers" problem
  (G3 is pessimistic, G7 was optimistic).
- There is no live venue, so the only honest forward test is paper — but paper
  is only honest if the fills are realistic.

## Consequences

**Positive:** G7 promotion now requires a realistic, bar-level edge, closing the
most dangerous remaining promotion path (frictionless-paper → Active).

**Negative / trade-offs:** forward validation becomes markedly more conservative;
strategies that only clear the optimistic ledger will no longer promote. This is
intended — the pipeline's observed outcome has been "zero strategies reach G7,"
and a stricter G7 is not the bottleneck when the failures are already upstream
(EPIC-017 diagnostic §5).

**Risks:** the Hostile Fill model may be *more* pessimistic than reality in
adverse-selection terms; a strategy with a genuine (small) real edge might be
falsely rejected at G7. Mitigation: the fill engine already models three modes;
G7 uses the pessimistic mode by design, and the optimistic/realistic modes
remain visible in the same report so a false rejection is diagnosable.

## Assumptions & Open Questions (explicit)

- A1 The Hostile-Fill engine's bar-level realism for the *forward* stream
  requires a live L2 / bar source at capture time; if L2 is unavailable, the
  forward fill must FAIL CLOSED (no fill recorded, no fabricated bar) rather
  than silently fall back to mid. Confirm this matches US-199's fail-closed bar
  policy.
- A2 "Bar-level realistic" needs a precise definition of the adverse-selection
  tick (one tick vs. spread). OPEN — pin the exact tick model so G3 and G7 use
  the identical pessimistic definition.
- A3 The transition rule from paper-hostile to live capture ("the moment a live
  venue is approved") needs a concrete handoff artifact (a flag/registry field
  marking the epoch at which live capture supersedes paper-hostile). OPEN.

## Review Date
Revisit at the first human live-venue approval or 2027-01-02, whichever first.

## Related
- [[US-209-G7-Paper-HostileFill]] · [[US-181-vol-VRP-forward]] · [[PROP-001-§02]]
- [[ADR-008-G1-Size-Relative-Capacity-Power-Floor]] · [[ADR-009-G0-Maker-Taker-Cost-Model]]