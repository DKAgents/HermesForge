---
type: campaign-scorecard
campaign: 2026-09-aegis-rebuild
status: GRADED
pass: 2
generated_by: aegis-auditor (T1, read-only)
generated_utc: 2026-09-07
display_tz: America/Los_Angeles
supersedes: pass-1 (DEGRADED, 2026-09-06)
---

# Aegis Rebuild — SCORECARD (Pass 2, GRADED)

Campaign: `2026-09-aegis-rebuild`
Mode: **GRADED** — the Campaign Brief is now sufficiently complete to issue
verdicts. Pass 1 (2026-09-06) was DEGRADED because `inventory.yaml` and
`cost-30d.md` were stubs; US-124 filled both. This second pass re-scores against
the real inventory and against the current on-disk state, which has advanced
materially since pass 1 (US-123/125/126 shipped).

Aegis is T1 read-only. This report proposes; it does not implement. Publisher
owns publish code; Risk Guardian owns the 1% cap. Neither is touched.
Facts / Inferences / Proposals are labelled throughout. Times display PT;
computation UTC.

---

## Brief completeness (pass 2)

Required pack: GOALS.md, inventory.yaml, hermes-version.md, context-budgets.md,
cost-30d.md, data-manifest.md, failure-log.md, constraints.md, current-adrs.md.

| File | State (pass 2) | Change since pass 1 |
|------|----------------|---------------------|
| GOALS.md | present | — |
| inventory.yaml | **COMPLETE** — 13 profiles, 24 crons, 9 channels, data roots, disk | ⬆ was 3-line stub |
| hermes-version.md | present, rich | — |
| context-budgets.md | **STILL STUB ("TODO")** | ✗ unchanged — the one remaining gap → US-139 |
| cost-30d.md | **COMPLETE** — $/token by job, no-agent list, disk | ⬆ was TODO |
| data-manifest.md | partial — `snapshot_last_ok`/`offbox_last_ok`/`restore_drill_last_ok` still `none`/unknown | ✗ stale vs on-disk reality (see Phase B) |
| failure-log.md | present | — |
| constraints.md | present | — |
| current-adrs.md | present (ADR-001..006) | — |

**Verdict:** 8 of 9 files usable. Only `context-budgets.md` remains a stub. Per
principal direction, this is **not** a DEGRADED-wide failure — the campaign
grades normally and files one narrow story (US-139) to close the last gap.
Phase D's per-profile *token composition* claims remain inferential until US-139
lands; every other phase is evidence-graded.

Note (FACT): `data-manifest.md` is now *stale in the safe direction* — it still
says snapshots/off-box/drill = none, but snapshots demonstrably exist on disk.
The manifest should be regenerated; US-136/US-137 write the missing
`offbox_last_ok`/`restore_drill_last_ok` fields as they land.

---

## What shipped between pass 1 and pass 2 (FACT, verified on disk)

| Story | Claim | Evidence (2026-09-07 UTC) |
|-------|-------|---------------------------|
| US-123 | Append-only journal; CSV becomes derived projection | `trade_journal.py` present; `trade_log.py` dual-writes (`journal_open/close/...` imported, header comment "journal is the source of truth"); `trade_journal.jsonl` = 1,687 rows; manifest carries sha256 + last_signal_id + closed_count=541 |
| US-125 | Single exit authority (STR-Q 5m vs Trade Monitor 60m) | `trades.csv` schema now has a `closer` field ("STR-Q-5m-sweep" / "trade-monitor-60m"); Trade Monitor note "Skips STR-Q per ADR-006" |
| US-126 | Snapshots + off-box + restore drill | `scripts/maintenance/snapshot_restore.py` present; 2 daily snapshot dirs with `snapshot.json` (per-file sha256, journal_rows, crosspost_state); snapshot cron `291708a04c39` left 03:00 output |
| US-133 | Cron retention → 35 days | inventory data_roots: `/root/.hermes/cron/output` retention "35 days (US-133, was 14 days)" |

The dominant pass-1 P0 (rewrite-the-world trades.csv with no journal) is
**resolved in class**: the journal is now the append-only source of truth and
the CSV is explicitly a projection. `_write_all_rows()` still rewrites the whole
CSV, but that is now acceptable — the CSV is derived and the fuse (temp→fsync→
verify→rename, >20% shrink + empty refusal) still guards it.

---

## Phase A — Goal trace and inventory verdicts (GRADED)

Fleet (FACT, `inventory.yaml`): 13 profiles (12 swarm + aegis-auditor),
24 crons (22 enabled, 1 paused `356f3c`, 1 completed `2b4f6f`), 9 channels.
Only `orchestrator` is `hot`; all others on-demand/campaign-only.

Goal → mechanism → verdict:

| Goal | Mechanism | Verdict | Note |
|------|-----------|---------|------|
| Discover/code/backtest/deploy strategies | Strategy Pipeline `2d8dff`, External Edge `e214a9`, Weekly Research `9202661` (all T3) | THIN | filter works; no coded seeder → US-127 (already filed) |
| Paper-trade + exit alerts → Discord | Capture `4b178ec`, STR-Q Sweep `b9fb0af`, Trade Monitor `d1e07c`, Signal→Publisher `3f49a0`, Perf Report `cb22b0` | KEEP | exit split resolved by US-125 (`closer` field shipped) |
| Robust trade history | journal + fuse + snapshots (US-123/126) | KEEP w/ residual | append-only shipped; **off-box copy inert** → US-136; drill unverified → US-137 |
| Daily market intelligence | Market Intel `79c465` (T3) | KEEP | verify F&G freshness (US-128 filed) |
| Self-maintain | Vault Maint `9d77b5`, Connection Discovery `232975`, **Weaver `98edbe`**, Watchdog `65dfc5`, Git Push `df2caa` | THIN | weaver is T2 + unrestricted toolset + near-zero recent yield → **US-138** |
| Risk via swarm governance | risk-guardian + ADR-001/005; STR-Q re-eval `23471`; US-121 gate `a76bfb` | KEEP | 1% cap and US-121 untouched |
| LinkedIn content | LinkedIn Gen `98a07` (T3) | KEEP | |
| Crosspost fan-out | Webhook Crosspost `61cccd` + paused `356f3c` | KEEP | overlap already handled — `356f3c` paused under US-130 |

Profile DELETE/THIN verdicts: see Phase F table and **US-141** (documenter→skill,
red-team periodic, trading/consulting as surfaces; publisher + risk-guardian
KEEP as monopolies). No hard-DELETE issued — smallest profiles are surfaces
worth keeping; documenter retirement is gated on its skill replacement existing.

Split-brain status:
- Two exit closers → **RESOLVED** by US-125 (`closer` ownership field).
- Two crosspost jobs → **RESOLVED** — `356f3c` is paused (US-130); `61cccd` is
  the sole active crosspost path.

---

## Phase B — Robustness (GRADED)

**B-1 (was P0) — trades.csv rewrite-the-world: RESOLVED IN CLASS.** Journal is
now the append-only source of truth; CSV is a derived projection guarded by the
fuse. FACT: journal 1,687 rows, manifest sha256 present. Residual: `_write_all_rows`
still full-rewrites the projection, but a projection rebuild is not history loss.

**B-2 (was P0) — no append-only journal: RESOLVED.** `trade_journal.py` +
`trade_journal.jsonl` + manifest exist and are written on every open/close.

**B-3 (was P0) — snapshots/off-box/drill: PARTIALLY RESOLVED.**
- Snapshots: **SHIPPED** — 2 daily snapshot dirs with per-file sha256.
- Off-box copy: **NOT ACTIVE (P1)** — `snapshot.json` records
  `"offbox_copied": false`; `OFFSITE_BACKUP_PATH` is unset in env/`.bashrc`/
  `.profile`/cron. Code exists (`_copy_offsite`) but is inert. → **US-136.**
- Restore drill: **UNVERIFIED (P1)** — cron `dfa4ab05ea77` exists (Sunday 08:00)
  but `~/.hermes/cron/output/dfa4ab05ea77/` does not exist and
  `restore_drill_last_ok: none`. No drill run has been observed to pass. → **US-137.**

**B-4 (P1) — crosspost_state.json protection: SHIPPED (US-131).** inventory:
"atomic write + regression guard (US-131)"; it is included in snapshot payloads
(`snapshot.json` records `crosspost_state_sha256` + bytes).

**B-5 (P1) — vault-maintenance retention vs evidence: RESOLVED (US-129/133).**
Cron output retention raised 14→35 days; follow-ups US-134 (cron output into
snapshot payload) and US-135 (incident log into snapshot payload) filed.

**B-6 — unpinned-LLM-cron fail-closed:** now checkable via inventory. All agent
crons show a pinned model (`deepseek-v4-flash`, or `-pro` for the weaver). No
unpinned LLM cron observed. THIN concern retired.

Robustness questions:
- Killed process mid-write destroys history? **No for the journal** (append-only
  + fuse). CSV projection is rebuildable.
- Last restore drill date? **Still never observed** → US-137.
- Off-box snapshot age? **None — off-box inert** → US-136.
- Does Trade Monitor see STR-Q? **Split resolved** — `closer` field + ADR-006 skip.

---

## Phase C — Effectiveness (GRADED)

- **Strategy pipeline — filter, not factory (FACT).** BACKLOG_INDEX shows
  WATCH-tier deploys (US-113/114/115/120/122) at 0.5% risk with walk-forward
  OOS — the reject-heavy filter works. Still no coded *seeder*; generation is
  ad-hoc. → US-127 (filed pass 1).
- **Exit alert ownership — RESOLVED.** `closer` field gives each trade exactly
  one closer (US-125).
- **Dead channel `#strategy-status` (FACT).** inventory channel
  `1533332485641998386` (strategy-status) note: "No cron job posts here
  currently — content gap." A live channel with no producer. Publisher-owned
  routing; evaluate whether to retire the channel or give it a producer — folds
  into publisher's US-118 (channel-routing) rather than a new Aegis story.
- **Stale feeds / F&G — tracked.** `fear_greed_last_ok: unknown` in manifest;
  US-128 (F&G freshness + fail-closed) filed pass 1.
- **Weaver effectiveness (FACT).** 90 runs / 204 lifetime connections; recent
  examined-notes all `connections_written: 0`. Effectiveness of the single most
  expensive job is near-zero recently. → US-138.

---

## Phase D — Token / RAM / context (GRADED where measured)

`cost-30d.md` now supplies measured-basis estimates; `context-budgets.md` is
still TODO so per-profile token *composition* remains inferential (→ US-139).
Full table: `TOKEN-RAM-BUDGET.md` (refreshed this pass).

Headlines (FACT from `cost-30d.md` + `jobs.json`):
- Total fleet LLM cron spend ~**$1.45/mo**; +orchestrator sessions ~$0.36 →
  **~$1.81/mo**. Cost is not the constraint.
- **Weaver = $1.18/mo = 65% of LLM cron spend**, the only T2 cron, and its
  `enabled_toolsets` is `None` (inherits all — a Phase-D allowlist violation).
  This is the clearest efficiency target on evidence. → US-138.
- 10 of 22 active crons are no-agent (45%). Perf Report `cb22b0` and Model
  Review `07149d` remain no-agent-gather candidates but at ~$0.01/mo each the
  saving is negligible; deprioritized.
- RAM (FACT): `free -h` = 7.7 Gi total, 3.0 Gi used, 4.8 Gi available. Only
  `orchestrator` is hot; no mega-merge proposed. No RAM pressure.
- Disk (FACT): 49 G / 240 G (22%). `signal_charts` = 826 MB / 8,497 files, the
  largest dir, with a weekend purge gap → US-140 (P3, no disk pressure).

---

## Phase E — Hermes release delta

Installed **v0.20.6, 5917 commits behind** (FACT). Full analysis in
`HERMES-RELEASE-DELTA.md`. Unchanged from pass 1 in substance: adopt native
primitives only where each deletes a Forge workaround, stage behind a
`hermes update --plan` receipt, and **do not upgrade until Train-0 durability is
fully closed** — which now means US-136 (off-box) + US-137 (drill proof) must
land first, since an upgrade on an unbacked-off-box store repeats the Sep-6
hazard class.

---

## Phase F/G — Target + trains

`TARGET-ARCHITECTURE.md` refreshed. Train 0 is now mostly *shipped*; its only
open items are US-136 (off-box) and US-137 (drill proof) — both P1, both must
precede any Train-5 Hermes upgrade. Train 1 gains US-138 (weaver), US-139
(context budgets), US-140 (charts purge). Train 4 gains US-141 (swarm diet).

---

## Stories (this campaign)

Pass 1 (filed 2026-09-06, unchanged): US-123✔ US-124✔ US-125✔ US-126(partial)
US-127 US-128 US-129✔ US-130✔ US-131✔ US-132 US-133✔ US-134 US-135.
(✔ = shipped/closed per on-disk evidence or BACKLOG_INDEX.)

Pass 2 (filed 2026-09-07):

| Story | Train | Pri | Owner | Title |
|-------|-------|-----|-------|-------|
| US-136 | 0 | P1 | no-agent | Activate off-box snapshot copy (offbox_copied=false) |
| US-137 | 0 | P1 | no-agent | Capture restore-drill evidence + restore_drill_last_ok |
| US-138 | 1 | P2 | coder | Right-size Vault Connection Weaver (tier/cadence/toolset allowlist) |
| US-139 | 1 | P2 | no-agent | Fill context-budgets.md (last stub brief file) |
| US-140 | 1 | P3 | no-agent | Close signal_charts purge gap (826 MB / 8,497 files) |
| US-141 | 4 | P3 | product-owner | Swarm diet — documenter→skill, trading/consulting surfaces (evidence-gated) |

---

## Do-not-touch

See `DO-NOT-TOUCH.md`. Unchanged: 1% Risk Guardian cap, US-121 gate, publisher's
9 files, live souls, cron definitions (Aegis does not edit them — US-138/US-141
hand cron/profile changes to their owners with evidence attached), `.env`,
journals/Parquet, `crosspost_state.json`.
