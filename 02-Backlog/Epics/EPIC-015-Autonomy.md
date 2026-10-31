---
id: EPIC-015
type: epic
status: backlog
created: 2026-10-31
updated: 2026-10-31
tags: [epic, autonomy, self-healing, orchestrator, detection, digest, t1-escalation]
---

# EPIC-015: Autonomous Self-Healing (ADR-007)

## Goal

Implement ADR-007's operational wiring so the fleet runs itself under the autonomy boundary: a detection loop feeds a shared queue, the Orchestrator self-runs on a cron tick (routing to specialists without human steering), T1 escalates autonomously for non-live triggers, and a confidence digest surfaces auto-fixes + human-gated exceptions. Human involvement shrinks to genuine exceptions only.

## Stories

| Story | Title | Status |
|-------|-------|--------|
| **US-158** | Layer-1 detection loop (system doctor → findings queue) | ⬜ Backlog |
| **US-159** | Forge Loop cron tick (orchestrator self-runs + delegates) | ⬜ Backlog |
| **US-160** | T1 auto-escalation for non-live triggers | ⬜ Backlog |
| **US-161** | Confidence digest (periodic Discord summary) | ⬜ Backlog |
| **US-162** | Human sign-off queue (Tier-2 exceptions, non-blocking) | ⬜ Backlog |
| **US-163** | Python/dependency standardization (fix bare tools-python root cause) | ⬜ Backlog |

## Definition of Done

- [ ] System doctor cron scans (cron errors, data freshness, model/cost drift, disk/SSH, upstream git) and writes findings to a queue.
- [ ] Orchestrator self-runs on a cron tick: reads queue → selects ≤3 → delegates → documents, with no human steering.
- [ ] T1 escalation for non-live triggers (#1–5, #7, #9 of ADR-001) dispatches autonomously + logs; live triggers stay human-gated.
- [ ] Digest posts to Discord: auto-fixed N (listed) · M need sign-off · 0 trading-boundary anomalies.
- [ ] Sign-off queue accumulates Tier-2 items for human review on their own schedule.
- [ ] HermesForge scripts run under a single, dependency-complete Python that survives `hermes update`.
- [ ] Every change path-scoped-committed; boundary enforced by SOUL.md instruction + JSONL audit log (documented, not overclaimed as unskippable).

## Notes

- **Governing ADR:** ADR-007 "Self-Healing System with Trading-Safety Boundary" (finalized 2026-10-31). Rollout order below matches its Sequencing.
- **No hard enforcement:** there is no interceptor in front of `delegate_task` — "autonomous" is enforced by SOUL.md instruction + audit trail, not a code gate. Document this; do not overclaim.
- **Rollout order (eyes before hands):** Phase 1 = US-158 + US-161 (detection + digest, no auto-fix). Phase 2 = US-159 + US-162 (auto-fix non-live). Phase 3 = US-160 (T1 escalation). US-163 is an infra prerequisite for reliability.
- **US-163 root cause (found 2026-10-31):** cron `.sh` wrappers resolve bare `python3` to the bare tools Python (`/root/.hermes/tools/python-3.14.x`), which lacks third-party deps — this caused the `discover_connections` yaml failure and the Daily Signal Scanner mplfinance failures. `hermes update` re-stages this interpreter, wiping manual installs.