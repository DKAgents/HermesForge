---
id: ADR-003
type: decision
status: accepted
date: 2026-07-19
deciders: [HermesForge Orchestrator]
tags: [adr, strategy, schema, knowledge-evolution]
topic: adrs
confidence: high
has_quotes: false
source: HermesForge ADR
---
# ADR-003: Strategy Note Schema and Living Strategy Layer

## Status

**Accepted** — 2026-07-19

## Context

HermesForge needs a structured, verifiable way to store trading strategies in the vault such that:

1. Every strategy is traceable to specific evidence in the knowledge base
2. Strategies can be automatically validated (no orphaned claims)
3. Strategies can be updated as new knowledge is discovered without losing history
4. The system can gate strategies from paper → live mode using the evidence requirement as a quality signal

Without a schema, strategies become unconstrained prose that cannot be queried, validated, or systematically improved.

## Decision

### Folder Structure
All strategies live under `06-Strategies/` with sub-folders:
- `Active/` — strategies currently running in paper or live mode
- `Hypotheses/` — strategies under development, not yet paper traded
- `Deprecated/` — retired strategies (must include `## Deprecation Reason`)
- `Pending-Updates/` — auto-generated update suggestions from US-051 discovery and US-053 lessons
- `Backtests/` — backtest result files (CSV, JSON, or markdown)
- `Live/` — (reserved for future live trading)

### Strategy Note Schema (frontmatter)

| Field | Type | Required | Values |
|-------|------|----------|--------|
| `id` | string | ✅ | `STR-YYYYMMDD-slug` |
| `type` | string | ✅ | Must be `strategy` |
| `status` | enum | ✅ | `hypothesis` \| `tested` \| `validated` \| `deprecated` |
| `asset_class` | enum | ✅ | `stocks` \| `crypto` \| `options` \| `futures` \| `mixed` |
| `trade_style` | enum | ✅ | `swing` \| `position` \| `day` \| `scalp` |
| `timeframe` | enum | ✅ | `daily` \| `weekly` \| `4h` \| `1h` \| `multi` |
| `confidence` | enum | ✅ | `low` \| `medium` \| `high` \| `validated` |
| `market_regime` | enum | ✅ | `trending` \| `ranging` \| `volatile` \| `any` |
| `core_idea` | enum | ✅ | `breakout` \| `pullback` \| `mean-reversion` \| `trend-continuation` \| `reversal` \| `other` |
| `evidence_links` | list | ✅ | List of vault note stems (informational; wikilinks in body are the enforced source) |
| `last_reviewed` | date | ✅ | ISO 8601 `YYYY-MM-DD` |
| `publish_enabled` | bool | optional | `true` \| `false` — whether this strategy posts alerts to Discord (default: not published if absent) |
| `publish_channel` | enum | optional (required if `publish_enabled: true`) | `stocks` \| `crypto` — which Discord channel to publish alerts to |

### Required Sections (body)
All strategy notes must contain these H2 sections:
1. `## Thesis` — the edge hypothesis
2. `## Entry Criteria` — specific, checkable conditions
3. `## Exit Criteria` — stop, target, time stop, trailing stop
4. `## Risk Rules Applied` — explicit list of RISK_RULES.md rules that apply
5. `## Supporting Evidence` — ≥1 wikilink to existing vault note (enforced by validator)
6. `## Counter-Evidence` — notes or edge-conditions that weaken the thesis
7. `## Change Log` — date-stamped history of changes

### Evidence Requirement
`validate_strategy.py` enforces:
- `## Supporting Evidence` must contain ≥1 `[[wikilink]]` pointing to an existing vault note
- All wikilinks are verified to resolve to actual files at validation time
- Strategies failing validation cannot be promoted from `hypothesis` to `tested`

### Publish Control (EPIC-009)
Two optional frontmatter fields gate Discord signal distribution per-strategy, independent of code changes:
- `publish_enabled: true | false` — whether the strategy's scanner output posts alerts to Discord. Absent or `false` = no publishing.
- `publish_channel: stocks | crypto` — target Discord channel category. Required when `publish_enabled: true`; validator warns (does not error) if missing or set to an unrecognized value.

This keeps publish/no-publish decisions in the vault (auditable, versioned) rather than in a separate config file, consistent with the vault-first philosophy.

### Auto-Update Mechanism
When the Discovery Engine (US-051) finds an insight with similarity > 0.7 to a strategy's thesis, it writes a suggestion note to `06-Strategies/Pending-Updates/`. The strategy author reviews and applies changes to the strategy `## Change Log`.

### Template
`Templates/Strategy-Template.md` provides the canonical starting point for new strategies.

## Alternatives Considered

1. **Free-form markdown notes** — No validation possible; strategies become stale without detection. Rejected.
2. **External database (Airtable/Notion)** — Breaks the vault-first philosophy; adds external dependency. Rejected.
3. **JSON schema files alongside markdown** — Over-engineered for current scale; Dataview queries can extract frontmatter directly. Rejected.

## Consequences

**Positive:**
- Every strategy claim is traceable to a vault note
- `validate_strategy.py` acts as a CI gate before paper trading
- Dataview queries in `00-Strategy-Index.md` provide instant visibility
- Change Log makes strategies living documents with full audit trail

**Negative:**
- Creating a strategy requires more upfront work (must find evidence links)
- Validator will block promotion of strategies with broken wikilinks after note renames

**Mitigation:** The vault maintenance pipeline (US-050) runs nightly and keeps indexes fresh; `generate_wikilinks.py` helps surface relevant notes during strategy authoring.

## References

- [[RISK_RULES]] — Risk framework that all strategies must cite applicable rules from
- [[00-Strategy-Index]] — Dataview index of all strategies
- `scripts/validate_strategy.py` — Automated validation tool
- `Templates/Strategy-Template.md` — Strategy authoring template
- US-052: Living Strategy Layer (backlog story)
