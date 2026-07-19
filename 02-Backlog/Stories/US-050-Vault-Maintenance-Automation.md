---
id: US-050
type: user-story
epic: EPIC-006
status: backlog
priority: high
effort: M
created: 2026-06-30
updated: 2026-06-30
assigned_to: ""
tags: [backlog, knowledge, automation, indexing, maintenance]
---

# US-050: Automate Ongoing Vault Maintenance

## Story
**As a** HermesForge researcher,  
**I want** the vault to automatically re-index, re-embed, apply frontmatter, generate wikilinks, and run deduplication whenever new notes are added,  
**So that** I can ingest a new book or add research notes without manual pipeline steps, and vault-query tools always return fresh, well-linked results.

## Acceptance Criteria
- [ ] **AC1 — Watch/trigger:** A script (or cron job) detects new or modified `.md` files in the vault and triggers the maintenance pipeline. Detection method: git diff against last-run commit, or file mtime comparison against a stored checkpoint.
- [ ] **AC2 — Re-index:** `build_index.py` runs incrementally (new/changed files only) and updates `vault.db` without full rebuild unless forced.
- [ ] **AC3 — Re-embed:** `embed_vault.py` runs incrementally; only notes not already in ChromaDB are embedded. Existing embeddings are not re-computed unless the note body changed.
- [ ] **AC4 — Frontmatter enforcement:** A `check_frontmatter.py` script scans new notes and adds any missing required fields (`topic`, `confidence`, `has_quotes`, `tags`, `source`) with sensible defaults, logging what was patched.
- [ ] **AC5 — Wikilink generation:** `generate_wikilinks.py` runs on new notes only and adds cross-links to existing notes where unambiguous anchor phrases are found.
- [ ] **AC6 — Deduplication:** `dedup_notes.py --dry-run` runs after each ingestion; if similarity score ≥ 0.95, a dedup report is written to vault and a Discord alert is sent. Auto-deletion only triggers above 0.98.
- [ ] **AC7 — Single entry point:** A `maintain_vault.sh` (or `maintain_vault.py`) script orchestrates all the above steps in order with a `--scope [new|all]` flag.
- [ ] **AC8 — Cron integration:** The maintenance pipeline is registered as a Hermes cron job, runs nightly (e.g. 02:00 UTC), and delivers a brief summary to Discord (`#forge-log` or equivalent).
- [ ] **AC9 — Idempotent:** Running the pipeline twice on the same vault state produces no changes on the second run.

## Notes / Context
> Current state: all pipeline steps exist as separate scripts (`build_index.py`, `embed_vault.py`, `generate_wikilinks.py`, `dedup_notes.py`, `check_frontmatter.py` — last one to be created). They run manually. This story wires them into a single automated pipeline.
>
> Incremental indexing approach: store a `last_indexed` timestamp or commit SHA in `~/.hermes/vault_index/checkpoint.json`. On each run, compare against vault file mtimes or `git diff --name-only` to get the changed file list.
>
> RAM constraint: VPS has 7.7GB. Full re-embed of 1,270 notes took ~30s. Incremental runs should be <5s for typical daily additions.

## Dependencies
- **Blocks:** US-051, US-052, US-053 (all depend on vault always being fresh)
- **Blocked by:** US-008 ✅ (pipeline scripts exist)

## Definition of Done
- [ ] `maintain_vault.py` (or `.sh`) implemented and tested on a dry run with 3 new synthetic notes
- [ ] Incremental FTS and embedding update confirmed (not full rebuild)
- [ ] Cron job registered and first nightly run logged
- [ ] Discord summary delivered after successful run
- [ ] Script committed to `HermesForge/scripts/` and documented in vault
