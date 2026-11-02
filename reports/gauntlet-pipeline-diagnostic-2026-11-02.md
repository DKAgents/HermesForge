# HermesForge Trading Strategy Pipeline — Diagnostic Overview

**Generated:** 2026-11-02 (UTC)
**Method:** read from live config (`~/.hermes/config.yaml`, `~/.hermes/cron/jobs.json`, `~/.hermes/cron/usage_audit.jsonl`), the Obsidian vault / ADRs, strategy registry, trials ledger, and live-trading source. No memory-based figures — every number below was pulled from a file/log this session.

---

## 1. ARCHITECTURE

### 1.1 Swarm agents (Hemes subagent profiles)

Profiles live under `/root/.hermes/profiles/` (13 specialized + default):

| Agent | Model tier (ADR-001) | OpenRouter model | Hard floor |
|---|---|---|---|
| orchestrator | T2 | `deepseek/deepseek-v4-pro-0813` | T2 |
| architect | T2 | `deepseek/deepseek-v4-pro-0813` | T2 |
| coder | T2 | `deepseek/deepseek-v4-pro-0813` | T2 |
| risk-guardian | T2 | `deepseek/deepseek-v4-pro-0813` | T2 |
| backtester | T3 | `deepseek/deepseek-v4-flash-0731` | T3 |
| researcher | T3 | `deepseek/deepseek-v4-flash-0731` | T3 |
| trading | T3 | `deepseek/deepseek-v4-flash-0731` | T3 |
| product-owner | T3 | `deepseek/deepseek-v4-flash-0731` | T4 |
| documenter | T4 | Gemini-Flash / MiniMax (cheap) | T4 |
| publisher | (T3) | per-cron `deepseek/deepseek-v4-flash-0731` | — |
| aegis-auditor | T1 | `anthropic/claude-opus-4.8` | T1 (safety valve only) |
| red-team | T3 | `deepseek/deepseek-v4-flash-0731` (pinned in its config) | — |
| consulting | (T2/T3) | inherits | — |

- **Default model** (`config.yaml`): `deepseek/deepseek-v4-pro-0813`, provider OpenRouter.
- **T1 is a safety valve, not a tier** — `claude-opus-4.8` ($5/$25 per M) fires only on 10 concrete escalation triggers (ADR-001 §2b). `aegis-auditor` is pinned to it.
- The two "unusual" profiles have explicit `config.yaml` model lines: `aegis-auditor` → `claude-opus-4.8`, `red-team` → `deepseek-v4-flash-0731`. All others inherit the default or route by ADR-001 tier.

### 1.2 How trading work requests code (dev-swarm handoff)

Per ADR-001 and the standing hard rule (memory): **all code changes route through the swarm, never directly by the orchestrator principal.** The flow is:

`human / orchestrator → route → architect (design) → coder (implement) → risk-guardian (adversarial review) → backtester (independent revalidation) → commit`

- Architect produces a spec (`02-Backlog/Specs/`), coder implements + commits path-scoped, risk-guardian reviews adversarially, backtester independently re-derives the edge. I (orchestrator) only commit path-scoped and file/route stories.
- Autonomous boundary (ADR-007): swarm routing, non-live T1 escalation, ADR drafting/committing, index/cron/model maintenance, audit dispatch are autonomous. Go-live, first real fill, `LIVE_TRADING_ENABLED`, kill-switch/size-cap changes, secrets, and `--force`/`>20%` overrides are human-gated.

### 1.3 Scheduled jobs (cron)

**38 cron jobs** registered (`~/.hermes/cron/jobs.json`). Full inventory with schedules:

**Agents (no_agent=False, LLM-driven, mostly pinned `deepseek-v4-flash-0731`):**
- CRON-001 Market Intelligence — 13:00 Mon–Fri
- HermesForge Autonomous Strategy Pipeline — 17:00 daily
- Paper Trading Performance Report — 13:00 daily
- Auto-Crosspost Daily Briefing — 13:05 Mon–Fri
- Connection Discovery — 04:00
- External Edge Discovery — 16:00 Tue/Thu/Sun
- Weekly Research Pipeline — 12:00 Sun
- Vault Maintenance — 02:00
- decay-watch — 14:00 daily
- STR-Q Position Size Re-eval — 09:00 Mon
- Weekly Model Assignment Review — 09:00 Mon
- ADR-005 Rollout Readiness — 14:00 Mon
- Trade Monitor triage — interval
- Vault Connection Weaver — interval

**no-agent script jobs (majority, incl. all data ingests):**
- Cron Watchdog — `*/15 * * * *`
- Data ingests (Hyperliquid bars 13:10, funding 13:15, assetCtx hourly `0 * * * *`, OKX liquidation `*/5`, Deribit IV `15 * * * *`, equity IV 21:00, cross-venue basis `30 * * * *`)
- STR-Q Intraday Sweep Capture — `*/5 * * * *`
- Paper Trading Capture (A/B/D) — 14:50
- Daily Signal Scanner → Publisher — 14:45
- Webhook Crosspost — `*/5`
- Daily Git Push — 03:00; Hostile Fill Report — 22:00; Edge Factory — `0 */4 * * *`
- x-strategy-scout — 02:00; polymarket-feed — 12:30
- Various maintenance (chart purge, F&G fetch, journal snapshot, restore drill, system doctor, confidence digest)

System crontab additionally runs `hermes-git-sync` every 15 min (now routed through the shared `git_commit_paths` flock, US-184).

---

## 2. DATA

| Venue | Endpoint / feed | Fields | Granularity | History depth | Refresh |
|---|---|---|---|---|---|
| Hyperliquid | `candleSnapshot` → `hl_bar_store` (`bars_5m.db`, `bars_1d.db`) | OHLCV | 5m, 1d | 5m ~17-day retention; 1d ~4yr via direct fetch (deep backtest), store seeds forward | 13:10 daily (1d), + 5m |
| Hyperliquid | `fundingHistory` → `hl_funding_store` | hourly funding APR | hourly | ~90d backfill, accumulating | 13:15 daily |
| Hyperliquid | `metaAndAssetCtxs` → `hl_assetctx_store` | markPx, oraclePx (real basis), openInterest (total only), day_ntl_vlm, prev_day_px | snapshot | accumulating forward (no history endpoint → real basis gated ~weeks) | hourly |
| OKX (proxy) | `funding-rate`, `ticker`, `liquidation` | HL↔OKX funding spread + price basis; liquidation events | hourly / 5-min poll | ~90d funding backfill; liq forward | 30-min / `*/5` |
| Deribit | `get_volatility_index_data` (DVOL) + options chain `mark_iv` | DVOL index, ATM IV term structure | hourly | ~30d (just began) — GATED | `15 * * * *` |
| Equities | Alpaca (data), yfinance option_chain | OHLC parquet; ATM impliedVol → IV rank | 5m / daily | multi-year parquet; IV forward | daily |
| Polymarket | market feed | macro/political market prices | event | forward | 12:30 |

**Flagged but not (fully) implemented:**
- Hyperliquid exposes **no public liquidation feed** and **no long/short OI split** (verified live — websocket rejects `liquidation`; `metaAndAssetCtxs` gives total OI only). OI-delta quadrant (`oi_delta.py`) is the derived proxy; liquidations come from OKX cross-venue proxy. HL-native funding/positioning granularity would need Coinglass (paid) or a persistent listener.
- **Binance / Bybit are 403** (blocked) — cross-venue basis is HL↔OKX only.
- `.env` contains `LUNARCRUSH_API_KEY` (a social/alt-data key present but no confirmed active ingestion cron in the 38 jobs).

---

## 3. HYPOTHESIS GENERATION

**How seeds are created:**
- Pre-registered seed pool (`PROP-001` §01): 10 hypotheses HYP-01…HYP-10 (verbatim below).
- Vault-to-hypothesis (edge-condition → falsifiable hypothesis).
- External edge discovery (cron, Tue/Thu/Sun) + x-strategy-scout (X/Twitter) + Weekly Research Pipeline + Edge Factory (`0 */4 * * *`).
- Conditional-edge mining grid (6 primitives × 4 regimes × 3 funding × 4 OI = 288 cells) — planned, partially built.
- Every backtest writes to the trials ledger exactly once; pre-registration is required before a result is valid.

**Seed pool (HYP-01…HYP-10, verbatim from PROP-001):**
1. **HYP-01** Swing 4–48h — *Funding-extreme unwind* (fade crowded positioning when funding >95th %ile + OI rising). Tier T3 — killer G6.
2. **HYP-02** Intraday 5m — *OI-confirmed breakout* (price↑/OI↑ new-money quadrant). T2 — G3.
3. **HYP-03** Intraday 5m — *Cascade exhaustion* (post-liquidation-cascade retrace). T3 — G2 look-ahead.
4. **HYP-04** Intraday 5m — *Settlement-hour drift*. T3 — G0 cost.
5. **HYP-05** Swing 1–7d — *Cross-sectional perp momentum* (long top / short bottom decile, funding filter). T1 — G6 clustering.
6. **HYP-06** Intraday 5m–4h — *BTC-beta residual reversion*. T2 — G0 two-leg cost.
7. **HYP-07** Intraday 5m — *Asia-range / EU-continuation*. T2 — G5 trials.
8. **HYP-08** Intraday 5m — *Oracle-mark dislocation snap-back*. T3 — G0 capacity.
9. **HYP-09** Swing 1–5d — *Volatility compression expansion*. T1 — G4 stability.
10. **HYP-10** Swing 1–14d — *New-listing drift* (persistent funding skew + drift). T1 — G5 sample.

**20 most-recent strategy hypotheses in the registry** (`trading/strategies/Hypotheses/`, by mtime — freeform notes, no structured asset/timeframe frontmatter):
1. STR-2026-09-20 ran-every-valid-crt-setup-across-fx-majors-indices-and-gold
2. STR-2026-09-22 ran-every-valid-crt-setup… (repeat)
3. STR-2026-09-20 buy-when-ema20-crosses-above-ema50-with-price-above-ema200
4. STR-2026-10-04 one-setup
5. STR-20260818 lowcorr-regime
6. STR-2026-09-27 fosl-signal-triggered
7. STR-2026-09-27 xmtr-signal-triggered
8. STR-2026-09-26 fosl-signal-triggered
9. STR-2026-09-26 xmtr-signal-triggered
10. STR-2026-09-22 i-gave-horizon-a-simple-sol-4h-setup
11. STR-20260920 triple-rsi-mean-reversion
12. STR-20260920 wintermute-mm-pattern
13. STR-20260920 liquidity-sweep-wide
14. STR-20260917 CAP-BOTTOM
15. STR-20260730 breadth-gated-gap-reversal
16. STR-20260726 selling-climax-reversal
17. STR-T1-02 adx-trend-pullback
18. STR-T1-03 gap-continuation
19. STR-T1-01 outside-day-key-reversal
20. STR-20260726 eufearia-cci-reversal

*(These are short freeform `.md` notes — hypothesis_id in the trials ledger is the canonical registration; the notes mostly lack `asset_class`/`timeframe`/`holding_period` frontmatter.)*

---

## 4. GATE CONFIG (G0–G7)

Cost model (G0): Hyperliquid base perp tier **4.5 bps taker / 1.5 bps maker**; all-in round-trip taker **~11–13 bps** (crypto 12 bps corrected dynamic split; stock ~3 bps). Gross capture ⇒ **≥45 bps** (4× cost).

| Gate | Test | Pass criteria |
|---|---|---|
| G0 | Cost & capacity pre-screen | median \|move\| ≥ 4× all-in cost · clip ≤ 4% top-5 depth · gross ≥ 45 bps (taker) |
| G1 | Signal scan (liquidity-filtered) | ≥200 signals across ≥15 symbols · 30d median 5m notional ≥ $250k · top-5 depth ≥ $50k within 10 bps |
| G2 | Leakage audit | L1–L3 green · funding/OI accessed only with realistic lag · delay-one-bar edge decay < 50% |
| G3 | Execution realism | realistic ≥ 60% of optimistic avg R · pessimistic PF > 1.0 · slippage monotonic in clip. **MANDATORY + fail-closed for promotion** |
| G4 | CPCV | N=12 groups, k=2 → 66 splits, 11 reconstructed paths · purge by holding horizon · median split PF ≥ 1.3 · 10th-%ile split PF ≥ 1.0 · block-bootstrap p < 0.05 |
| G5 | Multiple-testing | DSR > 0.95 · PBO < 0.30 |
| G6 | Robustness | non-negative in ≥3 of 4 regimes · present in ≥2 of 3 BTC-beta clusters · no symbol >35% P&L · no month >40% |
| G7 | Forward validation | ≥100 trades or 30 sessions · realised slippage ≤ 1.5× modelled · live avg R ≥ 50% CPCV median |

- **Sensitivity ranges / regime definitions:** 4 regimes (bull/bear/neutral via BTC realised-vol percentile + TF alignment), 3 funding states, 4 OI quadrants, 3 BTC-beta clusters, session partition (Asia/EU/US). Directional funding gate λ sensitivity 0.25/0.50/1.00 (funding must exceed λ·realized-vol).
- **CPCV folds:** N=12, k=2 (fixed).
- **Retirement (pre-registered kill rules):** trailing-100 PF < 1.15, or trailing-20 avg R < 0 twice, or realised slippage >2× modelled for 20 trades → Active → Hypotheses.

---

## 5. FUNNEL

**Factual state — there is no single maintained per-gate funnel tally.** The gate results are spread across the trials ledger, the strategy-registry folder status, and per-strategy reports. Raw counts actually on disk:

| Stage / source | Count |
|---|---|
| Trials ledger entries (`data/gauntlet/trials.jsonl`) | **115** (phase1a/scan results) |
| Strategy registry — Active | **2** (VIX-VRP-contango-breakout, oil-shock-sector-rotation) |
| Strategy registry — Deprecated | **1** (ma-pullback-fibonacci, STR-A) |
| Strategy registry — Live | **0** |
| Strategy registry — Hypotheses | **35** `.md` notes |
| G7 forward-validated / promoted to Live | **0** |
| Currently "in progress" | US-181 vol/VRP (paper-forward, data-gated), US-182 xsmom (demoted to Hypothesis on overfit) |

Recorded outcomes (recent, from this session's audit + gauntlet runs):
- **STR-Q liquidity-sweep:** bar-level **−8,447 R** (t≈−41, 24.7% win rate) → rejected, no edge.
- **16 chart-pattern strategies:** promoted on frictionless close-entry edges < friction (~0.1–0.3R) → demoted as a class.
- **Funding carry (US-179/185):** directional rejected at G3 (price risk 20–39× funding); delta-neutral blocked (no liquid HL spot).
- **Cross-sectional momentum (US-182):** **G3 pass** (+0.59 R PF 1.34) but **G4/G5 FAIL** (CPCV 10th-pct PF 0.72, PBO 0.56, DSR 0.66) → BTC-beta, demoted to Hypothesis.
- **Vol/VRP (US-181):** Hypothesis — data-gated, 6–12 months accumulation.

**Gap to flag:** because gate results are not consolidated, the exact "N entered / passed / failed per gate" and "top-3 failure reasons per gate" cannot be produced without a one-time aggregation pass over the ledger + reports. The dominant failure reasons, from the recorded outcomes, are: (1) **edge < friction** (cost), (2) **fill-timing/look-ahead** (G2/G3), (3) **beta-not-alpha / overfit** (G4/G5).

---

## 6. FEEDBACK LOOP

- **Trials ledger** (`data/gauntlet/trials.jsonl`, 115 rows) is append-only: `hypothesis_id`, `param_hash`, `universe_hash`, `period`, `result` (avg R / PF / Sharpe / win-rate / trade-count). Every backtest writes once.
- **Strategy-registry status transitions** change the folder (Active ↔ Deprecated ↔ Hypotheses) + the note. Pre-registered kill rules auto-demote Active → Hypotheses (decay-watch cron runs daily at 14:00).
- **Jev decay** (`jev_decay.py`) scores strategy health → demote/watch/healthy.
- **Does failure feed back into generation?** Partially: the `strategy-gauntlet` skill encodes a **negative prior on retail-TA / chart-pattern / ICT-SMC classes** (fast-fail at G0), and the persistent-edge shortlist (funding/basis carry, vol/VRP, cost-aware xsmom) now directs future seeds. However, the ledger is **not yet queried programmatically** by the generation cron to bias seed choice — that linkage (G5 DSR/PBO + regression-to-beta findings steering new hypotheses) is a gap.

---

## 7. EXECUTION

- **Paper trading (default):** all execution wrappers default `paper_mode=True` (ADR-002). `trade_log` + `trades.csv` (12,504 closed rows, 6 strategies — STR-Q 12,452 dominant). **Current open paper positions: 0.**
- **Crypto live:** `scripts/live_trading/live_executor.py` targets **Hyperliquid mainnet** (`api.hyperliquid.xyz`), agent custody via `create_agent_key.py`. NOT testnet. Gated by `LIVE_TRADING_ENABLED` env (default **off**) — live is dormant until credentials + gate + human approval.
- **Stocks:** **data only via Alpaca** (parquet under `~/.hermes/market_data/` + `scripts/data/alpaca_connector.py`). **No live stock broker** (no Schwab; no Alpaca trading/broker integration — Alpaca used for market data, not execution).
- **Live safety invariants (hard):** kill switch blocks OPEN only never CLOSE; every live open places a protective stop (fail-closed → flatten if stop fails); executor re-checks size cap itself; `LIVE_TRADING_ENABLED` must be explicitly set.

---

## 8. ERRORS & GAPS (last 30 days)

**Failing / degraded cron jobs (from `jobs.json` last_status/failure_streak):**

| Job | Issue |
|---|---|
| Daily Signal Scanner → Discord Publisher | **streak=29, error** (script exit 1) — the longest-running silent failure |
| Daily F&G Fetch + Freshness (US-128) | streak=2, error (Traceback) |
| Paper Trading Capture (A/B/D) | streak=2, error (exit 1 during data fetch) |
| HermesForge Confidence Digest | `delivery_failed` |
| Equity ATM IV / HL Bar Store / HL Funding Store / Vol-VRP ingests | `last_status=None`, empty last_run — newly created, not yet fired or first-run pending |

**`errors.log` recurring token classes (30d):** `error` 3,014 · `connection` 1,055 · `exception` 352 · `traceback` 327 · `timeout` 115 · `refused` 50 · `401` 42 · `403` 7 · `429` 6 · `ModuleNotFoundError` 8.

**Known recurring failure classes (from the pipeline-health skill, still relevant):**
- Cron scripts silently exit 1 (agent-wrapped crons report the agent's exit, not the subprocess — must read the output file, not `last_status`).
- Interpreter drift: 4 Pythons (system, tools, Forge venv, resolve_python target) — deps present in one but not another cause `ModuleNotFoundError` in `.sh` wrappers.
- Data unavailable → trade monitor skips closes (mitigated by `DATA_UNAVAILABLE_TIMEOUT_DAYS=5`).
- 403 on Binance/Bybit (standing; not retried).

---

## 9. COST (OpenRouter, last 30 days)

> **Scope caveat:** `usage_audit.jsonl` tracks **cron jobs only**. The ad-hoc swarm dispatches (coder/architect/backtester sessions — the bulk of this session's build work) are **not** in this ledger; they are logged in `~/.hermes/logs/agent.log`/`gateway.log` but not aggregated into a per-agent spend figure here. The number below is therefore **cron spend only** and under-states total OpenRouter spend.

**Cron spend, ≥2026-10-01 (priced at ADR-001 documented OpenRouter rates):**

| Model | Prompt tok | Completion tok | Cost |
|---|---|---|---|
| deepseek-v4-flash | 73.8M | 1.66M | $9.26 |
| deepseek-v4-pro | 11.6M | 0.21M | $8.05 |
| deepseek-v4-flash-0731 | 4.2M | 0.14M | $0.53 |
| **Total (cron, 30d)** | | | **$17.84** |

**Top cron consumers (30d):** Auto-Crosspost Daily Briefing $7.71 · Vault Connection Weaver $4.63 · decay-watch $1.25 · Autonomous Strategy Pipeline $0.66 · STR-Q Position Size Re-eval $0.59.

**Model tier pricing (documented, OpenRouter 2026-10-29):** T1 `claude-opus-4.8` $5/$25 · T2 `deepseek-v4-pro-0813` $0.66/$1.98 · T3 `deepseek-v4-flash-0731` $0.12/$0.24 · T4 blended <$0.50. (`glm-5.2`, the retired pre-10-29 T2, appears in all-time usage but $0 in the 30d window; its rate is not documented in ADR-001 anymore.)

---

## Flags / follow-up candidates

1. **No consolidated funnel tally** — recommend a one-time aggregation job (US-190) to reconcile the 115-ledger rows + registry statuses into a per-gate funnel.
2. **Daily Signal Scanner streak=29** — silent failure needs root-cause (highest-priority data/ops gap).
3. **Swarm spend not tracked in usage_audit** — ad-hoc coder/architect/backtester sessions are the real cost driver and are absent from the $17.84 cron figure.
4. **Feedback-loop gap** — trials ledger not programmatically steering seed generation (prior lives in the skill, not in the generator cron).