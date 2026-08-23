---
id: ADR-001
type: adr
status: accepted
created: 2026-06-27
updated: 2026-08-23
deciders: [human, orchestrator]
tags: [adr, model-routing, cost-optimization, llm-strategy]
topic: adrs
confidence: high
has_quotes: true
source: HermesForge ADR
---
# ADR-001: Model Routing Strategy

## Status
**accepted** — updated 2026-07-17 with Phase 1 concrete routing table

---

## Context

HermesForge uses multiple Hermes subagent profiles, each making LLM calls for
different task types (research, coding, backtesting, risk analysis, documentation).
Without a routing strategy, all calls default to the same model regardless of task
complexity or cost sensitivity.

We are in **Phase 0 → Phase 1 transition**: bootstrap is complete, the vault and
agent profiles exist, and we are now activating automation. This is the right moment
to define a concrete routing strategy before the task volume scales.

All models are accessed via **OpenRouter** through the **Headroom proxy** (port 8787),
configured as `provider: custom, base_url: http://127.0.0.1:8787/v1`.

---

## Section 1: Evaluation of claude-sonnet-4.6 for Trading Goals

### Strengths
| Dimension | Assessment |
|---|---|
| **Complex reasoning** | ✅ Excellent. Handles multi-step thesis construction, scenario analysis, conditional logic in strategies |
| **Long-context synthesis** | ✅ 200K context window. Well-suited for ingesting trading books, multi-day research threads, full backtests |
| **Strategy development** | ✅ Strong. Can hold complex market frameworks, identify edge cases, challenge assumptions |
| **Code quality** | ✅ Strong Python/pandas. Handles backtesting logic, data pipelines, Hermes skill scaffolding |
| **Risk reasoning** | ✅ Reliable for structured risk decisions when given clear rules (RISK_RULES.md input works well) |
| **Cost** | ⚠️ $3/$15 per 1M tokens (in/out). Acceptable for high-value tasks; expensive for bulk/routine work |
| **Speed** | ⚠️ ~3-5s TTFT. Fine for async tasks; noticeable in interactive flows |
| **Tool use / JSON** | ✅ Reliable structured output, good function-calling |

### Weaknesses for Our Use Case
- **Too expensive for high-volume tasks**: Daily market scans, news ingestion, simple journal
  entries, formatting tasks — all unnecessary at $15/M output tokens
- **Overkill for mechanical coding**: Simple script generation, template filling, cron job
  maintenance doesn't need Sonnet-class reasoning
- **Not the fastest**: For time-sensitive market alerts or rapid multi-step tool chains,
  faster models reduce latency meaningfully
- **Not the best for pure reasoning depth**: For genuinely complex multi-step mathematical
  reasoning (e.g., options pricing derivations, deep statistical analysis), Opus-class or
  specialized models outperform Sonnet

### Overall Verdict
Claude Sonnet 4.6 is the **right default** for Phase 0 bootstrapping and complex core tasks.
It should NOT be the default for everything at scale — cost and speed will become friction
points as automation volume increases.

---

## Section 2: Model Routing Strategy

### Design Principles
1. **Risk-sensitive tasks always use a strong model** — no downgrade for Risk Guardian
2. **Route by task complexity, not agent identity** — the same agent may do simple OR complex work
3. **Use fast/cheap models for high-frequency loops** — ForgeLoop, daily summaries, news triage
4. **Synthesize with strong models** — final strategy write-ups, thesis construction, ADR decisions
5. **Fallback to GLM-5.2** — when task complexity is ambiguous, default up not down

### Model Tier Reference (updated 2026-07-20)

| Tier | Model (OpenRouter) | Approx Cost (in/out per 1M) | Used For |
|------|--------------------|-----------------------------|----------|
| **T1** | `anthropic/claude-opus-4.8` | $5 / $25 | Novel strategy design, major architecture decisions, critical risk incidents only. Use sparingly. |
| **T2** | `deepseek/deepseek-v4-pro` | ~$0.41/$0.83 (OpenRouter, 2026-08-23) | Build work (coder, architect, orchestrator), high-quality research synthesis, hard floor for risk-guardian. Switched from `z-ai/glm-5.2` on 2026-08-23 per user request — see Change Log. |
| **T3** | `deepseek/deepseek-v4-flash` (primary)<br>`z-ai/glm-5.2` (secondary) | DeepSeek ~$0.05–0.14 / $0.15–0.28<br>GLM ~$0.4–1.4 / $1.3–4.4 | Most operational trading, backtesting, daily research, product-owner, most automation. |
| **T4** | Gemini Flash variants / MiniMax M3 / cheaper open models | <$0.50 blended | News triage, alert classification, bulk scanning, documenter, simple structured tasks. |

### Agent Routing Rules

| Agent | Default Tier | Hard Floor | Notes |
|-------|-------------|------------|-------|
| **risk-guardian** | T2 | T2 | Never route below GLM-5.2 (T2). Errors here are costly. |
| **orchestrator** | T2 | T2 | Active platform-build phase — force T2 |
| **architect** | T2 | T2 | Active platform-build phase — force T2 |
| **coder** | T2 | T2 | Active platform-build phase — force T2 |
| **researcher** | T3 | T3 | Escalate to T2 only if quality insufficient |
| **backtester** | T3 | T3 | Escalate to T2 for final synthesis only |
| **trading** | T3 | T3 | Escalate to T2 for complex analysis |
| **product-owner** | T3 | T4 | T3 default, T4 acceptable for formatting |
| **documenter** | T4 | T4 | Mechanical work only — T4 sufficient |

> **Note:** T2 was switched from `anthropic/claude-sonnet-5` to `z-ai/glm-5.2` on 2026-07-26 (user-directed). The Sonnet-5 introductory-pricing reminder (cron job 27a6aa851a96, scheduled Aug 25–28 2026) is now stale/no-op for T2 pricing purposes but has been left in place — see Change Log for follow-up note.

---

## Section 3: Implementation Approach

### Phase 1 (Now): Per-Skill Model Override (Recommended)

The cleanest implementation with current Hermes architecture is **per-skill model
configuration** using the `model` parameter in cron job creation and delegate_task calls.

```python
# High-stakes task — use Sonnet (explicit)
delegate_task(goal="...", context="...",
    model={"model": "anthropic/claude-sonnet-4.6", "provider": "custom"})

# Automation tick — use Flash (cheap)
cronjob(action="create", ...,
    model={"model": "google/gemini-2.0-flash-001", "provider": "custom"})
```

This requires no new infrastructure — Hermes already supports per-job model overrides.

### Phase 1 (Now): Agent Profile Headers

Each agent profile in `01-Agents/Profiles/` should document its default model tier:

```yaml
# In agent SOUL.md frontmatter
default_model_tier: tier-2  # or tier-3 for automation agents
model_floor: tier-2         # never route below this (Risk Guardian: tier-2 hard floor)
```

### Phase 2 (ForgeLoop): ModelRouter Skill

Build a `model-router` Hermes skill that:
1. Accepts a task description and returns a recommended model
2. Uses a simple rule-based classifier (keyword matching on task type + complexity signals)
3. Logs all routing decisions to `08-Knowledge/ModelRouter-Log.md` for review
4. Can be overridden by explicit `model_tier` parameter

Skill trigger keywords:
- `["risk", "guardian", "escalat", "incident"]` → tier-2 (hard floor)
- `["strategy", "thesis", "architecture", "ADR"]` → tier-1 or tier-2
- `["daily", "summary", "journal", "tick", "cron"]` → tier-3
- `["triage", "scan", "classify", "filter"]` → tier-4

### Phase 2: OpenRouter Auto Router as Fallback

`openrouter/auto` can be used as a safety net for unclassified tasks.
Do NOT use it as primary routing — it's opaque and inconsistent.

---

## Decision

**Immediate (Phase 1):**
- Keep `anthropic/claude-sonnet-4.6` as the global default in `config.yaml`
- Override to `google/gemini-2.0-flash-001` on all new cron jobs for automation tasks
- Override to Sonnet explicitly on Risk Guardian and synthesis tasks
- Risk Guardian: tier-2 (Sonnet) is a **hard floor** — document this in RISK_RULES.md

**Near-term (Phase 2):**
- Build `model-router` skill as part of EPIC-001 (Foundation)
- Instrument routing decisions in ForgeLoop run log
- Review routing effectiveness quarterly

---

## Rationale

- Gemini Flash is 10-40x cheaper than Sonnet and suitable for 60-70% of automation tasks
- Sonnet remains the right choice for anything touching real trading decisions
- Per-skill overrides are the pragmatic path now; full ModelRouter can be built later
- Hard floor on Risk Guardian prevents accidental cost-cutting on the most important agent

---

## Alternatives Considered

| Option | Pros | Cons |
|---|---|---|
| Single model for everything | Simplest | Expensive at scale; overkill for bulk tasks |
| OpenRouter Auto Router | No implementation | Opaque, inconsistent, no audit trail |
| Custom ModelRouter skill (now) | Optimal | Requires build effort before system is stable |
| Per-skill overrides (chosen) | Immediate, auditable, no new infra | Manual; needs discipline to apply consistently |
| Fixed model per agent | Predictable | Agents do both simple and complex tasks |

---

## Consequences

**Positive:**
- 60-70% cost reduction on automation tasks when Flash is used correctly
- Risk-sensitive tasks remain on Sonnet (quality maintained)
- Clear audit trail — model choice is explicit in each cron job / delegate_task call
- Path to full ModelRouter skill without blocking current progress

**Negative/Trade-offs:**
- Requires discipline to apply overrides consistently on new cron jobs
- Two models to monitor/test (Sonnet + Flash) instead of one
- Flash may produce lower quality on tasks that slip through without override

**Risks:**
- Accidentally routing a risk task to Flash — mitigated by Risk Guardian hard floor rule
- Flash behavior drift on OpenRouter — mitigate by pinning model version where possible

---

## Change Log

- **2026-08-23**: T2 tier switched from `z-ai/glm-5.2` to `deepseek/deepseek-v4-pro` per explicit user (Dan Keseloff) instruction. Rationale: GLM-5.2 price increased 45% since adoption ($0.67→$0.97 input, $2.10→$3.04 output); DeepSeek V4 Pro at $0.41/$0.83 is less than half the price with strong reasoning and 1M context window. Expected savings: ~$14/month (~$172/year, 7.9% cost reduction). User reviewed full OpenRouter model landscape (422 models), actual usage stats (729 sessions, 781M tokens, $181.61/month), and approved the switch. Hermes global default updated via `hermes config set model.default deepseek/deepseek-v4-pro`. Vault Connection Weaver and Discovery Engine scripts updated to use the new T2 model. T3 (deepseek-v4-flash) and T1 (claude-opus-4.8) unchanged. Follow-up: monitor quality of build/research/synthesis tasks on DeepSeek V4 Pro for regressions vs GLM-5.2 baseline.
- **2026-07-26**: T2 tier and hard floor switched from `anthropic/claude-sonnet-5` to `z-ai/glm-5.2` per explicit user (Dan Keseloff) instruction. Rationale given: cost (GLM-5.2 ~$0.67/$2.10 vs Sonnet-5 $2-3/$10-15 per 1M tokens) and consolidating on OpenRouter. User explicitly approved relaxing the risk-guardian/orchestrator/architect/coder hard floor to allow this. Follow-up: monitor risk-guardian/orchestrator/architect/coder output quality on GLM-5.2 for regressions vs. the Sonnet-5 baseline; escalate back to T1/Sonnet-class model if quality issues surface. Cron job `27a6aa851a96` (Sonnet-5 pricing reminder, Aug 25-28 2026) is now stale for T2 purposes but left in place — revisit at that date.
- **2026-07-29**: Cron job tier cleanup (biweekly model review 2026-07-27). Tiered 2 mechanical cron jobs to T3 (`deepseek/deepseek-v4-flash`): `27a6aa851a96` (Sonnet-5 Pricing Reminder — now stale, no LLM reasoning needed) and `a76bfb516675` (ADR-005 Readiness Check — mechanical status check). Paper Trading Capture (`4b178ecc02cd`) is `no_agent: true` (script-only, no LLM) — no tier assignment needed. Daily Signal Scanner (`3f49a07a2f04`) and Weekly Model Review (`07149d6b05cc`) kept on default (T2) — require reasoning/reliability. T4 (`gemini-2.0-flash-001`) remains unused — user deferred decision on removal. Sonnet-5 pricing countdown retired — user confirmed move away from Sonnet-5.

---

## Review Date
2026-10-17 (3 months) — review after Phase 2 ModelRouter skill is built and 90 days of
routing data is available. Evaluate: actual cost savings, routing accuracy, any quality
incidents from downgraded model calls.
