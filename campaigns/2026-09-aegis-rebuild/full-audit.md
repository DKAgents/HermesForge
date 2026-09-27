# Full Audit — HermesForge System State

**Date**: 2026-09-27
**Scope**: read-only, no code/soul/cron/vault edits, no posts, no trades

---

## 1. Hermes Version, Gateway, Profiles

- **Hermes**: v0.21.2 (2026.9.11), upstream 9a60a7f3. 11,278 commits behind.
  Python 3.11.15. Update pulled but gateway not restarted — mixed modules warning.
- **Gateway**: `hermes-gateway.service` (systemd), enabled, running.
  Discord connector active (`DKAgents` server, guild `1500553453628428361`).

### Profile → Model mapping

Only the `default` profile specifies a model explicitly. All swarm sub-profiles
(`aegis-auditor`, `architect`, `backtester`, `coder`, `consulting`, `documenter`,
`orchestrator`, `product-owner`, `publisher`, `red-team`, `researcher`,
`risk-guardian`, `trading`) inherit their model from the default or from
override configuration at delegation time.

| Profile | Model | Gateway | Purpose |
|---|---|---|---|
| `default` | deepseek/deepseek-v4-pro | running | Primary chat agent |
| `aegis-auditor` | anthropic/claude-opus-4.8 | stopped | Audit agent (T2) |
| `red-team` | deepseek/deepseek-v4-flash | stopped | Adversarial testing (T3) |
| All others (10 profiles) | — (inherit default) | stopped | Swarm specialists |

Model routing: OpenRouter (`openrouter` provider), key from
`OPENROUTER_API_KEY` env. Pricing: T2=v4pro $0.41/0.83, T3=v4-flash $0.05/0.11.

Profiles on disk: `/root/.hermes/profiles/{aegis-auditor,architect,backtester,
coder,consulting,documenter,orchestrator,product-owner,publisher,red-team,
researcher,risk-guardian,trading}/` — 13 profile directories.

---

## 2. Scheduled Jobs (Cron)

User crontab is empty. The real scheduler is **Hermes cron** (`hermes cron`),
stored in `/root/.hermes/cron/jobs.json`.

| Job ID | Name | Schedule | Script | Last |
|---|---|---|---|---|
| `73a9a8ecba59` | Forge Edition Sync | daily 02:00 | `forge_edition_sync.sh` | ok? |
| `3f49a07a2f04` | Daily Publish (v4-flash) | daily 14:47 | `daily_publish_wrapper.sh` | ok |
| `b0e6961eea8d` | x-strategy-scout [T3] | daily 02:00 | `scout_x_wrapper.py` | ok |
| `5041c3c5103f` | Hostile Fill Report | daily 22:00 | `hostile_fill_report_daily.sh` | ok |
| `61cccd31ed5c` | Crosspost Signals | daily 14:49 | `crosspost_webhook_all.sh` | ok |
| `65dfc591efad` | Strategy Status Watchdog | daily 00:00 | `cron_watchdog.py` | ok |
| `cb22b038a6d6` | Performance Report | daily 13:00 | `post_performance_report.sh` | ok |
| `232975d5fc83` | Connection Discovery | daily 22:00 | `discover_connections.py` | ok |
| `e214a9d8f348` | External Edge Discovery | daily 22:00 | `external_edge_discovery.sh` | ok |
| `e5542799dfe4` | Edge Factory [T3] | daily 00:00,04:00,08:00,12:00,16:00,20:00 | `edge_factory.py` | ok? |

All scripts live under `/root/.hermes/scripts/`.

---

## 3. Second Brain — Top-Level Folders

### Numbered vault (Obsidian — 00–10)

| Folder | Purpose | Readers |
|---|---|---|
| `00-Meta/` | Project meta, cross-cutting index | Orchestrator, Documenter |
| `01-Agents/` | Agent profiles/souls (`Profiles/`) | All agents (self-reference) |
| `01-System/` | System configuration docs | Orchestrator |
| `02-Backlog/` | User stories, epics, ADR stories | Orchestrator, Product Owner |
| `03-ADRs/` | Architecture Decision Records | Architect, Orchestrator |
| `04-ForgeLoop/` | Forge loop outputs + `Discovery/` | Orchestrator, Documenter |
| `04-Strategies/` | Strategy notes (phase1a, T1, STR-Q variants) | Researcher, Backtester |
| `trading/proposals/` | Proposals (PROP-001 gauntlet) | Architect, Orchestrator |
| `05-Research/` | Research + `Strategy-Validation/` | Researcher |
| `06-Strategies/` | `Hypotheses/`, `Active/`, `Backtests/`, `Live/`, `Regimes/`, `Failure-Modes/`, `Deprecated/` | Researcher, Backtester, Coder (`capture_signals.py` reads `Hypotheses/`) |
| `07-Risk/` | Risk rules, incident log | Risk Guardian |
| `08-Knowledge/` | `Insights/`, `Learnings/`, `Skills/`, `Trading-Systems/`, MOC | Documenter, Researcher |
| `09-Journal/` | Trading journal | All |
| `10-Operations/` | Ops documentation | Ops |

### Un-numbered tree

| Folder | Purpose | Readers |
|---|---|---|
| `scripts/` | All executable code | All agents, crons |
| `tests/` | Test suite | Coder, CI |
| `docs/` | Documentation | All |
| `campaigns/` | Campaign working docs (LU series) | Orchestrator |
| `data/` | Data storage | Coder, Researcher |
| `reports/` | Report outputs | Crons |
| `Inbox/` | Capture inbox (unfiled notes) | Documenter |
| `Templates/` | Note/story templates | Documenter, Product Owner |
| `vault/` | Dead stub — 2 legacy research files | None active |
| `technical-analysis-of-the-financial-mark-murphy/` | Murphy book (knowledge graph source) | Knowledge graph ingestion |

### Scripts that read the vault

- `capture_signals.py` reads `06-Strategies/Hypotheses/` (strategy frontmatter)
- `discover_connections.py` reads `08-Knowledge/` and `06-Strategies/`
- `portfolio_publish.py` reads `06-Strategies/Hypotheses/` via scanner registry
- `jev_performance_tracker.py` reads `trades.csv` from `scripts/paper_trading/`
- `live_performance_tracker.py` reads `trades.csv` + `BACKTEST_EXPECTATIONS`
- `performance_report.py` reads `trades.csv` + `hostile_fill_report_strq.jsonl`

---

## 4. Trading Path — Full Chain

### Signal capture (daily)

1. `capture_signals.py` → `_discover_strategies()` reads `06-Strategies/Hypotheses/STR-*.md` frontmatter
2. `PAPER_STRATEGIES` built from `status ∈ {live, watch}` + `hostile_pass: true` gate (LU-06b)
3. `_scan_and_capture()` scans each strategy against cached OHLCV data
4. Jev prefilter (`jev_prefilter.prefilter_signal`) — 3 noul calls per signal
5. `trade_log.open_trade(trade_dict)` → writes `trades.csv`

### Signal capture (intraday sweeps)

1. `capture_sweep_signals.py` → fetches 5m bar data, detects liquidity sweeps
2. `_process_sweeps()` builds trade dicts per sweep
3. Jev prefilter — same gate, same 3 noul calls
4. `trade_log.open_trade()` → writes `trades.csv`

### Jev call sites (all)

| File | Call | Frequency |
|---|---|---|
| `jev_prefilter.py` → `prefilter_signal()` | 3 noul calls | Per signal (daily + sweep) |
| `jev_regime.py` → `classify_regime()` | 3 calls (2 score, 1 noul) | Imported but **never called** |
| `jev_client.py` | HTTP POST to `typesafe.ai/v1/systemone` | Per noul/score/choice |

### Hostile fill pipeline

1. `hostile_fill_report_daily.sh` (cron `5041c3c5103f`, 22:00 UTC)
2. → `hostile_fills.py` (swing trades) + `hostile_fills_strq.py` (STR-Q only)
3. Writes `hostile_fill_report_strq.jsonl` (12,674 records, append-only)

### Paper scoreboard

1. `post_performance_report.sh` (cron `cb22b038a6d6`, 13:00 UTC)
2. → `performance_report.py` → reads `trades.csv` + `hostile_fill_report_strq.jsonl`
3. Posts to `#paper-trading` (`1537225420120793088`)

### Kill card

1. `live_performance_tracker.py` reads `trades.csv`
2. Compares live stats against `BACKTEST_EXPECTATIONS` (hardcoded)
3. Flags divergence at 1.5σ → posts `🚨 Live Performance Tracker` embed
4. Does NOT reference hostile fill data

---

## 5. Secrets — File Paths Only

**NEVER INCLUDED**: actual key values, tokens, addresses.

### Active secrets store

- `/root/.hermes/.env` — mode 0600, 27KB, all secrets live here
- Read by: `jev_client.py` (`_load_api_key`), `connection_test.py` (`load_dotenv`),
  `intraday_provider.py`, `fetch_earnings_calendar.py`, `fetch_lunarcrush.py`,
  `liquidity_heatmap.py` (public data only, no keys), all Discord scripts
  (via `$DISCORD_BOT_TOKEN` env)

### Key names referenced in code

- `TYPESAFE_API_KEY` — Jev/TypeSafe API
- `OPENROUTER_API_KEY` — model routing
- `DISCORD_BOT_TOKEN` — all Discord posting
- `ALPACA_API_KEY` / `ALPACA_API_SECRET` — stock intraday data
- `HYPERLIQUID_TESTNET_AGENT_ADDRESS` / `..._PRIVATE_KEY` — testnet wallet (key loaded but unused)
- `FINNHUB_API_KEY` — earnings calendar
- `LUNARCRUSH_API_KEY` — crypto social data
- `GITHUB_TOKEN` — repo operations

### Stale secrets on disk

- `/root/HermesForge/.env` — 1-line placeholder (tracked in git — not the real secrets)
- `/root/HermesForge/.hermes/.env` — may exist, refer to `~/.hermes/.env` above

---

## 6. Git State

- **Branch**: `main`
- **Unpushed commits**: 17 (most recent: `3179b4b9` "fix(LU-03b): hostile line includes
  record count, date range, frozen scoreboard")
- **`.env` in `.gitignore`**: NO — not listed in `.gitignore`
- **Is `.env` tracked?**: YES — `/.env` is in the index (1-line placeholder, not the real secrets)
- **Real secrets** (`/root/.hermes/.env`): NOT in the repo, mode 0600
- **Risk**: if the 1-line `.env` accidentally accumulates real keys in the repo root,
  they would be committed and pushed. The `.gitignore` does not protect against this.

---

## 7. Broken or Colliding Paths

### Number collisions

| Pair | Conflict |
|---|---|
| `04-ForgeLoop/` vs `04-Strategies/` | Both claim "04" — process output vs trading ideas |
| `trading/proposals/` vs `05-Research/` | Proposals vs research (now separated) |
| `06-Strategies/Hypotheses/` vs `06-Strategies/Active/` | `Active/` is a ghost — 4 files with `status: active` but never used by any scanner |

### Dead paths

- `vault/` — only `vault/research/research-2026-08-{06,09}.md` (2 legacy files)
- `06-Strategies/Live/` — empty directory
- `04-Strategies/` — strategy notes that overlap with `06-Strategies/` purpose
- `technical-analysis-of-the-financial-mark-murphy/` — raw book, ingested to knowledge graph, not a vault directory

### Double-frontmatter hypothesis files

Five files have two YAML blocks — `status` lives in the second block. The
`_discover_strategies()` loader only reads the first block, so these are
silently skipped:

- `STR-20260719-sr-role-reversal-entry.md` (STR-D)
- `STR-20260726-first-pullback-trend-swing.md`
- `STR-20260728-adaptive-trend.md` (STR-I)
- `STR-20260730-atr-contraction-breakout.md`
- `STR-20260801-crosssectional-factor.md` (STR-P)

This means **STR-I and STR-D never reach the scanner** regardless of their
`status` field — a silent drop caused by the frontmatter format, not by
any gate.

### T1 strategies gated but present

Three STR-T1-* files exist in `Hypotheses/` with `status: watch` but no
`hostile_pass: true`. They are blocked by both the T1 gate (env
`HERMESFORGE_T1_ENABLED` unset → default OFF) AND the LU-06b hostile_pass
gate. Double-gated.

### Scripts that claim 04- or 05- without disambiguation

- `post_heatmaps.py` references just `#paper-trading` channel — no collision
- `performance_report.py` doesn't distinguish 04-ForgeLoop from 04-Strategies;

---

## Summary of Critical Findings

1. **Gateway stale**: update pulled but not restarted — mixed sys.modules.
2. **Double frontmatter**: STR-I (adaptive-trend) and STR-D (sr-role-reversal)
   silently dropped by the loader due to dual YAML blocks — not by any gate.
3. **`.env` in git index**: the repo-root `.env` is tracked, though it's a
   1-line placeholder. No `.gitignore` protection.
4. **Number collisions**: `04-ForgeLoop` vs `04-Strategies`, `trading/proposals/`
   vs `05-Research` — same prefix, different purposes.
5. **Secrets all in one file**: `/root/.hermes/.env` (0600) holds every key
   for the entire system. No vault, no encryption at rest.
6. **Performance report now cites hostile R** (LU-03b): `+1163R on 7661 rows,
   2026-09-09 to 2026-09-26` alongside frozen `-104R` scoreboard.
7. **STR-Q**: remains paper-only, not un-killed. Frozen scoreboard stands.