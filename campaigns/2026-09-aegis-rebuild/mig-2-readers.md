# MIG-2: Vault Directory Readers

**Date**: 2026-09-27
**Status**: note-only — no file moves, no code edits

Every script under `scripts/` and `campaigns/` that opens or references these
eight numbered vault directories.

---

## 04-ForgeLoop

| Script | Path referenced | Operation |
|---|---|---|
| `scripts/discover_connections.py` | `04-ForgeLoop/Discovery/` | Writes weekly discovery reports |
| `scripts/maintain_vault.py` | `04-ForgeLoop/Maintenance/` | Writes maintenance logs |
| `scripts/validation/scout_x_strategies.py` | `04-ForgeLoop/` | Writes edge-discovery candidates |
| `scripts/validation/edge_factory.py` | `04-ForgeLoop/edge-factory-results/` | Writes cycle results |
| `scripts/validation/walk_forward_us114.py` | `04-ForgeLoop/AUDIT-backtester-US114.md` | Writes audit report |
| `scripts/cron/scout_x_wrapper.py` | `04-ForgeLoop/edge-discovery-candidates.txt` | Writes candidates file |

## 04-Strategies

| Script | Path referenced | Operation |
|---|---|---|
| `scripts/validation/run_phase1a_batch.py` | `04-Strategies/` | Reads phase1a results |
| (No other active readers — `full-audit.md` and `lu-08-vault-map.md` in `campaigns/` document this directory but do not execute against it) |

## 05-Proposals

| Script | Path referenced | Operation |
|---|---|---|
| (No active readers — only `full-audit.md` and `lu-08-vault-map.md` in `campaigns/` document it) |

## 05-Research

| Script | Path referenced | Operation |
|---|---|---|
| `scripts/check_frontmatter.py` | `05-Research/` | Validates frontmatter across vault |
| `scripts/research/edge_discovery_engine.py` | `05-Research/Edge-Candidates/` | Writes edge candidates |
| `scripts/research/hype_strategy.py` | `05-Research/Strategy-Validation/` | Writes STR-H validation results |

## 06-Strategies

| Script | Path referenced | Operation |
|---|---|---|
| `scripts/paper_trading/capture_signals.py` | `06-Strategies/Hypotheses/` | **Reads** strategy frontmatter to auto-discover active scanners |
| `scripts/discord/portfolio_publish.py` | `06-Strategies/Hypotheses/` | **Reads** frontmatter for strategy metadata |
| `scripts/discord/daily_publish.py` | `06-Strategies/Hypotheses/` | **Reads** frontmatter for daily signal generation |
| `scripts/validation/scout_x_strategies.py` | `06-Strategies/Hypotheses/` | Writes new HYP notes from X scouting |
| `scripts/validation/edge_factory.py` | `06-Strategies/Hypotheses/` | Writes HYP notes from edge factory |
| `scripts/discover_connections.py` | `06-Strategies/` | Reads strategy files for knowledge graph |
| `scripts/extract_lessons.py` | `06-Strategies/` | Reads strategy files for lesson extraction |
| `scripts/check_frontmatter.py` | `06-Strategies/` | Validates frontmatter across all strategy files |
| `scripts/cron/scout_x_wrapper.py` | `06-Strategies/Hypotheses/` | Writes new HYP notes |

## 07-Risk

| Script | Path referenced | Operation |
|---|---|---|
| `scripts/check_frontmatter.py` | `07-Risk/` | Validates frontmatter |
| `scripts/extract_lessons.py` | `07-Risk/` | Reads risk rules for lesson extraction |
| `scripts/discover_connections.py` | `07-Risk/` | Reads for knowledge graph |
| `scripts/maintain_vault.py` | `07-Risk/` | Maintenance scans |
| `scripts/governance/validate_handoff.py` | `07-Risk/` | Reads risk rules for handoff validation |
| `scripts/build_index.py` | `07-Risk/` | Builds vault index |
| `scripts/embed_vault.py` | `07-Risk/` | Embeds vault content |
| `scripts/dedup_notes.py` | `07-Risk/` | Deduplicates notes |

## 08-Knowledge

| Script | Path referenced | Operation |
|---|---|---|
| `scripts/discover_connections.py` | `08-Knowledge/Insights/` | Writes accepted insights |
| `scripts/maintain_vault.py` | `08-Knowledge/Trading-Systems/` | Reads Murphy book for maintenance |
| `scripts/check_frontmatter.py` | `08-Knowledge/` | Validates frontmatter |
| `scripts/extract_lessons.py` | `08-Knowledge/` | Reads for lesson extraction |
| `scripts/build_index.py` | `08-Knowledge/` | Builds vault index |
| `scripts/embed_vault.py` | `08-Knowledge/` | Embeds vault content |
| `scripts/generate_wikilinks.py` | `08-Knowledge/` | Generates wikilinks |

## 09-Journal

| Script | Path referenced | Operation |
|---|---|---|
| `scripts/extract_lessons.py` | `09-Journal/Lessons/` | Writes lesson notes |
| `scripts/paper_trading/extract_lessons.py` | `09-Journal/Lessons/` | Writes trading lessons |
| `scripts/check_frontmatter.py` | `09-Journal/` | Validates frontmatter |
| `scripts/maintain_vault.py` | `09-Journal/` | Maintenance scans |
| `scripts/dedup_notes.py` | `09-Journal/` | Deduplicates notes |

---

## The Five Known Readers — Confirmed or Dropped

| Script | Reads a vault dir? | Details |
|---|---|---|
| `capture_signals.py` | **YES** | Reads `06-Strategies/Hypotheses/` at line 193 via `_discover_strategies()` |
| `discover_connections.py` | **YES** | Reads `04-ForgeLoop/`, `06-Strategies/`, `07-Risk/`, `08-Knowledge/`; writes to `04-ForgeLoop/Discovery/` and `08-Knowledge/Insights/` |
| `jev_performance_tracker.py` | **NO** | Reads only `scripts/paper_trading/trades.csv` — zero vault directory references |
| `live_performance_tracker.py` | **NO** | Reads only `trades.csv` via `trade_log.LOG_PATH` — zero vault directory references |
| `performance_report.py` | **NO** | Reads `trades.csv` + `hostile_fill_report_strq.jsonl`, both under `scripts/paper_trading/` — zero vault directory references |

## Summary

- **14 scripts** read from one or more of the 8 numbered vault directories.
- **3 of the 5 "known" readers actually touch vault dirs** — `capture_signals.py` and `discover_connections.py` confirmed; `jev_performance_tracker.py`, `live_performance_tracker.py`, and `performance_report.py` do not (they read `trades.csv` only).
- The heaviest reader is `discover_connections.py` (4 vault dirs).
- `05-Proposals/` has zero active script readers — it exists only as a documentation bucket.
- `04-Strategies/` has only one active reader (`run_phase1a_batch.py`).
- `06-Strategies/` and `08-Knowledge/` are the most heavily read directories (9 readers each).