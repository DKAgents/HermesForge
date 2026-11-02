---
id: ADR-012
type: adr
status: proposed
created: 2026-11-02
deciders: [architect]
tags: [adr, model-routing, delegation, cost-optimization, tiers]
topic: adrs
confidence: medium
has_quotes: false
source: HermesForge ADR
---
# ADR-012: Delegation Tier Routing (profile_routes)

## Status
**proposed** — DESIGN ONLY. No config applied, no plugin installed, no backend
switched. Implementation is gated on swarm review (coder + risk-guardian) and
human approval. This ADR defines the delegation config shape, the role→tier
mapping, and the fail-safe that prevents a misconfigured route from silently
downgrading a T2-floor agent.

---

## Context

US-220 pinned the T3/T4 agent profiles' `config.yaml` models. That fixed DIRECT
profile dispatch (`HERMES_PROFILE=… hermes chat`) and cron jobs. It did **not**
fix `delegate_task`, because delegation does not dispatch a profile by default —
it bills by the PARENT model.

Ground truth read this session (2026-11-02):

- The active profile's `config.yaml` `delegation:` section has NO `backend` key
  and empty `model:`/`provider:` (`delegation.model: ''`). Under the built-in
  `default` backend with an empty route, every child **inherits the parent's
  route** — i.e. the orchestrator's T2 `deepseek/deepseek-v4-pro-0813`. This is
  exactly the leak US-221 describes: parallel research subagents bill at T2
  regardless of role.
- Hermes delegation resolves a backend from `delegation.backend`. `default` is
  the built-in (bundled) strategy. `model_map` and `profile_routes` are separate
  backends supplied by the **advanced-delegation plugin** — see
  `agent/delegation_registry.py` ("Populated by plugins via
  `register_delegation_provider`") and `agent/delegation_provider.py` (route
  vocabulary includes a `profile` key: "Core runs the child as that profile: its
  config, primary model and credentials, skills, SOUL.md and terminal policy").
- **The advanced-delegation plugin is NOT installed.** Only the bundled
  `plugins/delegation/default` exists on disk; `plugins.enabled` in the active
  profile lists only `homeassistant`. `model_map`/`profile_routes` are therefore
  **unavailable today** — `backend_status("profile_routes")` returns a
  "backend is not installed" reason and `delegate_task` fails closed. Installing
  the plugin is a blocking precondition (flagged in §Assumptions).

The fix is to select a delegation backend that routes each subagent to the
model it is already declared to use, honoring ADR-001's tier table, and to make
a silent T2-floor downgrade impossible.

---

## Decision

### 1. Backend: `profile_routes` (primary), over `model_map`

Use the **`profile_routes`** backend. Rationale:

- Each swarm role already has a 1:1 Hermes profile whose `config.yaml` — since
  US-220 — is pinned to the right tier. `profile_routes` makes the subagent run
  **as that profile**, adopting its `config.yaml` model, plus its `SOUL.md`,
  skills, and persona. The profile `config.yaml` is the single source of truth
  for the tier; the delegation config only names the profile, so the model string
  is NOT duplicated in a second place (no drift risk).
- `model_map` would re-encode the model strings a second time in
  `delegation.backends.model_map.options` and would give the child an
  anonymous-agent body (no profile `SOUL.md`/skills), losing the persona the
  swarm relies on.

`model_map` is documented as an alternative if persona/skills inheritance is
later found undesirable, but it is NOT chosen here.

### 2. Exact mapping (role → profile → tier/model/provider)

The `profile_routes` allowlist is an **identity mapping**: each role name equals
its profile name. This is deliberate — it makes the fail-safe assertable (§4)
and removes any "role mapped to the wrong profile" failure class.

| Role (ADR-001)    | Profile (on disk) | Tier | Effective model                     | Provider   | Guard |
|-------------------|-------------------|------|-------------------------------------|------------|-------|
| coder             | coder             | T2   | `deepseek/deepseek-v4-pro-0813`     | openrouter | HARD floor |
| architect         | architect         | T2   | `deepseek/deepseek-v4-pro-0813`     | openrouter | HARD floor |
| orchestrator      | orchestrator      | T2   | `deepseek/deepseek-v4-pro-0813`     | openrouter | HARD floor |
| risk-guardian     | risk-guardian     | T2   | `deepseek/deepseek-v4-pro-0813`     | openrouter | HARD floor |
| researcher        | researcher        | T3   | `deepseek/deepseek-v4-flash-0731`   | openrouter | T2 hard floor for hypothesis-gen (per-call override) |
| backtester        | backtester        | T3   | `deepseek/deepseek-v4-flash-0731`   | openrouter | escalate T2 for final synthesis |
| trading           | trading           | T3   | `deepseek/deepseek-v4-flash-0731`   | openrouter | escalate T2 for complex analysis |
| product-owner     | product-owner     | T3   | `deepseek/deepseek-v4-flash-0731`   | openrouter | — |
| publisher         | publisher         | T3   | `deepseek/deepseek-v4-flash-0731`   | openrouter | — |
| red-team          | red-team          | T3   | `deepseek/deepseek-v4-flash-0731`   | openrouter | — |
| documenter        | documenter        | T4   | `deepseek/deepseek-v4-flash-0731`¹  | openrouter | cheap tier (see §3 note) |

¹ The T4 "cheap tier" has no distinct model deployed: US-220 pinned `documenter`
to `flash-0731` to satisfy ADR-001's "<$0.50/blended" T4 budget without adding a
new provider. The model string is therefore identical to T3; the T4 designation
is a **cost-budget classification**, not a different model. OPEN — see §Assumptions.

On-disk profiles **not** in ADR-001's routing table and therefore **not** in the
allowlist (tier undefined): `consulting`, `aegis-auditor`. They are excluded from
`profile_routes` until explicitly tiered (they can only ever be picked if listed;
an unlisted profile is unreachable, which is the fail-closed default).

### 3. Config shape (exact keys, verified against Hermes delegation docs + core)

```yaml
# active profile (~/.hermes/config.yaml — the orchestrator's)
delegation:
  backend: profile_routes
  backends:
    profile_routes:
      profiles:
        - name: coder
          description: "Code changes, refactors, tests. T2 floor."
        - name: architect
          description: "Architecture/ADR design. T2 floor."
        - name: orchestrator
          description: "Coordination and planning. T2 floor."
        - name: risk-guardian
          description: "Risk analysis and guardrails. T2 hard floor."
        - name: researcher
          description: "Web and vault research, summaries. T3."
        - name: backtester
          description: "Backtests and strategy validation. T3."
        - name: trading
          description: "Operational trading analysis. T3."
        - name: product-owner
          description: "Spec and backlog shaping. T3."
        - name: publisher
          description: "Embeds, alerts, templates, posts. T3."
        - name: red-team
          description: "Adversarial review. T3."
        - name: documenter
          description: "Documentation, formatting. T4 cheap tier."
      default: orchestrator    # fail UP, not down (ADR-001 principle #5)
```

Key facts that make this safe (all verified):

- `profiles` is both the allowlist AND what the parent model reads. An unlisted
  profile can never be picked (fail-closed).
- A listed `name` with no matching on-disk profile is refused with a pointer to
  `hermes profile list`.
- `default: orchestrator` (T2) means any task the parent does not explicitly
  route runs on T2 — fail UP, matching ADR-001 principle #5 ("default up not
  down"). A cheap T3/T4 profile is deliberately NOT made the default.
- If the backend is missing/disabled/unavailable, `delegate_task` returns a tool
  error naming the backend and the fix and starts **no** subagent — it never
  quietly runs children on the default route.

### 4. Fail-safe: a misconfigured route cannot silently downgrade a T2-floor agent

The T2 floor is protected by **two independent mechanisms**, one static (before
any dispatch) and one dynamic (after dispatch). Both are required; neither is
advisory.

**4a. Static — config-read assertion (pre-dispatch, primary defense).** The
failure US-220 found was "no `config.yaml` → inherits the global default." The
four T2-floor profiles (`coder`, `architect`, `orchestrator`, `risk-guardian`)
currently have **no** `config.yaml` and inherit the global default
(`deepseek/deepseek-v4-pro-0813`, T2) — correct today, but exactly as fragile as
the T3 leak was. To make the floor a *fact* rather than an *inheritance
accident*, implementation MUST:

1. Give each T2-floor profile an explicit `config.yaml` pinning
   `model.default: deepseek/deepseek-v4-pro-0813` + `provider: openrouter`
   (identical shape to the US-220 T3 pins).
2. Add a static **assert** that, for each T2-floor role, the profile's resolved
   model (explicit `config.yaml` `model.default`, else global default) equals
   `deepseek/deepseek-v4-pro-0813` with `provider: openrouter`; and that the
   `profile_routes` allowlist is a 1:1 identity map (role name == profile name,
   no T2 role pointing at a non-T2 profile, `default` not a T3/T4 profile).
3. This assert runs as part of the implementation's acceptance gate (and ideally
   as a periodic check so a future edit to a profile `config.yaml` that drops a
   T2 floor is caught at the source before any subagent spawns).

**4b. Dynamic — `model_snapshot`/`provider_snapshot` (post-dispatch, ground
truth).** US-220 established that `model_snapshot`/`provider_snapshot` record what
*actually ran* (the declared `model` field can lie). The acceptance proof is a
probe dispatch: one `delegate_task` per role, then read each resulting session's
`model_snapshot`/`provider_snapshot` and assert:

- every T2-floor role's snapshot == `deepseek/deepseek-v4-pro-0813` / `openrouter`;
- every T3 role's snapshot == `deepseek/deepseek-v4-flash-0731` / `openrouter`;
- `documenter`'s snapshot == its pinned (flash) model.

A snapshot mismatch (e.g. `model_snapshot=v4-pro` on a T3 role, or a T2 role
snapshotting flash) is a **hard failure** and blocks acceptance — never a warning.

**Limitation to state honestly (not overclaim):** neither mechanism constrains
the parent model's *per-task choice*. `profile_routes` exposes the profiles as an
enum the parent selects; a parent could in principle route a risk-guardian task to
the `researcher` profile (T3). That is a *prompt/supervision* concern (governed by
the orchestrator's SOUL.md + the identity map convention), not a config
enforcement, because routing-by-identity cannot also route-by-complexity within a
role. It is mitigated by the identity map (each role = its own profile) and the
T2 `default`. Flagged, not solved, here.

---

## Consequences

**Positive:** delegate_task subagents bill at their role's tier (removes the
continuing T2 leak on the heaviest parallel-research path); the profile
`config.yaml` stays the single source of truth (no duplicated model strings);
T2-floor downgrade is now a test failure, not a silent inheritance accident.

**Negative / trade-offs:** requires installing the advanced-delegation plugin as
a new dependency; `profile_routes` routes by *identity*, so it cannot express
ADR-001's "route by task complexity within a role" (the researcher's T2
hypothesis-generation floor must remain an explicit per-call model override, as
it is today); delegation config is profile-scoped, so the mapping must be written
to the orchestrator's `config.yaml` (the profile that actually calls
`delegate_task`).

**Risks:** a future edit that lowers a profile's `config.yaml` pin survives only
because of §4's static assert — if implementation skips 4a, the same "inherits a
different default" failure US-220 found can recur for T2 floors. The plugin's
profile-route credential-sharing surface (listed profiles share credentials/keys
with their subagents) is acceptable here only because each role maps to its own
same-named profile.

---

## Assumptions & Open Questions (explicit — where a fact is unverified it is marked)

- **A1 — BLOCKING / VERIFIED:** `advanced-delegation` plugin is NOT installed
  (only `plugins/delegation/default` is bundled; `plugins.enabled` = `[homeassistant]`).
  `model_map`/`profile_routes` backends are unavailable until it is installed and
  enabled. This is a hard precondition, verified against `plugins/` on disk and
  `agent/delegation_registry.py`. NOT a config-only change.
- **A2 — UNVERIFIED (per docs + core, not empirically):** that a `profile_routes`
  child actually *bills* at the child profile's model. Core
  `agent/delegation_provider.py` states a `profile` route runs the child "as that
  profile: its config, primary model and credentials" and "ignores the other route
  keys." This implies billing follows the profile model, but the claim must be
  proven via §4b's `model_snapshot` probe — that probe IS the acceptance test.
- **A3 — OPEN:** the `documenter` T4 "cheap tier" has no distinct model (pinned to
  `flash-0731`, same string as T3). Whether to keep the provisional flash pin or
  deploy a genuinely cheaper T4 model (ADR-001 T4 row: Gemini Flash / MiniMax M3)
  is deferred. The current pin is cost-budget-compliant but not a real T4 tier.
- **A4 — OPEN:** `consulting` and `aegis-auditor` profiles are on disk but absent
  from ADR-001's routing table; their tier is undefined. They are excluded from
  the allowlist. Assign them a tier (or confirm they must stay unroutable) before
  they are ever delegated to.
- **A5 — OPEN:** exact plugin install mechanism (`hermes plugins install
  advanced-delegation` vs catalog) and whether it needs a `/new` session for the
  `delegate_task` schema (which carries the per-task `profile` enum) to refresh —
  the cached tool list switches with the backend, so a running session stays on
  its old backend until `/new`. Confirm the operational restart step.
- **A6 — UNVERIFIED key spelling:** the `delegation.backends.profile_routes`
  `profiles`/`default` key spellings are taken from the official delegation docs
  and are corroborated by core (`hermes_cli/web_routers/delegation.py`,
  `hermes_cli/config_defaults.py`), but were not exercised against the installed
  Hermes (plugin absent). Exact key names, not invented — but not yet machine-tested here.

---

## Related
- [[ADR-001-Model-Routing-Strategy]] · [[ADR-005-Stage-Based-Model-Floors-and-Red-Team]]
- [[US-220-Enforce-Tier-Routing]] · [[US-221-Delegation-Tier-Routing]]
- [[US-002-Hermes-Profiles]] · [[EPIC-015-Autonomy]]