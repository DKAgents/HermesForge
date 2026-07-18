---
id: US-007
type: user-story
epic: EPIC-001
status: in-progress
priority: high
effort: M
created: 2026-07-17
updated: 2026-07-17
assigned_to: orchestrator
tags: [backlog, story, model-routing, market-intelligence, automation, T3]
---

# US-007: Implement Initial Model Routing & Daily Market Intelligence

## Story
**As a** HermesForge Orchestrator,  
**I want** a working 4-tier model routing policy enforced in risk rules and demonstrated through live T3 automation,  
**So that** we use the right model for each task type, protect risk-sensitive decisions with hard model floors, and reduce cost on routine daily automation.

## Acceptance Criteria
- [x] AC1: 4-tier model strategy accepted and documented in ADR-001 (T1=opus-4-5, T2=sonnet-4.6, T3=gemini-2.0-flash-001, T4=gemini-2.5-flash/llama-3.1-8b)
- [x] AC2: RISK_RULES.md Section 10 (AI-001–AI-005) added — Risk Guardian hard floor at T2, Tier 4 restrictions, audit requirements
- [x] AC3: `Headroom Daily Savings Report` cron job (`ad0e12500771`) updated with explicit T3 model — AI-004 compliance fixed
- [x] AC4: `CRON-001-Market-Intelligence` (`79c465c541f2`) live on T3, running Mon–Fri 9am ET, writing to `05-Research/Market-Intelligence/`
- [x] AC5: ForgeLoop runlog entry 2026-07-17 documents routing activation and T3 job creation
- [ ] AC6: All remaining cron jobs reviewed for AI-004 compliance (explicit model tier declared)
- [ ] AC7: ModelRouter skill built (deferred — do after more working T3 examples exist)

## Model Routing Summary
| Tier | Model | Jobs Using It |
|---|---|---|
| T2 | `anthropic/claude-sonnet-4.6` | Global Hermes default; Risk Guardian hard floor |
| T3 | `google/gemini-2.0-flash-001` | `CRON-001-Market-Intelligence`, `Headroom Daily Savings Report` |
| T4 | `google/gemini-2.5-flash` / `meta-llama/llama-3.1-8b` | Reserved — triage tasks only, not yet deployed |

## Tier 4 Constraint (Non-Negotiable)
Per **RISK_RULES.md AI-003**: Tier 4 must never feed into trading decisions, risk analysis,
or strategy development. Approved uses: news headline filtering, alert classification,
watchlist keyword scanning, template population. All other tasks: T3 minimum.

## Notes / Context
> This story captures the full model routing bootstrap as accepted in the 2026-07-17
> session. It supersedes the partial tracking in US-006 for the routing-specific work.
> The ModelRouter skill (AC7) is intentionally deferred — we want 3–5 working T3 examples
> first so the routing rules emerge from real usage patterns rather than speculation.
>
> Existing cron jobs `LinkedIn Post Generator` (98a07007974b) and
> `X Post Generator for DXFoundation` (1509fc837a11) still have `model: null` —
> these are content generation jobs (not trading-related) and should be assigned T3
> as a follow-up AC6 action.

## Dependencies
- **Blocks:** US-005 (model-router skill — needs this routing spec as input)
- **Blocked by:** Nothing

## Definition of Done
- [x] ADR-001 updated and committed to GitHub
- [x] RISK_RULES.md v1.1 committed with Section 10
- [x] CRON-001-Market-Intelligence running on T3
- [x] Headroom stats job fixed to T3 (AI-004 compliant)
- [x] ForgeLoop runlog updated
- [ ] Remaining cron jobs (LinkedIn, X Post) assigned explicit model tiers
- [ ] Risk Guardian sign-off on AI model rules (Section 10) — pending live trading phase
