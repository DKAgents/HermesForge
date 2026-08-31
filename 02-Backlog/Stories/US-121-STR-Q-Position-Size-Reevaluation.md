---
id: US-121
epic: EPIC-004
type: story
status: blocked
created: 2026-08-31
points: 1
tags: [backlog, story, risk, position-sizing]
---

# US-121: Re-evaluate STR-Q Position Size Cap (1% → conditional 1.25%+)

## Story
**As a** principal trading STR-Q with an accumulating evidence base,
**I want** the 1% single-position risk ceiling re-evaluated once out-of-sample evidence makes an increase strongly recommended,
**So that** risk scales with demonstrated edge rather than staying flat indefinitely.

## Background
The "regime-matched strategy" edge candidate (CAND-20260830-regime-matched-strategy.md)
recommended raising STR-Q position size from 1.0% to 1.5% in `risk_on` regime
(+0.99R avg, 59.1% WR across 208 trades). The Risk Guardian issued a formal
**REJECT** on 2026-08-31 for two independent reasons:

1. **Hard-cap violation** — the 1% single-position ceiling is non-overridable
   in the Risk Guardian's SOUL.md. A 1.5% size breaches it regardless of edge.
2. **Evidentiary bar not met** — the 208-trade sample is drawn from the same
   ~4-day post-purge window (trade-log corruption cleared 2026-08-25), under a
   churning rule set (CONFIRMATION_BARS 3→2→1→2 within one week), with a
   quality score reweighted the same day. The +0.99R does not net out ~0.18%
   market-order drift. Regime backfill into trades.csv is unvalidated.

## Unlock Conditions (all must hold — from Risk Guardian verdict)

1. **Governance:** A principal-signed ADR amending the 1% single-position
   ceiling (Risk Guardian cannot grant this unilaterally).
2. **Evidence, rebuilt on a stable basis:**
   - ≥200 out-of-sample trades spanning multiple regimes, well beyond the
     4-day post-purge window
   - CONFIRMATION_BARS frozen at a single value for the entire sample
   - Quality-score weights stable (no mid-sample reweighting)
   - R-multiple recomputed **net of** ~0.18% market-order drift
   - Regime backfill methodology validated

## Acceptance Criteria
- [ ] ADR drafted (amendment to ADR-001 or new ADR) proposing a conditional
      risk increase with explicit ceilings (e.g. 1.25% cap, never 1.5%)
- [ ] Evidence presented that satisfies every "Unlock Condition" above
- [ ] Risk Guardian re-review issues APPROVE or CONDITIONAL
- [ ] Principal (Dan) explicitly approves the ADR
- [ ] `position_sizing.py` updated only after the above

## Notes / Context
> This story is deliberately `blocked` — it is a reminder, not active work.
> Do not begin implementation until the unlock conditions are met. The
> pipeline will accumulate evidence automatically; revisit on a recurring
> basis (see cron reminder) once ~200 clean OOS trades exist.

## Dependencies
- Blocks: Any STR-Q position size increase
- Blocked by: Evidence accumulation (≥200 stable OOS trades), principal-signed ADR

## Definition of Done
- [ ] ADR signed and committed
- [ ] Risk Guardian APPROVE/CONDITIONAL on record
- [ ] `position_sizing.py` change committed and paper-trade verified
- [ ] Documented in vault (ADR + story status)
