---
topic: risk
confidence: high
has_quotes: false
tags: []
source: HermesForge Risk Framework
created: 2026-07-26
---
# ADR-005 Implementation Log

**ADR:** ADR-005 (Stage-Based Model Floors and Red Team Review) — accepted 2026-07-26
**This log:** records what was actually built, tested, and verified for each workstream, plus known limitations. Read this alongside the ADR itself — the ADR describes the policy, this describes the real implementation state.

## Workstream 1 — Red Team agent profile

**Built:** `~/.hermes/profiles/red-team/` — full profile directory structure, `SOUL.md` defining identity, advisory-only hard rules, T3 default model routing, output format, and findings-log location (`~/HermesForge/07-Risk/RedTeam/`).

**Tested:** Ran a real adversarial review (via delegate_task, simulating the red-team role's instructions) against strategy hypothesis `STR-20260719-ma-pullback-fibonacci-entry`. Result: 10 findings produced (3 critical, 6 concerning, 1 informational), zero approve/reject verdict issued, explicit role disclosure included, findings framed as questions for the owner/Risk Guardian. Behavior matches the ADR's advisory-only contract.

**Known limitation:** the test ran under the parent session's model (Sonnet 5), not a true profile switch to `red-team`'s T3 default — this validates the *behavioral* contract (advisory-only, no verdict) but not yet the *model-routing* contract (T3 default in actual live use). First live invocation of the red-team profile itself should confirm T3 routing.

## Workstream 2 — Hand-off contract enforcement (Option B)

**Built:** `~/HermesForge/scripts/governance/validate_handoff.py` — a standalone validator that checks the five required contract fields (`stage`, `tier`, `consumes`, `produces`, `downstream_allowed`), enforces the stage→tier floor table from ADR-005, and writes every validation attempt (pass or fail) to `~/HermesForge/07-Risk/Governance/handoff_audit_log.jsonl`.

**Piloted on:** `coder` profile only, per the plan's phased rollout (not all 8 agents at once). `~/.hermes/profiles/coder/SOUL.md` now requires declaring and validating a contract before any delegation, with the exact command to run and explicit "do not proceed on failure" instruction.

**Tested:** three real runs — (1) valid T3 `draft` contract passed, (2) `decide` stage declared at T3 correctly rejected (below T2 floor), (3) contract missing three required fields correctly rejected. All three logged to the audit file, confirmed via direct file read.

**Known limitation (important — do not overstate this):** there is no orchestration service or runtime layer in front of `delegate_task` in this system. This validator is a gate the calling agent's own instructions require it to run — it is not mechanically unskippable. An agent could, in principle, delegate without running it. This is "Option B" in spirit (a real validator that fails loudly, not just a convention) but not a true interceptor. Closing this gap further would require either (a) a wrapper/harness around delegate_task itself, which does not currently exist in this codebase, or (b) routine Red Team/governance audits of the log file to catch skipped validations after the fact.

## Workstream 3 — Force-escalate / kill-switch

**Built:** no separate script — the mechanism is inherent to `validate_handoff.py`'s floor logic. Any tier at or above a stage's floor passes; any tier below the floor is hard-rejected. This makes downgrade structurally impossible through the validator, and upward re-declaration always succeeds.

**Tested:** confirmed a `decide` stage re-declared at T2 (escalated from an original lower-tier draft) passes validation; confirmed a `decide` stage declared at T3 (attempted downgrade) is rejected. Both logged.

**Known limitation:** same as Workstream 2 — this is enforced only for agents that actually call the validator (currently: `coder`, pilot only).

## Rollout status

| Agent profile | Hand-off contract wired in? |
|---|---|
| coder | Yes (pilot) |
| architect, orchestrator, researcher, backtester, trading, product-owner, documenter, risk-guardian, red-team | Not yet — pending pilot review before wider rollout, per the phased plan |

## Next steps (deferred, not abandoned — explicit trigger criteria below)

Both items below were deliberately deferred on 2026-07-26 pending evidence, not skipped. User confirmed: revisit when the trigger criteria are met, don't let this go stale.

### #1 — True interceptor in front of delegate_task
**Trigger to build this:** either (a) a real skipped validation shows up — i.e., `coder` delegates a task with no matching entry in `handoff_audit_log.jsonl` around the same time, or (b) user explicitly decides the "voluntary gate" risk is unacceptable regardless of evidence. Absent either, building unskippable orchestration infrastructure is premature complexity for a failure mode that hasn't occurred.
**How to check:** compare `coder`'s actual delegation/cron activity against `handoff_audit_log.jsonl` entry timestamps periodically — a gap is the signal.

### #3 — Roll out hand-off contracts to remaining 7 profiles (architect, orchestrator, researcher, backtester, trading, product-owner, documenter, risk-guardian, red-team)
**Trigger to expand:** `coder` pilot should accumulate a meaningful run of real (non-test) contract validations — a rough bar is 5-10 real entries in `handoff_audit_log.jsonl` spanning at least 1-2 weeks of normal use, with no unexpected floor violations or schema friction. That's the evidence the schema/floors work before multiplying by 8.
**How to check:** read `handoff_audit_log.jsonl`, filter out the 3 test contracts from 2026-07-25 (timestamps `19:17:11.xxx`), count real entries and date range.

**Monitoring:** a weekly cron job (`ADR-005 Rollout Readiness Check`) reviews the audit log against both trigger sets and reports a recommendation — see cron job for details. This does not replace judgment, it just prevents this from going stale across sessions.
