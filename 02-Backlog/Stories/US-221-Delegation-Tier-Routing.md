---
type: user-story
epic: EPIC-017
priority: P1
status: backlog
created: 2026-11-02
owner: architect
tags: [cost, routing, delegation]
---

# US-221 — Route delegate_task subagents by profile tier

## Problem

US-220's config.yaml tier pins fix DIRECT profile dispatch (`HERMES_PROFILE=… hermes chat`), but `delegate_task` bills by the PARENT model, not the target profile. Subagents spawned via `delegate_task` therefore inherit the orchestrator's T2 model regardless of role, bypassing the tier routing — a continuing cost leak on the path used for heavy parallel research.

## Fix (ADR-level)

Configure the advanced-delegation backend — `delegation.backends.profile_routes` (map each role → its Hermes profile, so subagents run AS the profile and adopt its `config.yaml` model) or `model_map` — honoring ADR-001:

- T2 floor (never downgraded): coder, architect, orchestrator, risk-guardian → `deepseek-v4-pro-0813`.
- T3: researcher, backtester, trading, product-owner, publisher, red-team → `deepseek-v4-flash-0731`.
- T4: documenter → cheap tier.

A misconfigured route must NOT silently downgrade a T2-floor agent (fail-safe; verify the effective model per role after config).

## Acceptance Criteria

- A `delegate_task` dispatch bills at the target profile's tier (verified via `model_snapshot`/`provider_snapshot`).
- T2-floor agents are never downgraded (explicitly asserted).
- Before/after monthly cost reported.

## Owner / RACI
- Owner (A): architect · Responsible (R): coder · Consulted (C): risk-guardian · Informed (I): orchestrator