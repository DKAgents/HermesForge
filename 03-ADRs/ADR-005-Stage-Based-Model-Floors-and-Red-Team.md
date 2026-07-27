---
id: ADR-005
type: decision
status: accepted
date: 2026-07-26
deciders: [HermesForge Orchestrator, User]
tags: [adr, model-routing, sdlc, red-team]
topic: adrs
confidence: high
has_quotes: true
source: HermesForge ADR
---
# ADR-005: Stage-Based Model Floors and Red Team Review

## Status
**Accepted** — 2026-07-26. User approved via "OK, let's proceed with your recommendation, then." Supersedes nothing; extends ADR-001.

## Context

ADR-001 established a 4-tier model taxonomy and agent-level routing rules. In practice, individual agents perform work spanning multiple complexity levels within a single task (e.g. the coder agent both scaffolds boilerplate and makes irreversible design calls). ADR-001's own Design Principle #2 states routing should follow task complexity, not agent identity, but no mechanism currently enforces this at the stage level.

Separately, no adversarial review layer exists today. Strategies, code, and prompts are reviewed by the same agents that produced them, with Risk Guardian as the only independent check, and only for capital-facing decisions.

This ADR formalizes two additions building on the critique-and-revision process documented in the 2026-07-26 conversation thread: (1) explicit per-stage model floors within existing SDLC roles, and (2) a Red Team agent for adversarial review, advisory-only.

---

## Decision — Part A: Stage-Based Model Floors (Phase 1)

### Roles retained
BA/Product Owner, Architect, Coder, QA/Reviewer, Documenter, Orchestrator — unchanged from ADR-001's agent roster. This ADR does not add or remove agents; it adds stage granularity within their existing work.

### Stage vocabulary

| Stage | Tier | Purpose |
|---|---|---|
| `explore` | T3/T4 | Open-ended investigation, option generation, no commitment |
| `draft` | T3/T4 | First-pass content/code, expected to be revised |
| `boilerplate` | T3/T4 | Mechanical scaffolding, templates, repetitive structure |
| `test-gen` | T3/T4 | Test case generation from existing spec/code |
| `decide` | **T2 hard floor** | Risk Guardian and strategy-affecting decisions |
| `synthesize` | **T2 hard floor** | Combining multiple inputs (including Council of Experts outputs, see ADR-006) into a single authoritative output |
| `commit` | **T2 hard floor** | Architecture ADRs, code merges to main, irreversible or hard-to-reverse actions |

Rationale for three T2 stage names instead of one generic "critical" tier: `decide`, `synthesize`, and `commit` map 1:1 onto the three real T2 use cases in this system (risk/strategy decisions, multi-source synthesis, architecture/code finalization). A single catch-all name invites ambiguity about which use case applies.

### Hand-off contract

Every stage declaration in a `delegate_task` or cron job call must include:

```yaml
stage: <name>          # one of the vocabulary above
tier: <T2|T3|T4>        # explicit, no inference
consumes: <description of inputs read>
produces: <description of outputs written, and where>
downstream_allowed: <list of stages/paths permitted to consume this output>
```

This satisfies RISK_RULES.md Rule AI-004 (Audit Trail): tier is declared, not inferred, for every task. No complexity classifier is introduced — routing remains explicit per ADR-001 Phase 1 implementation approach.

### Force-escalate / kill-switch

Any agent or human may re-declare a task's stage to a higher tier at any time if the original stage assignment is judged incorrect (e.g. a `boilerplate`-tagged task turns out to touch a risk-adjacent decision). Escalation is always upward only — no mechanism exists to downgrade a T2 hard-floor stage, consistent with RISK_RULES.md Rule AI-001/AI-002.

---

## Decision — Part B: Red Team (Phase 2)

### Role
A new advisory agent, `red-team`, tasked with adversarial review of strategies, code, risk analysis, and prompts. Default tier: T3 (`deepseek-v4-flash`), consistent with ADR-001's tiering for non-decision-making work.

### Constraints
- **Advisory only.** Red Team output is a finding, never a decision, veto, or sign-off.
- **Routes through Risk Guardian.** All Red Team findings that touch risk or capital must be forwarded to Risk Guardian, which retains sole veto authority per RISK_RULES.md Rule Hierarchy (Section "Rule Hierarchy": Human override > Risk Guardian veto > written rules > agent judgment).
- **Red Team findings are never treated as equivalent to Risk Guardian sign-off**, regardless of how thorough or confident the finding is. This is an explicit non-negotiable in this ADR to prevent scope creep of the role over time.
- Escalation to T2 for Red Team's own synthesis/reporting step is permitted if a finding is complex enough to warrant it, using the `synthesize` stage from Part A.

---

## Compliance with RISK_RULES.md

- **Rule AI-001 (Risk Guardian hard floor):** Unaffected. Risk Guardian remains T2 hard floor at all times; this ADR adds no exception.
- **Rule AI-002 (Strategy decisions require T2):** Unaffected. `decide` stage is T2 hard floor by construction.
- **Rule AI-003 (Tier 4 restriction):** Unaffected. T4 remains restricted to `explore`/`draft`/`boilerplate`/`test-gen` low-stakes stages only, never feeding directly into `decide`/`synthesize`/`commit`.
- **Rule AI-004 (Audit trail):** Strengthened. Every stage now declares tier explicitly via the hand-off contract, closing a gap that existed at the agent level in ADR-001.
- **Rule AI-005 (Escalation):** Directly implemented via the force-escalate/kill-switch clause in Part A.

No amendment to RISK_RULES.md is required for this ADR. It operationalizes existing rules; it does not change them.

---

## Consequences

**Positive:**
- Closes the audit-trail gap ADR-001 left at the agent-granularity level.
- Red Team adds adversarial review at near-zero marginal cost (T3).
- Explicit hand-off contracts make routing decisions inspectable after the fact, not just at declaration time.

**Negative/Trade-offs:**
- More declarations required per task (stage, tier, consumes, produces, downstream_allowed) — modest overhead, offset by clearer audit trail.
- Red Team adds a review pass, increasing latency on paths that use it. Acceptable for non-time-sensitive review, not for time-sensitive market signal paths.

**Risks:**
- Stage mis-declaration (e.g. tagging a real decision as `boilerplate`) is the primary risk. Mitigated by the force-escalate clause and by Rule AI-004 making every declaration visible for review.
- Red Team findings being informally treated as sign-off over time. Mitigated by the explicit non-negotiable stated in Part B.

## Review Date
2026-10-26 (3 months) — review alongside ADR-001's scheduled review. Evaluate: stage mis-declaration incidents (target: zero), Red Team finding volume and quality, whether Council of Experts (ADR-006) is ready to move from held to accepted status.

