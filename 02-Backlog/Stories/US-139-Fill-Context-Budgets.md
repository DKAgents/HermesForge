---
id: US-139
epic: EPIC-014
type: story
status: story-ready
created: 2026-09-07
priority: P2
tags: [backlog, story, brief-builder, context-budgets, efficiency, no-agent]
campaign: 2026-09-aegis-rebuild
train: 1
owner_profile: no-agent
model_floor: no-agent
points: 1
depends_on: US-124
---

# US-139 — Fill context-budgets.md (the one remaining stub brief file)

- **Train:** 1
- **Priority:** P2
- **Owner profile:** no-agent
- **Model floor:** no-agent
- **Status:** story-ready
- **Campaign:** 2026-09-aegis-rebuild

## Story

As the campaign, I need real `/context` breakdowns for the hot profiles so that
Phase-D efficiency verdicts (toolset trims, soul-size cuts, no-agent
migrations) rest on measured token composition rather than structural inference.

## Background

Evidence from campaign `2026-09-aegis-rebuild` (second pass, 2026-09-07 UTC):

- FACT: US-124 delivered a complete `inventory.yaml` (13 profiles, 24 crons,
  channels, data roots, disk) and a complete `cost-30d.md`.
- FACT: `context-budgets.md` is **still a stub — literally "TODO"** (2 lines).
  It is the only required brief file that remains unfilled.
- INFERENCE: with soul sizes now known from `inventory.yaml`, the missing piece
  is the per-profile `/context` composition (tool-schema bytes, always-loaded
  skill bytes, memory/notepad footprint). Without it, Phase-D toolset-trim and
  soul-diet claims stay inferential.

This story is scoped narrowly: fill the last brief stub. It does not re-do
US-124.

## Acceptance

- [ ] `/context` dumps captured for the hot/representative profiles:
      orchestrator, researcher, trade monitor, weaver, strategy pipeline
      (as the brief template lists).
- [ ] For each: total context bytes, tool-schema share, always-loaded skill
      share, soul share, memory/continuity/notepad on|off.
- [ ] `context-budgets.md` replaces the "TODO" stub with this table. No API keys
      or credential material.
- [ ] Findings cross-referenced into a future `TOKEN-RAM-BUDGET.md` refresh so
      toolset-trim stories can cite measured bytes.

## Forbidden

- No live-soul edits
- No publisher-file edits
- No truncate/replace of history files
- No credentials in output

## Rollback

Brief file only; revert to the prior stub if a capture is malformed. No runtime
or data effect.
