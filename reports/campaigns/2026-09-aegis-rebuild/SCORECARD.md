---
type: campaign-scorecard
campaign: 2026-09-aegis-rebuild
status: DEGRADED
generated_by: aegis-auditor (T1, read-only)
generated_utc: 2026-09-06
display_tz: America/Los_Angeles
---

# Aegis Rebuild — SCORECARD (DEGRADED)

Campaign: `2026-09-aegis-rebuild`
Mode: **DEGRADED** — the Campaign Brief is incomplete. See "Brief completeness"
below. No profile or cron `DELETE` verdict is issued in this run; deletions
require inventory evidence that the brief does not yet supply.

Aegis is T1 read-only. This report proposes; it does not implement. Publisher
owns publish code; Risk Guardian owns the 1% cap. Neither is touched.

---

## Brief completeness

Required pack (per `templates/campaign-brief.md`): GOALS.md, inventory.yaml,
hermes-version.md, context-budgets.md, cost-30d.md, data-manifest.md,
failure-log.md, constraints.md, current-adrs.md.

| File | State | Effect on campaign |
|------|-------|--------------------|
| GOALS.md | present, thin | usable |
| inventory.yaml | **STUB** — 3 lines, no profiles/crons/data_roots/discord_channels/publisher_owned_files arrays | Phase A partially recovered from hermes-version.md; **no DELETE verdicts** |
| hermes-version.md | present, rich (profiles + 21 crons + version) | usable — primary Phase A/E source |
| context-budgets.md | **STUB** — "TODO", no `/context` dumps | Phase D cannot cite per-profile token breakdowns |
| cost-30d.md | **STUB** — "TODO", no $/token by job | Phase D cost claims are structural, not measured |
| data-manifest.md | partial — `last_signal_id: unknown`, `fear_greed_last_ok: unknown`, `crosspost_state_bytes` absent | durability findings hold; some baselines unknown |
| failure-log.md | present | usable |
| constraints.md | present | usable |
| current-adrs.md | present (ADR-001..006 listed) | usable |

**Verdict:** 4 of 9 required files are stub/partial. Report is emitted DEGRADED.
Brief-builder stories filed (US-123, US-124) to produce a real inventory.yaml,
context-budgets.md, and cost-30d.md before the next campaign or any Train-1
efficiency work is sequenced.

Facts / Inferences / Proposals are labelled throughout.

---

## Phase A — Goal trace and inventory verdicts

Source of record: `hermes-version.md` (profiles + 21 crons). Because
`inventory.yaml` is a stub, toolsets, always-load skills, and writable paths per
profile are **unknown**; verdicts below are conservative and no mechanism is
marked DELETE.

Fleet observed (FACT, from version dump):

- 12 profiles: orchestrator, architect, coder, publisher, risk-guardian,
  researcher, backtester, documenter, product-owner, red-team, trading,
  consulting. Only `default` (deepseek-v4-pro) and `aegis-auditor`
  (claude-opus-4.8) have a model shown running/assigned; `red-team` pinned
  deepseek-v4-flash; the rest show model `—` (INFERENCE: inherit default, or
  model not surfaced in this dump — unverifiable without inventory.yaml).
- 21 active crons.

Goal → mechanism → verdict (goals from GOALS.md + invariants):

| Goal | Mechanism (cron / script) | Verdict | Note |
|------|---------------------------|---------|------|
| Discover/code/backtest/deploy strategies | Autonomous Strategy Pipeline `2d8dff` (T3), External Edge Discovery `e214a9` (T3), Weekly Research Pipeline `9202661` (T3) | THIN | 0% ship is a filter, not a factory — no coded seeder (Phase C, US-127) |
| Paper-trade + exit alerts → Discord | Paper Trading Capture `4b178ec` (no-agent), STR-Q Sweep `b9fb0af` (no-agent, */5), Trade Monitor `d1e07c` (T3, 60m), Daily Signal→Publisher `3f49a0` (no-agent), Perf Report `cb22b0` (T3) | REPLACE (I/O layer) | split exit authority: STR-Q 5m vs Trade Monitor 60m (US-125) |
| Robust trade history | `trade_log.py` v1 fuse | REPLACE | rewrite-the-world persist; no journal/snapshot/offbox/drill (Phase B, US-123/126) |
| Daily market intelligence | CRON-001 Market Intelligence `79c465` (T3), Auto-Crosspost `356f3c` (no-agent) | KEEP | delivers; verify F&G freshness (US-128) |
| Self-maintain (vault/connections/watchdog/git) | Vault Maintenance `9d77b5` (T3), Connection Discovery `232975` (T3), Vault Connection Weaver `98edbe` (240m), Cron Watchdog `65dfc5` (no-agent /15), Daily Git Push `df2caa` (no-agent) | THIN | git push is not a data backup; weaver cadence unmeasured; vault-maintenance retention vs RCA evidence unverified (US-126, US-129) |
| Risk via swarm governance | Risk Guardian profile + ADR-001/005; STR-Q re-eval `23471` (weekly), US-121 re-eval `a76bfb` (ADR-005 readiness) | KEEP | do not touch 1% cap or US-121 gate |
| LinkedIn content (Dan's voice) | LinkedIn Post Generator `98a07` (T3) | KEEP | in scope, unremarkable |
| Model routing hygiene | Weekly Model Assignment Review `07149d` (T3, 6/52) | KEEP | |
| Crosspost fan-out | Webhook Crosspost All `61cccd` (no-agent /5), Auto-Crosspost `356f3c` | THIN | two crosspost jobs — possible overlap; publisher-owned, evaluate not delete (US-130, Train 5) |

Split-brain flags (FACT from failure-log + version dump):

- **Two exit closers.** STR-Q Intraday Sweep (`b9fb0af`, */5) and HermesForge
  Trade Monitor (`d1e07c`, 60m) both act on open positions. failure-log line 3
  confirms "Split exit paths: STR-Q 5m vs swing Trade Monitor 60m." → US-125.
- **Two crosspost jobs.** `356f3c` (Auto-Crosspost Daily Briefing) and `61cccd`
  (Webhook Crosspost All Channels). Both no-agent, both local-deliver. Overlap
  is plausible but unverified without inventory. Publisher-owned; evaluate in
  Train 5, do not merge blindly.

---

## Phase B — Robustness

The dominant risk class. Evidence is direct (read `scripts/paper_trading/trade_log.py`
read-only) — these findings are FACTS, not inference.

**B-1 (P0). `trades.csv` is still a rewrite-the-world file.**
`_write_all_rows()` (trade_log.py:59) does temp→fsync→verify→atomic-rename with a
>20% shrink refusal and an empty-file refusal — a real fuse. BUT every close
path (`close_trade` :263, `update_entry_status` :191, `register_discord_info`
:164) rewrites the **entire file**. The fuse caps catastrophic loss; it does not
make the store append-only. A row-dropping bug within the 20% tolerance, or a
crash between `shutil.move` steps, still mutates history in place. `trades.csv`
is the source of truth, not a derived projection — this contradicts the target
persist contract. → US-123.

**B-2 (P0). No append-only journal.** There is no JSONL/WAL fact log. The v1
fuse is explicitly "a fuse," per invariants. The truncation on 2026-09-06 (Sep
1–5 lost, failure-log line 2) is the realized instance of this class. → US-123.

**B-3 (P0). No snapshots, no off-box copy, no restore drill.**
data-manifest: `snapshot_last_ok: none`, `offbox_last_ok: none`,
`restore_drill_last_ok: none`. "Backup" today is the Daily Git Push (`df2caa`) —
git stores the CSV as code, which is not a data-backup regime and did not cover
the Sep 1–5 window. Numerous ad-hoc `.bak` files exist (`trades.csv.bak`,
`.bak2`, `.bak.heatfix`, `.bak.1788717923`) — informal, unmanaged, exactly the
"backup that is only a copy" anti-pattern. → US-126.

**B-4 (P1). `crosspost_state.json` has no stated protection.**
`crosspost_state_bytes` is absent from data-manifest and no guard is described.
Same protection class as trades per invariants. Publisher-owned file — Aegis
does not touch it; story routes to publisher. → US-131.

**B-5 (P1). Vault Maintenance retention vs RCA/cron evidence unverified.**
`9d77b5` runs daily 02:00. The protocol warns of "vault maintenance purging
RCA/cron evidence at 14 days." Cannot confirm or deny without inventory. → US-129
(investigation story).

**B-6 (P2). Unpinned-LLM-cron fail-closed status unverified.** Most crons show
model `—`. Invariant requires unpinned LLM crons fail closed. Unverifiable
without inventory.yaml. → folded into US-124 (inventory build).

Robustness questions answered:

- Can a killed process mid-write destroy history? **Reduced but not eliminated**
  (B-1/B-2). Rename is atomic; the whole-file rewrite model is the residual risk.
- Last restore drill date? **Never** (data-manifest).
- Off-box snapshot age? **None exist** (data-manifest).
- Does Trade Monitor see STR-Q? **Two closers exist** (B, A split-brain).

---

## Phase C — Effectiveness (vs stated goals, not feature count)

- **Strategy pipeline: filter, not factory (FACT).** failure-log line 4:
  "Strategy pipeline 0% ship (filter, not factory)." The BACKLOG_INDEX shows the
  pipeline *has* shipped WATCH-tier strategies recently (US-113/114/115/120/122,
  each deployed WATCH at 0.5% risk with walk-forward OOS). INFERENCE: "0% ship"
  refers to promotion past WATCH into a funded/scaled tier, or to a specific
  window; the reject-heavy filter is behaving as designed, but there is no coded
  *seeder* feeding it — candidate generation is ad-hoc. Keep the reject-heavy
  filter; add a coded seeder + Risk-Guardian-gated promotion. → US-127.
- **Exit alert SLA and ownership: split (FACT).** Two closers (Phase A/B).
  No single exit authority or stated SLA. → US-125.
- **Dead Discord channels: unverifiable.** `inventory.yaml` lists no channel
  names; version dump shows numeric channel IDs only. Cannot confirm a
  `#strategy-status` with no content source. → covered by US-124 inventory build.
- **Stale feeds disabling regime logic: unverified.** `fear_greed_last_ok:
  unknown` (data-manifest). If F&G is stale, regime gating silently degrades.
  → US-128 (F&G freshness check + fail-closed).
- **Research grounding: not assessed this run** (needs the artifacts the
  research crons emit; out of scope for a DEGRADED pass).

---

## Phase D — Token / RAM / context (DEGRADED — no measured data)

context-budgets.md and cost-30d.md are both "TODO." No `/context` dumps, no
$/token by job. Therefore **all statements here are structural inferences from
the cron/profile inventory, not measurements.** Full table in `TOKEN-RAM-BUDGET.md`.

Structural observations (INFERENCE):

- 21 crons; 8 already no-agent (capture, sweep, publish, crosspost×2, git push,
  watchdog, daily signal). Good — the mechanical floor is largely correct.
- ~9 T3 LLM crons remain (market intel, vault maintenance, connection discovery,
  model review, trade monitor, weekly research, external edge, strategy
  pipeline, perf report, LinkedIn, ADR-005 readiness, STR-Q re-evals). Several
  are candidates for no-agent gather + one reasoning call (perf report, model
  review) — but this needs measured cost to prioritize. → US-124 unblocks this.
- Vault Connection Weaver on every-240m: protocol calls out demoting/batching it
  "unless measured quality requires it." Quality unmeasured → cannot yet justify
  a cadence change. → deferred to Train 1 pending US-124.
- 8 GB VPS: do **not** merge unrelated crons into mega-jobs (protocol). No
  mega-merge proposed.

**No Train-1 efficiency story is sequenced ahead of the inventory/cost build.**
Cutting toolsets or demoting crons without measured `/context` is guessing.

---

## Phase E — Hermes release delta

Installed: **v0.20.6 (2026.8.27), git install, 5917 commits behind** (FACT,
hermes-version.md). No `hermes update --plan` receipt in the brief. Full
analysis in `HERMES-RELEASE-DELTA.md`. Headline: a 5917-commit gap is itself a
risk — adopt native primitives only where each deletes a Forge workaround, and
stage the update behind a plan receipt and Train-0 durability. Upgrade success =
net deletion.

---

## Phase F/G — Target + trains

See `TARGET-ARCHITECTURE.md`. Train order is fixed; **Train 0 (Survive) first**.
Stories filed this run are Train 0 durability + brief-builder only. Trains 1–5
are described but not yet sequenced into stories, pending the real inventory.

---

## Stories filed this campaign

| Story | Train | Pri | Owner | Title |
|-------|-------|-----|-------|-------|
| US-123 | 0 | P0 | coder | Append-only trade journal; trades.csv becomes derived projection |
| US-124 | 0 | P0 | no-agent | Build real inventory.yaml + context-budgets + cost-30d (brief-builder) |
| US-125 | 0 | P0 | coder | Single exit authority — resolve STR-Q 5m vs Trade Monitor 60m split |
| US-126 | 0 | P0 | no-agent | On-box snapshots ≥35d + off-box copy + weekly restore drill |
| US-127 | 3 | P2 | coder | Coded strategy seeder feeding the reject-heavy filter |
| US-128 | 0 | P1 | no-agent | Fear & Greed freshness check + fail-closed regime gate |
| US-129 | 0 | P1 | product-owner | Investigate Vault Maintenance retention vs RCA/cron evidence |
| US-130 | 5 | P2 | publisher | Evaluate crosspost job overlap (356f3c vs 61cccd) |
| US-131 | 0 | P1 | publisher | Protect crosspost_state.json (guard + snapshot class) |

Train 1/2/4 detailed stories are deferred until US-124 delivers measured
inventory and cost. No DELETE verdict is issued in this DEGRADED run.

---

## Do-not-touch

See `DO-NOT-TOUCH.md`. Summary: 1% Risk Guardian cap, US-121 gate, publisher's 9
files (embed/chart/alert/template/publishing), `trades.csv` (data), live souls,
cron definitions, `.env`, journals/Parquet, `crosspost_state.json`.
