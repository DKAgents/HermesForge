---
id: ADR-001
type: adr
status: accepted
created: 2026-06-27
updated: 2026-07-17
deciders: [human, orchestrator]
tags: [adr, model-routing, cost-optimization, llm-strategy]
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
5. **Fallback to Sonnet** — when task complexity is ambiguous, default up not down

### Task Categories & Routing Table

| Category | Task Examples | Complexity | Recommended Model | Rationale |
|---|---|---|---|---|
| **Deep Reasoning** | Strategy architecture, complex thesis construction, multi-variable scenario analysis, ADR decisions | Very High | `anthropic/claude-opus-4-5` or `anthropic/claude-sonnet-4.6` | Needs best available reasoning depth |
| **Risk Analysis** | Risk Guardian decisions, position sizing review, incident escalation, options Greeks analysis | High | `anthropic/claude-sonnet-4.6` (**hard floor**) | Never route down; errors here are costly |
| **Market Synthesis** | Daily/weekly market summaries, sector analysis, macro synthesis, trade thesis writing | High | `anthropic/claude-sonnet-4.6` | Quality matters; these inform real decisions |
| **Research & Ingestion** | Trading book synthesis, paper analysis, news triaging, watchlist building | Medium-High | `anthropic/claude-sonnet-4.6` or `google/gemini-2.0-flash-001` | Gemini Flash for bulk; Sonnet for final synthesis |
| **Coding & Skills** | Hermes skill creation, backtesting scripts, data pipeline code, indicator implementations | Medium-High | `anthropic/claude-sonnet-4.6` | Code quality matters; Sonnet reliable here |
| **Backtesting Analysis** | Interpreting backtest results, identifying strategy weaknesses, statistical summaries | Medium | `anthropic/claude-sonnet-4.6` or `google/gemini-2.0-flash-001` | Flash sufficient for structured numeric analysis |
| **Daily Automation** | ForgeLoop tick execution, journal auto-fill, cron job summaries, routine health checks | Low-Medium | `google/gemini-2.0-flash-001` | Fast, cheap, reliable for structured tasks |
| **High-Volume Triage** | News feed filtering, watchlist scanning, alert classification, Twitter/X monitoring | Low | `google/gemini-2.5-flash-preview` or `meta-llama/llama-3.1-8b-instruct` | Maximum throughput, minimal cost |
| **Documentation** | Docstrings, README updates, story formatting, backlog grooming, template filling | Low | `google/gemini-2.0-flash-001` or `meta-llama/llama-3.1-8b-instruct` | No creativity required; fast is fine |

### Model Profiles

#### Tier 1 — Deep Reasoning (Use Sparingly)
**`anthropic/claude-opus-4-5`** via OpenRouter
- Cost: ~$15/$75 per 1M tokens
- Use: Architecture decisions, genuinely novel strategy design, complex multi-step derivations
- Trigger: When Sonnet returns uncertain/conflicting output on a high-stakes question

#### Tier 2 — Core Intelligence (Default for Quality Work)
**`anthropic/claude-sonnet-4.6`** via OpenRouter (current default)
- Cost: $3/$15 per 1M tokens
- Use: Risk Guardian (hard floor), market synthesis, strategy development, coding, complex research
- This is the workhorse. Do not route below this for anything risk-sensitive.

#### Tier 3 — Fast & Capable (Automation Workhorse)
**`google/gemini-2.0-flash-001`** via OpenRouter
- Cost: ~$0.075/$0.30 per 1M tokens (~10-40x cheaper than Sonnet)
- Use: ForgeLoop ticks, daily summaries, backtesting result parsing, structured data tasks
- Strengths: Fast TTFT, good tool use, large context (1M tokens), structured output reliable
- Weakness: Less reliable on open-ended complex reasoning

#### Tier 4 — Bulk / Triage (High Volume Only)
**`google/gemini-2.5-flash-preview`** or **`meta-llama/llama-3.1-8b-instruct`**
- Cost: <$0.10 per 1M tokens
- Use: News triage, alert classification, watchlist scanning, simple text extraction
- Only use when task is truly mechanical with clear pass/fail criteria

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

## Review Date
2026-10-17 (3 months) — review after Phase 2 ModelRouter skill is built and 90 days of
routing data is available. Evaluate: actual cost savings, routing accuracy, any quality
incidents from downgraded model calls.
