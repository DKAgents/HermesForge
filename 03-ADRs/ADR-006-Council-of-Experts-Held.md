---
id: ADR-006
type: decision
status: held
date: 2026-07-26
deciders: [HermesForge Orchestrator, User]
tags: [adr, model-routing, council-of-experts, research, phase3, held]
topic: adrs
confidence: high
has_quotes: true
source: HermesForge ADR
---
# ADR-006: Council of Experts (Research-Only, Held Pending Sign-Off)

## Status
**Held** — 2026-07-26. Drafted for review. Requires (1) a RISK_RULES.md amendment, (2) explicit user sign-off, and (3) a passing smoke-test gate before any implementation begins. Not accepted. Not to be implemented from this draft alone.

## Context

ADR-005 (Phase 1/2) established stage-based model floors and Red Team. This ADR addresses the third and most sensitive piece of the proposed architecture evolution: a "Council of Experts" pattern for research and analysis, using multiple parallel cheap-tier (T3) model calls synthesized by a single Tier 2 step.

This pattern carries real risk if implemented carelessly: an ensemble of T3 outputs can produce false confidence that superficially resembles T2-quality reasoning without meeting the bar RISK_RULES.md Rule AI-002 sets. This ADR exists specifically to close that gap before any code is written, per the 2026-07-26 conversation thread's conclusion that "any multi-model pattern requires an explicit RISK_RULES.md update + ADR + human sign-off before implementation."

---

## Proposed Decision (held, not accepted)

### Scope
Strictly limited to research and analysis paths. Council of Experts may never be invoked on a path that can terminate in a trade entry, exit, or position-sizing decision.

### Pattern
N × T3 parallel perspectives → mandatory T2 `synthesize` stage (per ADR-005 stage vocabulary).

### Enforcement mechanism (required before implementation)
Scope cannot rely on documentation alone. Concrete controls required:
- **Output isolation:** Council of Experts output is written only to a designated research path (e.g. `05-Research/Council/`). Trading/execution code must not read from this path. This is enforced by code review checklist and, where feasible, a lint/CI rule that flags any import or read reference from execution modules into the Council output path.
- **Actor scoping:** Only the `researcher` and `backtester` agents may invoke Council of Experts. `coder`, `architect`, `orchestrator`, `risk-guardian`, and `documenter` are not authorized to invoke this pattern. This closes the gap where any agent could spin up a "Council" as a backdoor around a direct T2 call.
- **T2 rejection authority:** The `synthesize` step is not a summarizer or averager. It must have explicit instruction and authority to reject, heavily revise, or disregard any/all of the N parallel T3 outputs. The synthesis step's output is the actual decision input; the T3 outputs are raw material, not votes. This must be stated in the synthesis step's prompt/instructions, not left implicit.
- **Audit trail:** Every Council invocation declares `stage: synthesize`, `tier: T2` for the final step, and lists all N parallel T3 calls with their individual tier declarations, per the ADR-005 hand-off contract format.

### Smoke-test gate (required before implementation)
Before this ADR can move from held to accepted:
1. Select 3-5 past research questions with a known, already-validated answer (e.g. market-intel questions previously analyzed manually or via single T2 call).
2. Run the Council of Experts pattern (N×T3 → T2 synthesis) against the same questions.
3. Compare Council output quality against the single-Sonnet-call baseline on the same questions.
4. If Council output is not measurably better (or is worse) than the baseline, this ADR should be deprioritized further rather than accepted, regardless of cost savings, since the added latency/complexity is not earning its keep.
Results of this smoke test must be documented in this ADR's Consequences section before acceptance.

---

## Required RISK_RULES.md Amendment (prerequisite, not yet drafted)

RISK_RULES.md Section 10 (AI Model Usage Rules) currently contemplates single-model tiering only. It does not address ensemble/multi-model patterns. Before this ADR can be accepted, a new rule must be added to Section 10, covering at minimum:
- Explicit statement that ensemble outputs (N parallel cheap-model calls) do not, by themselves, satisfy the Tier 2 requirement in Rule AI-002 — only a genuine T2 synthesis/decision step satisfies it.
- Explicit statement that Council of Experts is scoped to research/analysis only, consistent with Rule AI-002's "Tier 3/4 models may assist with data gathering" language.
- Reference to this ADR for the enforcement mechanism (output isolation, actor scoping).

This amendment follows RISK_RULES.md's existing "Rule Change Process": any agent may propose, Risk Guardian reviews and recommends, an ADR documents the change (this one), and the human must explicitly approve before the rules version increments.

## Sign-off Checklist (all required before status changes from held to accepted)

- [ ] RISK_RULES.md Section 10 amendment drafted and reviewed by Risk Guardian
- [ ] Smoke-test gate executed with documented results
- [ ] Output isolation mechanism implemented and verified (not just documented)
- [ ] Actor scoping implemented in delegate_task/cron invocation layer
- [ ] T2 rejection authority explicitly written into the synthesis step's prompt
- [ ] User's explicit written sign-off

## Consequences (to be completed at acceptance time)

**Positive (anticipated):** improved diversity of perspective on research questions; low marginal cost per parallel T3 call.

**Negative/Trade-offs (anticipated):** total cost may exceed a single T2 call if N is large; added latency from parallel calls plus synthesis round-trip; increased system complexity and a new risk surface if enforcement controls are not built correctly.

**Risks:** false confidence from ensemble agreement; scope creep of actor authorization over time; erosion of the "advisory into T2" boundary if the synthesis step is implemented as a summarizer rather than a genuine decision-maker.

*Smoke-test results, final cost/quality comparison, and acceptance decision to be appended here once the sign-off checklist is complete.*

## Review Date
Not applicable while status is held. Upon acceptance, inherit ADR-005's 3-month review cadence.


