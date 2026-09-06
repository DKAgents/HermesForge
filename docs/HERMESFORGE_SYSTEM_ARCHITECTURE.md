# HermesForge — Complete System Architecture

> Generated 2026-09-06. For use by high-reasoning LLMs to understand the full
> operational structure and identify optimization opportunities.

---

## 1. OVERARCHING GOALS

HermesForge is a fully automated paper-trading research pipeline operated by
Dan Keseloff at DX Foundation. The system runs on a single VPS (8 GB RAM, 240
GB SSD) in UTC timezone.  All user-facing content is Pacific Time (PT/PT
display).  Code is hosted at `github.com/DKAgents/HermesForge` and pushed
daily.

**Primary goals:**
- Discover, code, backtest, and deploy trading strategies autonomously
- Run paper-trading simulations with exit alerts, cross-posted to Discord
- Generate daily market intelligence briefings
- Self-maintain: vault health, connection discovery, cron watchdog, git push
- Manage risk through swarm governance (ADR-001 model tiering, Risk Guardian)
- Produce LinkedIn content in Dan Keseloff's voice (consulting practice)

**Hard constraints:**
- Vault files remain on VPS, accessed via Obsidian skill
- All timestamps displayed in Pacific Time; UTC used for computation
- API keys/tokens/credentials NEVER appear in code, commits, or output
- The 12-profile swarm governs all code changes. Publisher agent owns all
  embed/alert/template/publishing code exclusively.
- No trade executes against a live account without explicit user approval
- Max single-position risk: 1% of capital (Risk Guardian hard limit)
- Active strategies: 7 (STR-A/B/D/I/Q/L/V) plus 1 pipeline-scanner (STR-P)

---

## 2. HERMES AGENT & MODEL TIERS

### Hermes Version
- **Current:** v0.20.6 (upgraded from v0.20.3 on 2026-08-30)
- **Key features enabled:** `max_concurrent_children=10`, `max_iterations=250`,
  cron `request_overrides` auto-forward (no manual pinning since 0.20.6+)

### Model Tier System (ADR-001)

| Tier | Model | Cost/Mtok | Usage |
|------|-------|-----------|-------|
| **T1** | `claude-opus-4.8` | $5/$25 | Escalation only — 10 concrete triggers. Safety valve, never routine. |
| **T2** | `deepseek/deepseek-v4-pro` | $0.41/$0.83 | Hard floor for code changes (coder, architect, orchestrator). Vault Connection Weaver. |
| **T3** | `deepseek/deepseek-v4-flash` | $0.05/$0.11 | Bulk: all cron agents (research, publishing, performance). Estimated ~$22-27/mo total. |
| **T4** | — | — | (cheapest — not currently assigned) |

**T3 is the default for all automated cron work.**  T2 is required for any
code-modifying work.  T1 is pinned to specific `request_overrides` triggers
only (ADR-001 §2b) and has never been used in production.

**Pinning rule:** All LLM cron jobs MUST be pinned to a specific model.
Unpinned jobs fail-closed.  `deepseek/deepseek-v4-pro` requires
`max_tokens >= 800` for reasoning-capable models.

---

## 3. SWARM GOVERNANCE (12 PROFILES)

Every code change routes through the swarm.  The orchestrator delegates tasks
to specialists following ADR-001 tier floors.

| Profile | Role | Model Floor |
|---------|------|-------------|
| **orchestrator** | Coordinate Forge Loop, prioritize backlog, delegate to specialists | T2 |
| **architect** | Design technical architecture, evaluate trade-offs | T2 |
| **coder** | Implement features, fix bugs, write tests | T2 |
| **publisher** | SOLE OWNER of embed/chart/alert/template code (9 files) | T2 |
| **risk-guardian** | Review all trading logic, enforce 1% cap, veto power | T2 |
| **researcher** | Market research, strategy discovery, data analysis | T2/T3 |
| **backtester** | Phase-1A/B and walk-forward validation of strategies | T2 |
| **documenter** | Maintain Obsidian vault knowledge graph | T3 |
| **product-owner** | Backlog grooming, story prioritization | T3 |
| **red-team** | Adversarial review — try to break strategies | T2 |
| **trading** | General-purpose trading assistant (consumer) | T3 |
| **consulting** | General-purpose consulting assistant | T3 |

**Publisher agent governance (2026-08-23):** All embed/alert/template/publishing
code changes MUST route through the publisher agent.  No exceptions.  This
prevents ad-hoc changes to post formats, chart templates, or Discord embed
structures.  The publisher owns 9 files as sole authority.

**Risk Guardian governance:** The Risk Guardian has veto power on any
position-sizing or risk-parameter change.  Its hard rule (1% max per position)
cannot be overridden by instruction — it requires a principal-signed ADR
amendment.  Formalized via US-121 (currently blocked pending evidence).

---

## 4. 21 CRON JOBS — THE FULL WORKFLOW ENGINE

### Trading Pipeline (core loop)

| Job | Schedule | Agent? | What it does |
|-----|----------|--------|--------------|
| STR-Q Intraday Sweep | `*/5 * * * *` | no-agent | Detects liquidity sweeps on 35 crypto + 18 stocks, opens paper trades, monitors exits, posts exit alerts |
| Daily Signal Scanner | 14:45 daily | no-agent | Runs daily scanner (STR-A/B/D/I/L/V), posts setups to Discord |
| Paper Trading Capture | 14:50 daily | no-agent | Captures A/B/D signals into paper trading |
| Trade Monitor | every 60m | T3 agent | Checks open trades for ENTRY/STOP/TARGET/TIME events, posts alerts |
| Performance Report | 13:00 daily | T3 agent | Posts paper trading PNL with 1w/1m lookback |

### Strategy Pipeline (research → deployment)

| Job | Schedule | Agent? | What it does |
|-----|----------|--------|--------------|
| Autonomous Strategy Pipeline | Tue/Thu/Sun 17:00 | T3 agent | Reads staged edge candidates, critiques, codes scanners, backtests, validates, deploys |
| External Edge Discovery | Tue/Thu/Sun 16:00 | T3 agent | Runs edge_discovery_engine.py (14 scanners across 10 data feeds), stages candidates |
| Weekly Research Pipeline | Sunday 12:00 | T3 agent | Full research pipeline + heatmaps |
| Weekly Model Review | Monday 09:00 | T3 agent | Reviews model tier assignments, recommends changes |
| ADR-005 Rollout Check | Monday 14:00 | T3 agent | Checks readiness for governance rollouts |

### Market Intelligence

| Job | Schedule | Agent? | What it does |
|-----|----------|--------|--------------|
| Market Intelligence | Mon-Fri 13:00 | T3 agent | Produces daily briefing → `#daily-market-briefing` |
| Connection Discovery | Daily 04:00 | T3 agent | Runs vault connection weaver (semantic wikilink creation) |
| Vault Connection Weaver | every 240m | T2 agent | Creates high-signal wikilinks in Obsidian vault |

### Infrastructure

| Job | Schedule | Agent? | What it does |
|-----|----------|--------|--------------|
| Vault Maintenance | Daily 02:00 | T3 agent | Vault health checks, broken frontmatter fixes, cron output purge (14-day) |
| Daily Git Push | Daily 03:00 | no-agent | Pushes HermesForge commits to GitHub |
| Webhook Crosspost | `*/5 * * * *` | no-agent | Crossposts bot messages from 8 source channels to follower server webhooks |
| Cron Watchdog | `*/15 * * * *` | no-agent | Python script: checks job health, STR-Q freshness, daily scanner completion — webhook alert on failure only |

### Content

| Job | Schedule | Agent? | What it does |
|-----|----------|--------|--------------|
| LinkedIn Post Generator | Tue/Thu 05:30 | T3 agent | Writes LinkedIn post in Dan's voice, posts to Discord for manual crosspost |
| STR-Q Position Size Re-eval | Monday 09:00 | T3 agent | Weekly evidence check for US-121 — stays SILENT until conditions met |

---

## 5. TRADING STRATEGIES (ACTIVE)

### Daily Swing Strategies

| Strategy | ID | Scanner | Entry | Notes |
|----------|-----|---------|-------|-------|
| STR-A Ma Pullback Fibonacci | STR-A-ma-pullback-fibonacci | `scanner_a_daily.py` | Daily bars, multi-asset | Pullback to MA + fib level |
| STR-B MACD Histogram Divergence | STR-B-macd-histogram-divergence | `scanner_daily.py` | Daily, stocks + crypto | MACD divergence on daily bars |
| STR-D SR Role Reversal | STR-D-sr-role-reversal | `scanner_daily.py` | Daily | Support/resistance role reversal |
| STR-I Adaptive Trend | STR-I-adaptive-trend | `scanner_daily.py` | Daily | Trend-following with momentum filters |
| STR-L ATR Contraction | STR-L-atr-contraction | `scanner_daily.pyy` | Daily | Volatility contraction patterns |

### Intraday (Day Trading)

| Strategy | ID | Scanner | Entry | Notes |
|----------|-----|---------|-------|-------|
| STR-Q Liquidity Sweep | STR-Q-liquidity-sweep | `detect_liquidity_sweeps.py` | 5m bars, 35 crypto + 18 stocks | Quality score v4, CONF_BARS=2, 3:1 R:R |

### Cross-Sectional / Rotational

| Strategy | ID | Scanner | Notes |
|----------|-----|---------|-------|
| STR-P Crosssectional | STR-P-crosssectional | `scanner_pipeline.py` | Monthly rebalance, momentum ranking |
| STR-VVIX Contango Breakout | STR-VIXC-vix-contango-breakout | `scanner_daily.py` | VIX term structure |

---

## 6. DICORD CHANNELS & CROSSPOSTING

### Source Server Channels (DKAgents)

| Channel | ID | Purpose |
|---------|-----|---------|
| `#stock-setups` | `1528555538848153640` | Daily swing stock entries |
| `#crypto-setups` | `1528555885310513213` | Daily swing crypto entries |
| `#daily-market-briefing` | `153202005354820328` | Market intelligence briefing |
| `#strategy-status` | `153333248564199836` | Strategy status updates (no publisher currently) |
| `#strategy-research` | `1534834809451450409` | Edge discovery, strategy pipeline output |
| `#paper-trading` | `1537225420120793088` | Performance reports, trade entries |
| `#day-trade-crypto` | `1540951134200402071` | STR-Q crypto entries + exits |
| `#day-trade-stocks` | `1540951208028803142` | STR-Q stock entries + exits |

### Crossposting (Follower Server)

Every 5-minute cycle (`crosspost_webhook_all.sh`): scans all 8 source channels
for bot messages from the last 24h that haven't been crossposted yet (state
file at `/root/.hermes/crosspost_state.json` prevents duplicates).  Forwards to
follower server via `CROSSPOST_WEBHOOK_{CHANNEL_ID}` environment variables in
`.env`.  Webhook URLs verified live — all return HTTP 200.

---

## 7. DATA FEEDS

### Active (14 sources used by edge discovery engine)

| Feed | File | Data |
|------|------|------|
| Fear & Greed | `fetch_fear_greed.py` | Crypto sentiment (0-100) |
| VIX / Regime | `regime_filter.py` + `fetch_macro.py` | VIX, DXY, yields, SPY, breadth |
| DeFiLlama TVL | `fetch_defillama.py` | Chain-level TVL (daily) |
| Stablecoin Supply | `fetch_stablecoin_supply.py` | USDT/USDC/DAI aggregate (daily) |
| Put/Call Ratio | `fetch_put_call_ratio.py` | Equity PCR, regime |
| SEC Insider | `fetch_sec_insider.py` | Insider transactions |
| Economic Calendar | `fetch_economic_calendar.py` | High-impact events |
| GitHub Activity | `fetch_github_activity.py` | 10 crypto repos, weekly |
| Hyperliquid Metrics | `fetch_hyperliquid_metrics.py` | Funding rates, OI per coin |
| Crypto Onchain | `fetch_crypto_onchain.py` | BTC dominance, altcoin season |
| Short Interest | `fetch_short_interest.py` | yfinance (FINRA broken) |
| Earnings Calendar | `fetch_earnings_calendar.py` | High-vol clusters |
| Intermarket | `fetch_intermarket.py` | VIX term structure, DXY, gold/oil |
| Reddit Sentiment | `fetch_reddit_sentiment.py` | Auth-gated — returns empty |

### Price Data

- **Stocks:** yfinance daily + Alpaca intraday (5m, free tier 200 calls/min)
- **Crypto:** Hyperliquid API for both daily + intraday 5m
- **Cache:** Parquet files in `~/.hermes/market_data/`
- **Unified provider:** `scripts/data/intraday_provider.py` routes by asset_class

---

## 8. PAPER TRADING ARCHITECTURE

### Trade Lifecycle

```
Sweep Detector (5m)
  → monitor_exits()   — check stop/target/time
  → _post_exit_alert() — Discord exit notification
  → capture()        — scan for new sweeps
  → _process_sweeps() — open_new_trades in trade_log.py

Trade Monitor (60m)   — separate path for swig strategies
  → check_enty()      — pending trades reaching enty price
  → check_exit()      — entered trades hitting stop/target/time
  → _post_alert()     — Discord notification
```

### Trade Log (`trades.csv`)

**Atomic write protection (2026-09-06):** `_write_all_rows()` now:
1. Writes to temp file first
2. fsync to disk
3. Verifies row count matches
4. Atomic rename over original
5. REFUSES write if row count would drop >20% or to 0 rows → raises ValueError
6. Original file never truncated before new write is confirmed

**Dedup:** `performance_repport.py` deduples by `signal_id` before computing PNL.
374 duplicate rows removed (21% inflation). 1,384 unique STR-Q signals recovered.

### Current State (as of 2026-09-06)

trades.csv was truncated on approx Sep 6 — only 139 rows remain (all from
today).  Sep 1-5 data lost.  No backup covered that window.  The atomic write
fix ensures this cannot recur.  The 7-day/30-day PNL reports will be
undereweighted until the evidence base rebuilds naturally.

---

## 9. ACTIVE GOVERNANCE DOCUMENTS

| Doc | Location | Status |
|-----|----------|--------|
| **ADR-001** (Model Tiers) | `01-System/ADR/ADR-001-model-tiers.md` | Live — T1 unused, T2 code floor, T3 default |
| **US-121** (STR-Q Position Size) | `02-Backlog/Stories/US-121-STR-Q-Position-Size-Reevaluation.md` | Blocked — needs 200+ OOS trades + principal ADR |
| **US-120** (Advanced Options) | `02-Backlog/Stories/` | Deferred to 2026-09-02 |
| **US-111** (Portfolio Risk) | Deployed — record_stop_loss() circuit breaker |
| **LinkedIn Post Generator Skill** | `docs/LINKEDIN_POST_GENERATOR_SKILL.md` | 365-line Claude-importable reference |

---

## 10. CURRENT KNOWN ISSUES & IMPROVEMENT CANDIDATES

### Resolved (recent)

- ✅ Webhook crosspost: all 8 channels crossposting every 5 min (state-file idempotent)
- ✅ Cron Watchdog: moved to no-agent Python, silent by default, webhook alert on failure
- ✅ Quality score v4: deduped level weights, bad hours filter dropped (t=1.04, p>0.05)
- ✅ Trade log atomic writes: temp → validate → rename, refuses >20% drop
- ✅ PNL dedup: signal_id-based, 374 duplicate rows removed
- ✅ STR-Q exit alerts: posting STOP/TARGET/TIME to Discord
- ✅ 1-week + 1-month PNL lookback in perforance report
- ✅ Edge Discovery: 14 scanners wired (onchain, earnings, intermarket added)
- ✅ Data feeds: 10 orphaned feeds wired into pipeline
- ✅ Git daily push + remote backup (235 commits caught up)

### Pending

- � Daily Signal Scanner: `portfolio_publish.py` posts embeds, but swig trade exits
  trail on Trade Monitor only.  No duplicate posting issue, but exit alerts
  lag up to 60 minutes for swing trades.
- ⚠️ `#strategy-status` channel: no cron job publishes here.  Channel exists,
  webhook configured, but no content source.
- ⚠️ F&G data stale (last updated Aug 31) — Sep 1-6 missing.  Prevents regime
  analysis for the current window.  Needs a daily fetch cron job.
- ⚠️ Performance Report: runs daily at 13:00 but could be more frequent
  (e.g., every 4 hours) given the 5-min sweep cadence and the recent data loss.

### Optimization Candidates (for high-reasoning LLM)

1. **Daily git push + crosspost could be unified** — one cron that runs the pipeline
   then commits + pushes + crossposts in sequence.  Currently 3 separate jobs.
2. **Trade Monitor (60m) vs Sweep Capture (5m)** — two separate exit paths.
   Sweep Capture closes STR-Q trades AND posts alerts now.  Trade Monitor
   handles swing exits but can't see STR-Q trades (uses daily parquet not
   intraday).  Could be unified.
3. **Performance report could self-heal from trades.csv backups** — the atomic
   write now includes verification.  A companion cron that rotates daily
   snapshots would provide long-term recovery.
4. **F&G fetch is not in cron** — needs a daily fetch job so regime
   analysis stays current.  The fetch script exists and works.
5. **Strategy pipeline 0% success rate** — in its last run it rejected all 3
   candidates correctly, but never shiped anything.  The pipeline works as a
   filter, not a generator.  Consider adding a "seed candidate" step that
   proactively proposes ideas rather than only filtering.
6. **Vault Connection Weaver cost** — runs on T2 (deepseek-v4-pro) every 4 hours.
   Could potentially run on T3 in batches with similar quality.
7. **Monthly cost ~$22-27 at T3 rates** — mostly LinkedIn posts, market
   briefings, and research pipelines.  Could trim cadence or length of
   prompts for marginal savings.