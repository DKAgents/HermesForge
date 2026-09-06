---
type: token-ram-budget
campaign: 2026-09-aegis-rebuild
status: DEGRADED
generated_utc: 2026-09-06
display_tz: America/Los_Angeles
---

# Token / RAM / Context Budget (DEGRADED)

**No measured data.** `context-budgets.md` and `cost-30d.md` in the brief are
both "TODO." There are no `/context` dumps and no $/token-by-job figures.
Everything below is STRUCTURAL INFERENCE from the cron/profile inventory in
`hermes-version.md`. Do not treat any number as measured. US-124 builds the real
data; no Train-1 efficiency cut is sequenced until then.

## Per-cron classification (FACT: mode; INFERENCE: cost)

| Cron | Schedule | Mode | Model tier | $/run | Note |
|------|----------|------|-----------|-------|------|
| Paper Trading Capture `4b178ec` | 50 14 * * * | no-agent | — | ~0 | mechanical |
| STR-Q Sweep `b9fb0af` | */5 | no-agent | — | ~0 | high frequency, script only |
| Daily Signal→Publisher `3f49a0` | 45 14 * * * | no-agent | — | ~0 | |
| Auto-Crosspost `356f3c` | 5 13 * * 1-5 | no-agent | — | ~0 | overlap? see US-130 |
| Webhook Crosspost All `61cccd` | */5 | no-agent | — | ~0 | overlap? see US-130 |
| Daily Git Push `df2caa` | 3am | no-agent | — | ~0 | |
| Cron Watchdog `65dfc5` | */15 | no-agent | — | ~0 | |
| Vault Connection Weaver `98edbe` | every 240m | agent(local) | unknown | unknown | protocol flags cadence — measure before changing |
| Market Intelligence `79c465` | 0 13 * * 1-5 | T3 | unknown | unknown | keep |
| Vault Maintenance `9d77b5` | 0 2 * * * | T3 | unknown | unknown | retention audit US-129 |
| Connection Discovery `232975` | 0 4 * * * | T3 | unknown | unknown | |
| Model Review `07149d` | 0 9 * * 1 | T3 | unknown | unknown | candidate: no-agent gather + 1 call |
| Trade Monitor `d1e07c` | every 60m | T3 | unknown | unknown | exit split US-125 |
| Weekly Research `9202661` | 0 12 * * 0 | T3 | unknown | unknown | notepad/continuity allowed here |
| External Edge `e214a9` | 0 16 * * 2,4,0 | T3 | unknown | unknown | |
| Strategy Pipeline `2d8dff` | 0 17 * * 2,4,0 | T3 | unknown | unknown | seeder US-127 |
| Perf Report `cb22b0` | 0 13 * * * | T3 | unknown | unknown | candidate: no-agent gather + 1 call |
| LinkedIn `98a07` | 30 5 * * 2,4 | T3 | unknown | unknown | keep |
| ADR-005 Readiness `a76bfb` | 0 14 * * 1 | agent | unknown | unknown | governance |
| STR-Q Re-eval `23471` | mon 9am | T3 | unknown | unknown | US-121 gate — do not touch |
| Model Assignment note | — | — | — | — | see Model Review |

## Per-profile budget (UNKNOWN — inventory.yaml is a stub)

Cannot populate: enabled toolsets, soul size, always-loaded skills,
memory/continuity/notepad flags, `/context` breakdown, model tier, $/run.
This entire table is what US-124 must fill. Known pins only:

| Profile | Model (from version dump) |
|---------|---------------------------|
| default | deepseek/deepseek-v4-pro (running) |
| aegis-auditor | anthropic/claude-opus-4.8 |
| red-team | deepseek/deepseek-v4-flash |
| architect, coder, publisher, risk-guardian, researcher, backtester, documenter, product-owner, trading, consulting | not surfaced (— in dump) |

## Structural targets (apply AFTER US-124 measures cost)

- Toolset allowlists per profile; none should be `all`.
- No-agent for non-judgment work — extend beyond the current 8 crons.
- Gather with scripts / execute_code; one reasoning call to decide (Perf Report,
  Model Review are prime candidates).
- Souls 80–120 lines: identity + invariants only; skills on demand.
- Weaver: measure quality before demoting off 240m.
- 8 GB VPS: no mega-job merges.

## RAM note

8 GB / 240 GB SSD. The */5 crons (STR-Q sweep, crosspost-all) plus */15 watchdog
mean frequent short-lived processes; all no-agent, so LLM RAM pressure is from
the ~9 T3 agent crons. Concurrency of T3 agent runs is unverified — a scheduling
overlap check belongs in US-124's output.
