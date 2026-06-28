---
id: ADR-001
type: adr
status: accepted
created: 2026-06-27
deciders: [human, orchestrator]
tags: [adr, model-routing, cost-optimization]
---

# ADR-001: Model Routing Strategy

## Status
accepted

## Context
HermesForge uses multiple Hermes subagent profiles, each making LLM calls for different task types (research, coding, backtesting, documentation). Without a routing strategy, all calls default to the same model regardless of task complexity or cost sensitivity. The system needs to balance quality (especially for risk-sensitive tasks) with cost efficiency as the number of agent calls scales.

## Decision
**Phase 0 (Bootstrap):** Use Claude Sonnet 4.6 via OpenRouter as the primary model across all agents. Quality bias is appropriate while the system is being established and prompt quality/agent reliability is still being validated.

**Phase 1 (Optimization):** Develop a custom ModelRouter skill inside Hermes that learns from task outcomes to route intelligently:
- High-complexity, high-stakes tasks (Risk Guardian, Architecture decisions) → strong model (Claude Sonnet 4.6 or equivalent)
- Medium-complexity tasks (Research, Coding) → mid-tier model
- Low-complexity tasks (Documentation, Journaling) → fast/cheap model
- High-value synthesis tasks → consider MOA (Mixture of Agents)

## Rationale
- Starting with a strong model prevents compounding errors during bootstrap
- Custom routing will reduce cost significantly at scale without sacrificing quality where it matters
- MOA is expensive and should be reserved for genuinely high-value synthesis
- OpenRouter's Auto Router is a fallback if custom routing is not yet built

## Alternatives Considered
| Option | Pros | Cons |
|---|---|---|
| Always use strongest model | Simplest, highest quality | Most expensive at scale |
| OpenRouter Auto Router | No implementation needed | Less control, opaque routing |
| Custom ModelRouter skill | Optimal cost/quality | Requires implementation effort |
| Fixed model per agent | Predictable cost | Not adaptive to task complexity |

## Consequences
**Positive:**
- Quality maintained during bootstrap
- Clear path to cost optimization
- MOA usage controlled and intentional

**Negative/Trade-offs:**
- ModelRouter skill needs to be built and validated
- Outcome tracking requires instrumentation

**Risks:**
- Under-routing a risk-sensitive task to a weaker model → mitigated by hard rule: Risk Guardian always uses strong model

## Review Date
2026-09-27 (3 months) — review after Phase 1 routing is implemented
