---
id: US-051
type: user-story
epic: EPIC-006
status: done
priority: high
effort: L
created: 2026-06-30
updated: 2026-06-30
assigned_to: ""
tags: [backlog, knowledge, discovery, rag, connections, insights]
---

# US-051: Novel Connection Discovery Engine

## Story
**As a** swing/position trader building a systematic edge,  
**I want** the system to actively search across all vault knowledge (rules, patterns, indicators, risk guidelines, research) and surface non-obvious, high-value connections,  
**So that** I can discover compound insights — e.g. "Murphy's volume confirmation rule + a risk guideline about volatility regimes → a specific entry filter" — that I would not find by reading individual notes linearly.

## Acceptance Criteria
- [ ] **AC1 — Cross-domain query engine:** A `discover_connections.py` script queries both FTS and semantic indexes simultaneously, using a set of seed prompts designed to find connections *across* knowledge domains (e.g. indicators + risk, patterns + macros, entry rules + position sizing).
- [ ] **AC2 — Cluster analysis:** Notes are grouped into semantic clusters (k-means or HDBSCAN on ChromaDB embeddings). Connections between clusters (notes from different clusters that are semantically close) are flagged as cross-domain candidates.
- [ ] **AC3 — LLM synthesis step:** For each candidate connection pair/group (top 20 per run), a T2 model call synthesizes whether the connection is actionable and non-trivial. Output: `connection_type`, `actionability_score` (1–5), `synthesis`, `supporting_notes[]`.
- [ ] **AC4 — Insight notes written to vault:** Each accepted connection (actionability ≥ 3) is written as an Obsidian note in `08-Knowledge/Insights/` with frontmatter `type: insight`, `sources: [note1, note2, ...]`, `actionability: N`, and a `## Trading Implication` section.
- [ ] **AC5 — Discovery report:** A weekly discovery run produces a `Discoveries-YYYY-WW.md` report in `04-ForgeLoop/Discovery/` listing all new insights, ranked by actionability score.
- [ ] **AC6 — Avoid redundancy:** Before writing a new insight, semantic similarity is checked against existing insight notes. Skip if cosine similarity > 0.85 to avoid duplicates.
- [ ] **AC7 — Configurable seed prompts:** Seed prompts are stored in a `discovery_seeds.yaml` config file so new domains can be added without code changes.
- [ ] **AC8 — Cron schedule:** Discovery engine runs weekly (e.g. Sunday 03:00 UTC) and delivers insight summary to Discord.

## Notes / Context
> The distinction between "obvious" and "non-obvious" connections: an obvious connection is two notes in the same subfolder about the same indicator. A non-obvious connection is e.g. a volume rule in `indicators/` that contradicts a risk guideline in `07-Risk/`, or a pattern in `patterns/` whose entry condition matches a macro condition in `03-Research/`. The cross-cluster design in AC2 enforces this — same-cluster pairs are deprioritized.
>
> Seed prompt examples: "What volume conditions are required before entering a breakout?", "Which technical patterns are invalidated by high-volatility regimes?", "Where do Murphy's stop-loss rules conflict with the 1% position sizing limit?", "What entry criteria improve when macro trend is confirmed?"
>
> T2 model = `anthropic/claude-sonnet-4.6` per Hermes model routing config.

## Dependencies
- **Blocks:** US-052 (strategy notes are built from discovered connections), US-053 (lessons reference insight notes)
- **Blocked by:** US-050 (vault must be fresh and fully indexed before discovery is meaningful)

## Definition of Done
- [ ] `discover_connections.py` implemented and produces ≥5 candidate connections on first run
- [ ] At least 3 insight notes written to `08-Knowledge/Insights/`
- [ ] Weekly cron job registered, first run delivered to Discord
- [ ] `discovery_seeds.yaml` committed with ≥10 seed prompts
- [ ] Dedup check against existing insights confirmed working
