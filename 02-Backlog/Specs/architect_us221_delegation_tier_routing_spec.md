# Architect Spec — US-221 (Delegation Tier Routing via profile_routes)

Date: 2026-11-02
Author: Architect (HermesForge)
Status: DESIGN ONLY — backend selection + mapping + fail-safe contract. No config
applied, no plugin installed, no backend switched. Awaiting swarm review + human
approval.
Epic: EPIC-017 (Gauntlet Pipeline Productionization)
Depends on: US-220 (profile config.yaml tier pins, done)
ADR: 03-ADRs/ADR-012-Delegation-Tier-Routing.md (this is the ADR-level companion)

Ground truth read:
- 02-Backlog/Stories/US-221-Delegation-Tier-Routing.md
- 03-ADRs/ADR-001-Model-Routing-Strategy.md (tier table + agent routing rules)
- /root/.hermes/config.yaml (delegation section: no `backend`, empty model/provider)
- /root/.hermes/profiles/* (13 on-disk profiles; 8 have config.yaml after US-220)
- Hermes delegation docs + core `agent/delegation_provider.py`,
  `agent/delegation_registry.py`, `hermes_cli/web_routers/delegation.py`

Summary of the defect this fixes: direct profile dispatch and cron are tier-pinned
(US-220), but `delegate_task` bills by the PARENT model. With no delegation backend
and empty delegation.model, every subagent inherits the orchestrator's T2
`deepseek/deepseek-v4-pro-0813` regardless of role — a continuing cost leak on the
parallel-research path.

---

# PART 1 — Backend choice and exact mapping

## 1.1 Backend: `profile_routes`

`delegation.backend: profile_routes` (from the advanced-delegation plugin). Each
subagent runs AS its role's Hermes profile, adopting that profile's `config.yaml`
model (already tier-pinned by US-220) plus `SOUL.md`/skills/persona. The profile
`config.yaml` is the single source of truth for tier; model strings are NOT
duplicated in the delegation config.

## 1.2 Role → profile mapping (identity map, 1:1 role name == profile name)

| Role | Profile | Tier | Model | Provider | Guard |
|---|---|---|---|---|---|
| coder | coder | T2 | deepseek/deepseek-v4-pro-0813 | openrouter | HARD floor |
| architect | architect | T2 | deepseek/deepseek-v4-pro-0813 | openrouter | HARD floor |
| orchestrator | orchestrator | T2 | deepseek/deepseek-v4-pro-0813 | openrouter | HARD floor |
| risk-guardian | risk-guardian | T2 | deepseek/deepseek-v4-pro-0813 | openrouter | HARD floor |
| researcher | researcher | T3 | deepseek/deepseek-v4-flash-0731 | openrouter | T2 hard floor for hypothesis-gen (per-call) |
| backtester | backtester | T3 | deepseek/deepseek-v4-flash-0731 | openrouter | — |
| trading | trading | T3 | deepseek/deepseek-v4-flash-0731 | openrouter | — |
| product-owner | product-owner | T3 | deepseek/deepseek-v4-flash-0731 | openrouter | — |
| publisher | publisher | T3 | deepseek/deepseek-v4-flash-0731 | openrouter | — |
| red-team | red-team | T3 | deepseek/deepseek-v4-flash-0731 | openrouter | — |
| documenter | documenter | T4 | deepseek/deepseek-v4-flash-0731 (provisional cheap pin; see A3) | openrouter | — |

Excluded (tier undefined in ADR-001, left OFF the allowlist): `consulting`,
`aegis-auditor`. An unlisted profile is unreachable (allowlist = fail-closed).

## 1.3 Exact config shape

```yaml
delegation:
  backend: profile_routes
  backends:
    profile_routes:
      profiles:
        - { name: coder,           description: "Code changes/refactors/tests. T2 floor." }
        - { name: architect,       description: "Architecture/ADR design. T2 floor." }
        - { name: orchestrator,    description: "Coordination and planning. T2 floor." }
        - { name: risk-guardian,   description: "Risk analysis and guardrails. T2 hard floor." }
        - { name: researcher,      description: "Web/vault research, summaries. T3." }
        - { name: backtester,      description: "Backtests and strategy validation. T3." }
        - { name: trading,         description: "Operational trading analysis. T3." }
        - { name: product-owner,   description: "Spec and backlog shaping. T3." }
        - { name: publisher,       description: "Embeds, alerts, templates, posts. T3." }
        - { name: red-team,        description: "Adversarial review. T3." }
        - { name: documenter,      description: "Documentation, formatting. T4 cheap tier." }
      default: orchestrator    # fail UP, not down (ADR-001 principle #5)
```

---

# PART 2 — Fail-safe contract (binding)

A misconfigured route MUST NOT silently downgrade a T2-floor agent. Two
independent, mandatory mechanisms:

## 2.1 Static — config-read assertion (pre-dispatch)

1. Give each T2-floor profile (`coder`, `architect`, `orchestrator`,
   `risk-guardian`) an explicit `config.yaml` pinning
   `model.default: deepseek/deepseek-v4-pro-0813` + `provider: openrouter`
   (same shape as the US-220 T3 pins). Removes the "inherits global default"
   fragility that caused the T3 leak.
2. Add a static assert (acceptance-gate test) that, per T2-floor role:
   - the profile's resolved model (explicit `model.default`, else global default)
     == `deepseek/deepseek-v4-pro-0813` and provider == `openrouter`;
   - the `profile_routes` allowlist is a 1:1 identity map;
   - no T2 role maps to a non-T2 profile;
   - `default` is not a T3/T4 profile.
3. Assert must run at implementation acceptance, and (ideally) as a periodic
   check so a later profile `config.yaml` edit that drops a floor is caught at
   the source.

## 2.2 Dynamic — `model_snapshot` / `provider_snapshot` (post-dispatch)

Probe dispatch: one `delegate_task` per role, then read each resulting session's
`model_snapshot`/`provider_snapshot` and assert:

- T2-floor roles snapshot == `deepseek/deepseek-v4-pro-0813` / `openrouter`.
- T3 roles snapshot == `deepseek/deepseek-v4-flash-0731` / `openrouter`.
- `documenter` snapshot == its pinned flash model.

A mismatch is a HARD failure (blocks acceptance), never a warning. This is the
ground-truth proof that billing actually follows the route — the same
declared-vs-actual distinction US-220 used to catch Auto-Crosspost.

## 2.3 Honest limitation (not overclaimed)

Neither mechanism constrains the parent model's per-task choice of profile: the
profiles are an enum the parent selects, so a parent could in principle route a
risk-guardian task to `researcher` (T3). Mitigated by the identity map + T2
`default`, but it is a supervision concern (orchestrator SOUL.md), not a config
gate. Also: a `profile` route ignores other route keys, so the researcher's T2
hypothesis-generation floor MUST remain an explicit per-call model override
(per ADR-001), not a second profile route.

---

# PART 3 — Acceptance criteria (mirrors US-221)

- A `delegate_task` dispatch bills at the target profile's tier, proven by
  `model_snapshot`/`provider_snapshot` (§2.2).
- T2-floor agents are never downgraded: static assert (§2.1) passes AND no
  snapshot shows a T2 role on `flash-0731`.
- Before/after monthly cost reported (parallel-research path should drop from
  T2 to the T3 roles' rate).

## 3.1 Assumptions & open questions (unverified items marked)

- A1 — BLOCKING / VERIFIED: advanced-delegation plugin NOT installed (only
  `plugins/delegation/default` bundled; `plugins.enabled` = `[homeassistant]`).
  Must install/enable before `profile_routes` is selectable. Not config-only.
- A2 — UNVERIFIED (docs + core, not empirical): that a profile-route child
  actually bills at the child profile's model. §2.2's snapshot probe is the proof.
- A3 — OPEN: documenter T4 has no distinct model (pinned to flash-0731). Defer a
  genuine T4 model decision.
- A4 — OPEN: `consulting`/`aegis-auditor` tier undefined — excluded from allowlist.
- A5 — OPEN: plugin install mechanism + `/new` restart step for the refreshed
  `delegate_task` schema.
- A6 — UNVERIFIED key spelling: `delegation.backends.profile_routes.profiles/default`
  taken from docs + core, but not machine-tested (plugin absent). Exact keys, not invented.

END OF DESIGN.