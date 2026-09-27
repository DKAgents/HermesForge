# MIG-10: Move 07-Risk → trading/risk

**Date**: 2026-09-27

**Moved**: `07-Risk/` → `trading/risk/` (ESCALATION_CRITERIA, Governance, GUARDIAN_DECISIONS, HYPERLIQUID_WALLET, INCIDENT_LOG, POSITION_SIZING, RedTeam, RISK-MOC, RISK_RULES).

**Scripts updated** (10):
- `scripts/build_index.py` — `VAULT_DIS` entry
- `scripts/embed_vault.py` — `VAULT_DIS` entry
- `scripts/check_frontmatter.py` — `SCAN_DIS` entry + string check
- `scripts/extract_lessons.py` — list entry
- `scripts/maintain_vault.py` — `VAULT_DIS` entry
- `scripts/dedup_notes.py` — `VAULT_DIS` entry
- `scripts/governance/validate_handoff.py` — `LOG_PATH` absolute path
- `scripts/vault_connection_weaver.py` — docstring reference
- `scripts/validate_strategy.py` — list entry
- `scripts/discover_connections.py` — verified: no reference to 07-Risk

**Not moved**: `06-Strategies`, `08-Knowledge`, `09-Journal`.

**Rollback**: `git revert` of this commit.