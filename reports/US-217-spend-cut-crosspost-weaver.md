---
type: report
story: US-217
epic: EPIC-017
title: Cut Auto-Crosspost + Vault Weaver spend >=50%
created: 2026-11-02
owner: orchestrator
tags: [cost, model-routing, cron, reconciliation]
---

# US-217 — Cut Auto-Crosspost + Vault Connection Weaver spend >=50%

## Root cause (confirmed against /root/.hermes/cron/usage_audit.jsonl)

Two top spend-cron items were measured over the trailing 30 days:

| Job | id | Runs/30d | Prompt tok | Compl tok | Model actually used | Est. $/30d |
|---|---|---|---|---|---|---|
| Auto-Crosspost Daily Briefing | 356f3c4fb973 | 21 | 10.92M | 0.20M | `deepseek-v4-pro` x20, `flash-0731` x1 | ~$7.61 (vs $7.71 baseline) |
| Vault Connection Weaver | 98edbe73d115 | 178 | 30.12M | 0.89M | `flash` x157, `flash-0731` x21 | ~$3.83 (vs $4.63 baseline) |

**Systemic tier-routing discrepancy (the key finding).** The Auto-Crosspost job
declared `model: deepseek/deepseek-v4-flash-0731` (T3) but had `provider: null`.
With no explicit provider pin, the cron worker ignored the model field and fell
back to the global default model — `deepseek/deepseek-v4-pro` (T2) — hence the
`model_snapshot: deepseek/deepseek-v4-pro`. 20 of the last 21 runs billed at T2
pro (~8x the intended T3 flash price). This is one instance of a broader class:
any job/agent labeled T3 whose provider pin is null silently bills at T2.

## Changes applied

1. **Auto-Crosspost provider pin fixed** — `hermes cron edit 356f3c4fb973 --model deepseek/deepseek-v4-flash-0731 --provider openrouter`. The job now explicitly pins the model to flash-0731 on openrouter (T3), matching its intent.

2. **Vault Connection Weaver frequency halved** — `hermes cron edit 98edbe73d115 --schedule "every 480m"` (was every 240m). Same per-run token volume, half the runs/month.

## Cost delta (before -> after, per 30d)

Pricing (ADR-001, 2026-10-29): T2 `deepseek-v4-pro-0813` $0.66/$1.98 per 1M in/out; T3 `deepseek-v4-flash-0731` $0.12/$0.24 per 1M in/out.

| Job | Before | After | Delta |
|---|---|---|---|
| Auto-Crosspost (T2->T3) | $7.71 | ~$1.36 | -82% |
| Vault Weaver (cadence /2) | $4.63 | ~$2.32 | -50% |
| **Combined** | **$12.34** | **~$3.68** | **-70%** |

- Auto-Crosspost "after" is computed from the measured trailing-30d token volume
  (10.92M in / 0.20M out) at flash pricing — not an invented number.
- Weaver "after" is exactly half of the baseline, since cadence is the only change.

Combined spend drops **~70%**, comfortably below the >=50% acceptance bar.
Publishing output is unchanged: the crosspost still runs Mon-Fri 13:05 (now on the
intended T3 tier) and the weaver still produces wikilinks, just at 8h cadence.

## Follow-ups (do not expand scope here)

- Systemic: audit every cron job/agent whose `model` field starts with `*-flash-0731`
  (T3) but whose `provider` is null — the provider pin is missing and it bills T2.
  Candidate for a separate story, not part of US-217.
- The `provider_snapshot`/`model_snapshot` on 356f3c4fb973 still show the pre-fix
  values until its next run (Mon 13:05); they are snapshots of the last execution,
  not live config.