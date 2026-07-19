---
id: US-063
epic: EPIC-001
type: story
status: backlog
created: 2026-07-20
points: 3
tags: [agents, soul, activation, profiles]
---

# US-063: Activate Thin Agent Profiles (risk-guardian, product-owner, documenter)

## Story
As a platform operator, I want the risk-guardian, product-owner, and documenter agent profiles to have fully defined SOUL.md identities (not just model routing guidance), so that these agents behave predictably when delegated work instead of falling back on generic default behavior.

## Context
During the 2026-07-20 model routing update (ADR-001), model tier guidance was added to all agent profiles. Three profiles were found to have only a bare `## Identity` header with no real role definition:

| Profile | Current State | Gap |
|---|---|---|
| `risk-guardian` | Model routing only (T2 hard floor) | No defined risk rules, escalation criteria, position sizing authority, or veto conditions |
| `product-owner` | Model routing only (T3 default) | No defined backlog grooming process, story-writing standards, or prioritization framework |
| `documenter` | Model routing only (T4) | No defined documentation standards, output locations, or scope boundaries |

Compare to `architect`, `coder`, `backtester`, `researcher`, and `orchestrator` — all of which have full Identity, Core Responsibilities, Hard Rules, and Output Format sections already.

## Acceptance Criteria
- [ ] `risk-guardian/SOUL.md` — full identity defined:
  - Core responsibilities: position sizing review, incident escalation, risk rule enforcement
  - Hard rules: references `07-Risk/RISK_RULES.md`, `07-Risk/POSITION_SIZING.md`, `07-Risk/ESCALATION_CRITERIA.md`
  - Veto authority: can block a strategy from Active status if risk criteria unmet
  - Output format: risk assessments logged to `07-Risk/GUARDIAN_DECISIONS.md`
- [ ] `product-owner/SOUL.md` — full identity defined:
  - Core responsibilities: backlog grooming, story writing, sprint prioritization
  - Hard rules: every story needs acceptance criteria before entering a sprint; references `02-Backlog/BACKLOG_INDEX.md`
  - Output format: story files follow existing US-XXX template pattern
- [ ] `documenter/SOUL.md` — full identity defined:
  - Core responsibilities: README maintenance, docstring quality, ADR formatting consistency
  - Hard rules: never makes architectural decisions, only documents existing ones
  - Output format: scope boundaries (what documenter touches vs. what it doesn't)
- [ ] All three retain their existing Model Routing section (added 2026-07-20) unchanged
- [ ] Follow the same structural pattern as `architect/SOUL.md` (Identity → Core Responsibilities → Hard Rules → Output Format)

## Definition of Done
- All three SOUL.md files have complete identity definitions
- Structurally consistent with the other 5 fully-defined profiles
- Committed to main (profiles are outside the git-tracked vault — confirm correct location, likely `~/.hermes/profiles/<name>/SOUL.md` which is NOT in the HermesForge git repo; note this in the story if so)

## Notes
Profile SOUL.md files live at `~/.hermes/profiles/<name>/SOUL.md` on the VPS — these are NOT part of the HermesForge git repository. This story's deliverable lives outside version control unless a decision is made to mirror profile configs into the vault for tracking purposes (worth raising as a follow-up question when this story is picked up).
