---
type: user-story
epic: EPIC-017
priority: P0
status: backlog
created: 2026-11-02
owner: orchestrator
tags: [cost, routing, tiers]
---

# US-220 — Enforce model-tier routing (fix T3-labeled billing-at-T2 leak)

## Problem

ADR-001's tier routing was never enforced at the profile/cron level. Agents/jobs whose `model` field says `*-flash-0731` (T3) but `provider` is null inherit the global default (`deepseek-v4-pro-0813` = T2) and **bill at 3–5× the intended cost**. Evidence: Auto-Crosspost (`model=flash-0731` but `model_snapshot=v4-pro`), researcher (no `config.yaml` → inherits T2). The `provider_snapshot`/`model_snapshot` fields record what *actually* ran, not the declared model. This is the single largest cost lever (≈3× the ≤$100/mo budget).

## Fix

1. Audit every agent profile + cron job for a declared-tier vs actual-billing mismatch (compare `model`/`provider` vs `model_snapshot`/`provider_snapshot`).
2. Enforce routing: pin T3 agents/jobs to `deepseek/deepseek-v4-flash-0731` + `provider: openrouter`; pin T2 (coder/architect/orchestrator/risk-guardian) to `deepseek-v4-pro-0813`; T4 to the cheap tier. Document the live mapping.
3. Give T3/T4 agent profiles an explicit `config.yaml` model (or equivalent) so they do NOT inherit the T2 default.
4. Report before/after monthly cost.

## Acceptance Criteria

- No T3/T4-labeled agent or job bills at T2 (verified via `model_snapshot`).
- The tier table in ADR-001 is reflected in actual profile/cron pins.
- Before/after monthly cost reported.

## Owner / RACI
- Owner (A): orchestrator · Responsible (R): coder · Consulted (C): product-owner · Informed (I): all swarm agents