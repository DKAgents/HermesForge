---
id: ADR-002
type: adr
status: proposed
created: 2026-10-29
deciders: [human]
tags: [adr, self-healing, autonomy, trading-safety, risk-ladder, aegis]
topic: adrs
confidence: medium
---

# ADR-002: Self-Healing System with Trading-Safety Boundary

## Context

HermesForge is moving from a manually-maintained system toward one that
self-identifies issues and optimizations, applies routine fixes automatically,
and keeps a strong reasoning model (Aegis) for the highest-consequence work —
including server operations. In parallel, the trading pipeline is about to take
real money, which imposes a hard safety boundary no automation may cross.

This ADR defines the architecture and the risk ladder that lets the system run
itself while keeping human involvement limited to genuine exceptions.

## Decision

A four-layer loop, gated by a risk ladder. The strong reasoning model is
`deepseek-v4-pro-0813` (T2); the Aegis roof is `anthropic/claude-opus-4.8` (T1),
used only where T1-grade reasoning earns its cost.

### Layer 1 — Detection (fully automatic)

A standing "system doctor" continuously scans: cron output and error logs, data
freshness (DXY/yields/macro), model staleness, cost drift against the
~$5–8/month cap, disk/SSH/security posture, and the Hermes upstream git. Each
finding is classified *issue* vs *optimization* and assigned a risk tier.

### Layer 2 — Fix (tiered autonomy)

- **Tier 0 — auto-apply, no approval:** dependency installs, data refresh,
  stale config/path/date fixes, disk/journal cleanup, model point-release bumps.
  (Example: all fixes performed 2026-10-29.)
- **Tier 1 — auto via swarm, sandboxed + tested + committed:** reversible code
  fixes with a green test gate and rollback path. Routes orchestrator → coder,
  then verified before merge.
- **Tier 2 — human sign-off, never auto:** trading logic, position sizing,
  secrets, exchange/broker API, or anything touching live money.

### Layer 3 — Trading pipeline (hard boundary, read-only to the loop)

Before real money, the pipeline must be fail-closed and paper-first:
- Fail-closed everywhere — no silent data loss, no silent skip.
- Full paper-trading shadow run against live before any real fill.
- The 8-gate gauntlet + risk-guardian + hard 1% positional cap + broker-side
  rejects remain the permanent floor (ADR-001 / PROP-001 / RISK_RULES).
- These rules NEVER auto-change. The loop may only *propose* changes to this
  layer, never apply them.

### Layer 4 — Aegis (server ops + governance + updates)

Aegis (Opus) owns: server administration (systemd/PATH, sshd hardening,
disk/journal hygiene, dependency management, security patches), governance
(ADR drafting, RCA/post-mortem), and Hermes update management. Same player as
the existing `aegis-auditor` profile, mandate broadened.

### Human involvement — the confidence digest

The entire loop collapses to a periodic digest: "auto-fixed N things (listed);
M things need sign-off (why + what happens if deferred); 0 anomalies in the
trading boundary." The human approves the rare Tier-2 exception and nothing else.

## Sequencing

1. **Phase 0** — trading-pipeline hardening audit against the real-money bar.
2. **Phase 1** — detection loop (system doctor).
3. **Phase 2** — Tier 0/1 auto-fix with commit + verify.
4. **Phase 3** — Aegis server-ops mandate + Hermes update manager.
5. **Phase 4** — confidence digest.

## Consequences

- Positive: routine maintenance stops consuming human time; risk is bounded by
  an explicit ladder; trading safety is a hard, non-negotiable boundary.
- Negative: autonomy requires the detection loop to be trustworthy (silent
  false-clean findings are the main risk — mitigated by the digest surfacing
  what was *not* inspected).
- Risks: over-automation of a Tier-2 item. Mitigated by the approval ladder and
  the fact that the trading boundary is read-only to automation.