---
id: US-006
type: user-story
epic: EPIC-001
status: in-progress
priority: high
effort: M
created: 2026-07-17
updated: 2026-07-17
assigned_to: orchestrator
tags: [backlog, story, model-routing, infrastructure, automation]
---

# US-006: Implement Model Routing Strategy

## Story
**As a** HermesForge Orchestrator,  
**I want** a defined and enforced model routing strategy that assigns the right LLM tier to each task type,  
**So that** we maximise reasoning quality on high-stakes tasks while minimising cost and latency on routine automation.

## Acceptance Criteria
- [x] AC1: ADR-001 updated with 4-tier routing table, model recommendations, and implementation approach
- [x] AC2: RISK_RULES.md v1.1 includes Section 10 (AI Model Usage Rules) with hard floors for Risk Guardian (AI-001) and trading decisions (AI-002), Tier 4 restrictions (AI-003), and audit requirements (AI-004, AI-005)
- [x] AC3: First T3 automation (CRON-001 Daily Market Intelligence) live and documented in `10-Operations/`
- [x] AC4: ForgeLoop runlog updated with model routing activation entry
- [ ] AC5: `model-router` Hermes skill built with keyword-based task classifier (see US-005 dependency)
- [ ] AC6: All existing cron jobs reviewed and model tier declared explicitly in job config
- [ ] AC7: Weekly routing audit log established in `08-Knowledge/ModelRouter-Log.md`

## Model Routing Reference
| Tier | Model | Use Case |
|---|---|---|
| T1 | `anthropic/claude-opus-4-5` | Architecture decisions, novel strategy design |
| T2 | `anthropic/claude-sonnet-4.6` | Risk Guardian (hard floor), strategy dev, market synthesis, coding |
| T3 | `google/gemini-2.0-flash-001` | Daily automation, ForgeLoop ticks, structured summaries |
| T4 | `google/gemini-2.5-flash` / `meta-llama/llama-3.1-8b` | Triage only — news filtering, alert classification |

**Hard rules (non-negotiable):**
- Risk Guardian: T2 minimum, always
- Trading decisions: T2 minimum
- T4: never feeds trading decisions directly

## Notes / Context
> This story implements the routing strategy accepted in the 2026-07-17 Orchestrator session.
> ADR-001 is the authoritative reference document. RISK_RULES.md Section 10 is the
> enforcement layer. CRON-001 is the first concrete example.
>
> AC5 (model-router skill) depends on US-005 (skill skeleton infra) being complete first.
> AC6 applies to: headroom-daily-stats cron job — currently has no explicit model tier set.

## Dependencies
- **Blocks:** US-005 (model-router skill skeleton needs this routing table as spec input)
- **Blocked by:** Nothing — AC1-AC4 already complete

## Definition of Done
- [x] ADR-001 updated and committed to GitHub
- [x] RISK_RULES.md v1.1 with Section 10 committed
- [x] CRON-001 live with T3 model and documented
- [x] ForgeLoop runlog entry added
- [ ] model-router skill built and loadable (AC5)
- [ ] All cron jobs declare model tier (AC6)
- [ ] Risk Guardian reviewed routing rules (AC1-AC4 complete; AC5-AC7 pending)
