# MIG-16: Move 06-Strategies → trading/strategies

**Date**: 2026-09-27

**Moved**: `06-Strategies/` → `trading/strategies/` (00-Enhancement-Backlog, 00-Strategy-Index, Active, Backtests, Deprecated, Failure-Modes, Hypotheses, Live, Pending-Updates, Regimes).

**Scripts updated** (20):
- `scripts/check_frontmatter.py` — `SCAN_DIS` entry
- `scripts/cron/scout_x_wrapper.py` — `HYP_DIR`
- `scripts/dedup_notes.py` — `VAULT_DIS` entry
- `scripts/discord/daily_publish.py` — strategy loader path
- `scripts/discord/portfolio_publish.py` — scanner registry path
- `scripts/discover_connections.py` — strategy discovery path
- `scripts/extract_lessons.py` — strategy dir list
- `scripts/gauntlet/run_decay_check.py` — decay targets
- `scripts/maintain_vault.py` — `VAULT_DIS` entry
- `scripts/paper_trading/capture_signals.py` — `_discover_strategies()` + docstring comments
- `scripts/paper_trading/extract_lessons.py` — LESSONS DIR
- `scripts/validate_strategy.py` — strategy scan list
- `scripts/validation/edge_factory.py` — `HYP_DIR`
- `scripts/validation/phase1b_v2_walkforward.py` — strategy path
- `scripts/validation/run_phase1b_q.py` — strategy path
- `scripts/validation/scanners/scanner_h_first_pullback_trend_swing.py` — docstring
- `scripts/validation/scanners/scanner_vix_vrp_contango.py` — docstring
- `scripts/validation/scout_x_strategies.py` — `HYP_DIR`
- `scripts/validation/str_q_mae_mfe_analysis.py` — strategy path
- `scripts/vault_connection_weaver.py` — docstring

**Not touched**: `capture_sweep_signals.py` (verified no reference), strategy rules, STR-Q, hostile_pass flags.

**Rollback**: `git revert` of this commit.