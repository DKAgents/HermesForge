---
id: US-052
type: user-story
epic: EPIC-006
status: backlog
priority: medium
effort: M
created: 2026-06-30
updated: 2026-06-30
assigned_to: ""
tags: [backlog, strategy, vault, evidence-links, trading]
---

# US-052: Living Strategy Layer

## Story
**As a** systematic trader,  
**I want** a defined structure for Strategy notes in the vault where every strategy links to its supporting evidence (Murphy rules, insights, research, risk guidelines),  
**So that** I can trace why a strategy exists, update it when new knowledge contradicts or strengthens it, and never use a strategy that has lost its supporting rationale.

## Acceptance Criteria
- [ ] **AC1 — Strategy note schema:** Define and document a `Strategy` frontmatter schema: `id`, `type: strategy`, `status` (hypothesis/tested/validated/deprecated), `asset_class`, `trade_style` (swing/position), `timeframe`, `evidence_links[]`, `last_reviewed`, `confidence`.
- [ ] **AC2 — Strategy template:** An Obsidian template `Templates/Strategy-Template.md` exists with all required sections: `## Thesis`, `## Entry Criteria`, `## Exit Criteria`, `## Risk Rules Applied`, `## Supporting Evidence`, `## Counter-Evidence`, `## Change Log`.
- [ ] **AC3 — Evidence links enforced:** A `validate_strategy.py` script checks that every strategy note has ≥1 wikilink in `## Supporting Evidence` pointing to an existing vault note. Strategies failing validation are flagged in a report.
- [ ] **AC4 — Vault folder:** All strategy notes live in `05-Strategies/` (create folder). Sub-structure: `05-Strategies/Active/`, `05-Strategies/Deprecated/`, `05-Strategies/Hypotheses/`.
- [ ] **AC5 — Seed strategies:** At least 2 complete strategy notes written from Murphy concepts (e.g. "Trend-Following Breakout with Volume Confirmation", "Support/Resistance Reversal Entry"), each with ≥3 evidence links to Murphy notes + ≥1 risk guideline link.
- [ ] **AC6 — Auto-update triggers:** When a new Insight note is written to `08-Knowledge/Insights/` (from US-051), a check runs to see if any existing strategy's `evidence_links` should be updated. If semantic similarity to the strategy thesis > 0.7, an update suggestion is written to `05-Strategies/Pending-Updates/`.
- [ ] **AC7 — Strategy index:** `05-Strategies/00-Strategy-Index.md` lists all strategies with status, asset class, style, confidence, and last-reviewed date via Dataview query.
- [ ] **AC8 — Deprecation process:** When a strategy is moved to `Deprecated/`, a required `## Deprecation Reason` section must exist explaining what evidence changed.

## Notes / Context
> This is the bridge between the knowledge base (Murphy, insights) and the trading engine (EPIC-003 paper trading). No strategy enters paper trading without a vault note that passes `validate_strategy.py`.
>
> The `Change Log` section makes strategies "living documents" — each update to entry/exit criteria is recorded with date, reason, and the vault note that triggered the change.
>
> Seed strategy ideas from Murphy analysis: (1) Breakout with volume > 20-day avg + trend confirmed on weekly chart. (2) Support bounce with RSI divergence + stop below prior swing low. These should map cleanly to Murphy indicator and pattern notes.

## Dependencies
- **Blocks:** EPIC-003 US-020+ (paper trading needs validated strategies)
- **Blocked by:** US-051 (discovery insights strengthen strategies; can start in parallel but AC6 requires US-051)

## Definition of Done
- [ ] `05-Strategies/` folder structure created in vault
- [ ] `Strategy-Template.md` committed to `Templates/`
- [ ] `validate_strategy.py` implemented and tested
- [ ] 2 seed strategies written with passing validation
- [ ] `00-Strategy-Index.md` Dataview query working
- [ ] Schema documented in `00-Meta/` or ADR
