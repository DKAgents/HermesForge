---
id: US-141
epic: EPIC-014
type: story
status: story-ready
created: 2026-09-07
priority: P3
tags: [backlog, story, efficiency, swarm-diet, profiles, train-4]
campaign: 2026-09-aegis-rebuild
train: 4
owner_profile: product-owner
model_floor: T2
points: 3
depends_on: US-139
---

# US-141 — Swarm diet: documenter→skill, trading/consulting as surfaces (evidence-gated)

- **Train:** 4
- **Priority:** P3
- **Owner profile:** product-owner (with architect review)
- **Model floor:** T2 (structural change to the profile fleet)
- **Status:** story-ready
- **Campaign:** 2026-09-aegis-rebuild

## Story

As the operator, I need the standing-profile count reduced to only those that
carry real, distinct judgment authority, so that the 8 GB VPS is not paying
soul/context overhead for profiles that are either surfaces or fold into a
skill — without ever collapsing the two governance monopolies.

## Background

Evidence from campaign `2026-09-aegis-rebuild` (second pass, 2026-09-07 UTC):

- FACT (standing): `inventory.yaml` marks **only `orchestrator` as `hot`**
  ("active in every user session"). Every other swarm profile is `on-demand`
  or `campaign-only`. So the *runtime* fleet is already thin — the diet is
  about definition/soul overhead and role clarity, not hot-loop RAM.
- FACT (souls): smallest souls are `trading` (513 B) and `consulting` (513 B),
  both tagged in inventory as "surface, not judgment loop." `documenter`
  (1,404 B) is tagged "may become coder skill after inventory." `red-team`
  (2,139 B) is tagged "may become periodic, not standing."
- FACT (monopolies): `publisher` and `risk-guardian` carry
  `monopoly: true` — governance invariant, **never collapse** (echoed in
  `DO-NOT-TOUCH.md`).
- INFERENCE: the campaign can now issue evidence-backed verdicts, but the
  measured per-profile `/context` (US-139) is needed before an actual profile
  is retired — collapsing a profile without knowing its context footprint is
  guessing at the saving.

### Profile verdicts (Phase A / Phase F, second pass)

| Profile | Standing | Verdict | Basis |
|---------|----------|---------|-------|
| orchestrator | hot | KEEP | only hot profile; coordinates the loop |
| publisher | on-demand | KEEP (monopoly) | owns 9 publish files — never collapse |
| risk-guardian | on-demand | KEEP (monopoly) | owns 1% cap — never collapse |
| coder, architect | on-demand | KEEP | T2 code-change floor |
| backtester, researcher | on-demand | KEEP | distinct validation/discovery judgment |
| product-owner | on-demand | KEEP | backlog authority (this story's owner) |
| red-team | on-demand | THIN | make explicitly periodic/on-demand, not standing |
| documenter | on-demand | REPLACE→skill | fold vault-graph upkeep into a coder/on-demand skill |
| trading | on-demand | THIN (surface) | 513 B surface; keep as entry surface, no judgment authority |
| consulting | on-demand | THIN (surface) | 513 B surface; same |
| aegis-auditor | campaign-only | KEEP | this campaign's runner (T1, invoked only) |

No profile is marked hard-DELETE in this pass: the two smallest (trading,
consulting) are user-facing *surfaces* worth keeping as thin entry points, and
documenter's retirement is conditional on the skill replacement existing first.
Every verdict names its disposition; none collapses a monopoly.

## Acceptance

- [ ] Per-profile `/context` bytes available (US-139) so each retirement states
      its measured saving before it is applied.
- [ ] `documenter` → replacement plan: a documenter *skill* loaded on demand by
      coder/orchestrator; the standing profile retired only after the skill is
      proven on one vault-maintenance cycle.
- [ ] `red-team` reclassified explicitly periodic/on-demand (no standing hot
      state), decision recorded.
- [ ] `trading` / `consulting` confirmed as surfaces with no exit/persist/
      publish authority; souls kept minimal.
- [ ] `publisher` and `risk-guardian` untouched (monopoly assertion re-stated in
      the change record).
- [ ] Each applied change names its rollback.

## Forbidden

- No live-soul edits by Aegis (this story hands soul/profile changes to
  product-owner + architect; Aegis only files the verdicts)
- Never collapse publisher or risk-guardian
- No publisher-file edits
- No truncate/replace of history files
- No credentials in output

## Rollback

Profile definitions are recreatable from git history and
`.curator_backups/`. Retire profiles one at a time, each behind its own commit,
so any single retirement is independently revertible. Surfaces (trading,
consulting) are not retired in this story.
