---
type: token-ram-budget
campaign: 2026-09-aegis-rebuild
status: GRADED
pass: 2
generated_utc: 2026-09-07
display_tz: America/Los_Angeles
supersedes: pass-1 (DEGRADED)
---

# Token / RAM / Context Budget (Pass 2, GRADED)

`cost-30d.md` and `inventory.yaml` now supply measured-basis figures and cron
shapes. `context-budgets.md` is still "TODO", so per-profile *token
composition* (tool-schema vs skill vs soul bytes) remains inferential until
US-139. Cron cost/mode and RAM/disk below are FACT.

## LLM cost (FACT — cost-30d.md)

| Tier | Model | $/mo |
|------|-------|------|
| T1 | claude-opus-4.8 | $0.00 (never used outside this campaign) |
| T2 | deepseek-v4-pro | $1.54 (weaver $1.18 + orchestrator ~$0.36) |
| T3 | deepseek-v4-flash | $0.27 (all other agent crons) |
| **Total** | | **~$1.81/mo** |

**The weaver alone is $1.18/mo = 65% of LLM cron spend and 77% of T2 spend.**
It is the only T2 cron. Cost is not the fleet's constraint, but the weaver is
the one line item where a tier/cadence change is materially the whole budget.

## Per-cron classification (FACT: mode + model from jobs.json)

| Cron | Schedule | Mode | Model | $/30d | Verdict |
|------|----------|------|-------|-------|---------|
| STR-Q Sweep `b9fb0af` | */5 | no-agent | — | ~0 | KEEP |
| Webhook Crosspost `61cccd` | */5 | no-agent | — | ~0 | KEEP |
| Cron Watchdog `65dfc5` | */15 | no-agent | — | ~0 | KEEP |
| Signal→Publisher `3f49a0` | 45 14 * * * | no-agent | — | ~0 | KEEP |
| Paper Capture `4b178ec` | 50 14 * * * | no-agent | — | ~0 | KEEP |
| Git Push `df2caa` | 3am | no-agent | — | ~0 | KEEP |
| Journal Snapshot `291708a` | 3am | no-agent | — | ~0 | KEEP (US-126) |
| Restore Drill `dfa4ab0` | Sun 8am | no-agent | — | ~0 | KEEP — verify it runs (US-137) |
| F&G Fetch `e3c306f` | 11am | no-agent | — | ~0 | KEEP (US-128) |
| **Weaver `98edbe`** | every 240m | **agent** | **deepseek-v4-pro (T2)** | **$1.18** | **THIN → US-138** (toolsets=None, 0 recent writes) |
| Trade Monitor `d1e07c` | 60m | T3 | flash | $0.17 | KEEP |
| Market Intel `79c465` | 0 13 * * 1-5 | T3 | flash | $0.02 | KEEP |
| Connection Discovery `232975` | 0 4 * * * | T3 | flash (toolsets=`['terminal']`) | $0.01 | KEEP — good allowlist example |
| External Edge `e214a9` | Tu/Th/Su 16 | T3 | flash | $0.01 | KEEP |
| Strategy Pipeline `2d8dff` | Tu/Th/Su 17 | T3 | flash | $0.01 | KEEP + seeder (US-127) |
| Perf Report `cb22b0` | 0 13 * * * | T3 | flash | $0.01 | KEEP (no-agent-gather candidate; saving negligible) |
| Vault Maintenance `9d77b5` | 0 2 * * * | T3 | flash | $0.01 | KEEP (retention fixed US-133) |
| LinkedIn `98a07` | Tu/Th 5:30 | T3 | flash | $0.01 | KEEP |
| Weekly Research `9202661` | Su 12 | T3 | flash | ~0 | KEEP (notepad/continuity allowed here) |
| Model Review `07149d` | Mon 9 | T3 | flash | ~0 | KEEP |
| ADR-005 Readiness `a76bfb` | Mon 14 | T3 | flash | ~0 | KEEP |
| STR-Q Re-eval `23471` | Mon 9 | T3 | flash | ~0 | KEEP — US-121 gate, do not touch |

Paused: `356f3c` (Auto-Crosspost, US-130). Completed: `2b4f6f` (US-120 reminder).

## Toolset allowlist finding (FACT)

- Weaver `98edbe`: `enabled_toolsets = None` → inherits all. **Violates** Phase-D
  "no `all`" rule. → US-138.
- Connection Discovery `232975`: `enabled_toolsets = ['terminal']` — correct
  pattern; use as the template for the weaver and any others found once US-139
  enumerates per-profile/per-cron toolsets.

## Per-profile budget (soul bytes FACT; /context INFERENCE pending US-139)

| Profile | Soul B | Model floor | Standing | /context |
|---------|--------|-------------|----------|----------|
| orchestrator | 3,425 | T2 | hot | pending US-139 |
| red-team | 2,139 | T2 | on-demand | pending |
| coder | 2,834 | T2 | on-demand | pending |
| publisher | 2,740 | T2 | on-demand (monopoly) | pending |
| risk-guardian | 1,507 | T2 | on-demand (monopoly) | pending |
| backtester | 1,476 | T2 | on-demand | pending |
| researcher | 1,422 | T2/T3 | on-demand | pending |
| documenter | 1,404 | T3 | on-demand (→skill, US-141) | pending |
| product-owner | 1,573 | T3 | on-demand | pending |
| architect | 1,270 | T2 | on-demand | pending |
| trading | 513 | T3 | on-demand (surface) | pending |
| consulting | 513 | T3 | on-demand (surface) | pending |
| aegis-auditor | 556 | T1 | campaign-only | pending |

Souls are already small (all < 3.5 KB; well under the 80–120-line ceiling). The
soul-diet lever is nearly spent; the real Phase-D levers are the weaver
tier/toolset (US-138) and enumerating toolset allowlists once US-139 lands.

## RAM / disk (FACT)

- RAM: `free -h` → 7.7 Gi total, 3.0 Gi used, **4.8 Gi available**, 189 Mi swap.
  Only orchestrator is hot; agent crons are short-lived and staggered. No RAM
  pressure and no mega-merge proposed (protocol forbids it on 8 GB).
- Disk: 49 G / 240 G (22%). Largest dir `signal_charts` 826 MB / 8,497 files
  with a weekend purge gap → US-140 (P3 — no disk pressure, >10-yr runway).

## Structural targets (unchanged, now evidence-anchored)

- Weaver: apply toolset allowlist now; decide tier/cadence on the 10-run quality
  test (US-138).
- Toolset allowlists for every agent profile/cron once US-139 enumerates them.
- No-agent stays the floor for mechanical work (already 10/22).
- Do not merge crons; do not collapse publisher/risk-guardian.
