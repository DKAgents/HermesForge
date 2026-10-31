---
id: SPEC-US-158-161-PHASE1
title: Phase-1 Detection-Only Self-Healing Layer — System Doctor + Confidence Digest
governed_by: ADR-007 (Self-Healing System with Trading-Safety Boundary)
governed_by_ref: ADR-001 (Model Routing Strategy)
epic: EPIC-015 (Autonomous Self-Healing)
stories: [US-158, US-161]
status: design-approved (decisions resolved 2026-10-31)
author: architect
created: 2026-10-31
confidence: high
phase: 1 (detection-only — "eyes, no hands")
---

# Phase-1 Detection-Only Self-Healing Layer — Design Spec

## 0. Purpose & Binding Constraints

This spec designs **US-158** (Layer-1 detection loop → shared findings queue) and
**US-161** (confidence digest). It is **design only** — no implementation, no cron
creation, no production code. It deliberately covers *only* Phase 1 of ADR-007's
Sequencing ("detection loop / system doctor").

Binding constraints (from ADR-007 "Autonomy boundary" + EPIC-015 DoD):

1. **Read-only to the trading pipeline.** The doctor may *observe* trading-relevant
   state and must *classify* anything that touches live money / kill-switch /
   size-cap / secrets as Tier-2 (human-gated). It must **never** modify it.
2. **No auto-fix in Phase 1.** "Auto-fixed N" in the digest is **0 by construction**
   until Phase 2 ships the Tier-0/1 fix loop. This must not be conflated with
   "nothing was found."
3. **Fail-closed.** A doctor that cannot complete a scan reports the *failure* as a
   finding (Tier-1 self-monitoring), never as "clean."
4. **Surface "what was NOT inspected."** The digest's most important line is the
   explicit list of scan components that did not produce a verdict — this is the
   ADR-007 mitigation for silent false-clean.
5. **One shared queue.** The existing fragmented detectors (Vault Maintenance
   `9d77b5c75db7`, Weekly Model Review `07149d6b05cc`, Cron Watchdog `65dfc591efad`,
   decay-watch `58bccfa185b5`) currently write isolated outputs. Phase 1 introduces
   a single sink that the Orchestrator will later consume (US-159).

---

## 1. System Doctor Scan Surface

The "system doctor" is a scheduled scan that reads **live** state and emits one
findings queue (Section 2). Pressures are grouped into six categories. Each
category names: **what is read**, **how it is read**, **classification rule**
(issue vs optimization), and **risk tier** (per ADR-007).

Risk-tier semantics for *detection* (a finding carries the tier its eventual fix
would require in Phase 2; Tier 2 findings are surfaced to the human and never acted
on automatically):

| Tier | Meaning (ADR-007 Layer 2 mapping) | Detection phase role |
|------|-----------------------------------|----------------------|
| **0** | Auto-apply fix (deps, refresh, stale path/date, cleanup, point-release bump) | record; Phase 2 will auto-apply |
| **1** | Auto-via-swarm (reversible code fix, green test + commit) | record; Phase 2 routes to coder |
| **2** | Human sign-off (trading logic, sizing, secrets, exchange API, live money) | surface to human; read-only, never touched |

### 1.1 Cron output & error logs

**What is read (live, authoritative):**
- `/root/.hermes/cron/jobs.json` — per job: `id`, `name`, `last_status`,
  `last_error`, `last_delivery_error`, `failure_streak`, `last_run_at`,
  `next_run_at`, `no_agent`, `model`, `script`.
- `/root/.hermes/cron/output/<job_id>/<YYYY-MM-DD_HH-MM-SS>.md` — newest file per
  job directory (the agent's last response body).
- `/root/.hermes/cron/output/<job_id>_<YYYYMMDD>_<HHMMSS>.txt` — loose "Cronjob
  Response" files (full transcript incl. header `Cronjob Response: <name>
  (job_id: ...)`).
- `/root/.hermes/cron/usage_audit.jsonl` — per-call token/spend records (cost rollup).
- `/root/.hermes/cron/executions.db`, `deliveries.db` — deeper forensics (optional,
  Phase 2).

**How read:** `jobs.json` is the single source of truth for *health*; output files
supply *why*. The doctor reads the `last_error`/`last_delivery_error` string and, for
jobs in `error`, opens the newest output file (`.md` or `.txt`) to extract the
failure signature (first N lines / a grep for `Traceback|Error|Exception|failed`).

**Classification rules:**

| Signal | Class | Tier | Note |
|--------|-------|------|------|
| `last_status=="error"` and `failure_streak>=1` | issue | 0 or 1 | tier decides by *cause*: dependency/config → 0; code bug → 1 |
| `failure_streak>=3` (recurring same signature) | issue | 1 | needs code fix, not a retry |
| `last_delivery_error` set but `last_status=="ok"` | issue | 0 | delivery/deliver-target misroute (matches user's crosspost concern) |
| job `model` field null/stale/retired | issue | 0 | tier drive (see 1.3) |
| output dir has zero files for an `enabled` job | issue | 1 | silent-skip detection (no output ≠ success) |
| detection gaps (see 1.6) | issue | 1 | self-monitoring |
| healthy job, no findings | — | — | no queue entry (do NOT write success noise) |

**Known live exemplars (as of 2026-10-31) that the doctor MUST catch on first run:**
- `b9fb0afb1e29` STR-Q Intraday Sweep — `error`, streak 22 (CRITICAL).
- `3f49a07a2f04` Daily Signal Scanner — `error`, streak 27 (CRITICAL).
- `232975d5fc83` Connection Discovery — `error`, streak 1.

These three are *already* failing and fragmented detectors have not surfaced them
cohesively — the exact failure mode Phase 1 exists to end.

### 1.2 Data freshness (DXY / yields / macro)

**What is read:** mtime + content of the cached datasets owned by the data-owner
scripts (read-only `stat` and head-of-file date stamp, never re-fetch):
- Regime data (VIX, DXY, 10Y yields, Fear&Greed, breadth) → `scripts/data/regime_filter.py`
- DeFi TVL → `scripts/data/fetch_defillama.py`
- Stablecoin supply → `scripts/data/fetch_stablecoin_supply.py`
- Fear & Greed (US-128) → `scripts/.../fetch_fg_daily.sh` cache

**How read:** locate the `last_refreshed`/`date` field or file mtime per dataset and
compare `age = now - refresh_time` against a per-domain staleness threshold.

**Classification rules:**

| Signal | Class | Tier |
|--------|-------|------|
| `age > threshold` for a market-open-relevant dataset (DXY/yields/VIX) | issue | 0 (refresh is Tier-0 auto-apply in Phase 2) |
| dataset file missing / parse error | issue | 1 (schema/code change) |
| `age` creeping but within threshold | optimization | 0 |

**Open decision D5:** exact cache paths + per-domain thresholds need a one-time
inventory (see Section 6). Default proposed thresholds: DXY/yields/VIX ≤ 1 market
day; Fear&Greed ≤ 2 days; TVL/stablecoin ≤ 2 days.

### 1.3 Model staleness vs OpenRouter

**What is read:**
- Every cron job's `model` field from `jobs.json`.
- OpenRouter `/models` (via Headroom proxy `http://127.0.0.1:8787/v1/models`) to
  check (a) the pinned slug still *exists*, (b) whether a newer point-release of
  the same family exists (`deepseek-v4-flash-0731` → `-xxxx` suffix).

**How read:** GET the model list, cache for the scan duration, compare families.

**Classification rules:**

| Signal | Class | Tier |
|--------|-------|------|
| pinned slug retired/404 on OpenRouter | issue | 0 (re-pin; but *which* model = a routing decision → flag to human if it affects risk-guardian/orchestrator/architect/coder hard floor) |
| newer point-release of a pinned T2/T3 model exists | optimization | 0 (Phase 2: bump point-release) |
| a hard-floor profile's job drifts below its floor (ADR-001 §"Agent Routing Rules") | issue | 2 (routing governance — flag to human, never auto-change) |
| all pinned slugs present + current | — | — |

### 1.4 Cost drift vs the ~$5–8/month cap

**What is read:** `usage_audit.jsonl` (or `executions.db`) rollup of OpenRouter spend
over the trailing 30 days.

**How read:** sum cost (and token deltas) per model tier + total; compare total to
the cap; compute day-over-day and week-over-week slope to detect drift *before* it
blows the cap, not after.

**Classification rules:**

| Signal | Class | Tier |
|--------|-------|------|
| trailing-30d spend > cap | issue | 1 (needs a routing/tier investigation — the *cure* is a T2 decision in Phase 2) |
| slope projects exceed-cap within next 30d | optimization | 1 |
| a single job's per-call cost anomalous vs its tier's norm | optimization | 1 |
| within cap, flat | — | — |

**Open decision D6:** confirm the cap number ($5 vs $8) and whether it is a hard or
soft ceiling (soft = threshold to *investigate*, not a blocker).

### 1.5 Disk / SSH / security posture

**What is read (read-only OS probes):**
- `df -h /` → usage % vs threshold (proposed: 85% warn, 92% critical).
- `systemctl is-active` for `hermes-gateway`, `hermesforge-listener`, `ssh`,
  `cron` services.
- `sshd -T` effective-config probe → `PermitRootLogin`, `PasswordAuthentication`,
  `PubkeyAuthentication` (security-relevant flags only).
- journald disk usage if large (`journalctl --disk-usage`, best-effort).

**Classification rules:**

| Signal | Class | Tier |
|--------|-------|------|
| disk > 92% | issue | 1 (cleanup is Tier-0 in Phase 2, but *root cause* may need eyes) |
| any core service inactive | issue | 1 |
| `PasswordAuthentication yes` or `PermitRootLogin yes` on sshd | issue | 2 (security posture = human-gated) |
| disk 85–92% | optimization | 0 |
| all healthy | — | — |

### 1.6 Upstream Hermes git

**What is read:** `git -C /root/HermesForge` (read-only, no write, no pull, no
fetch-with-effect — use `git fetch --dry-run` to learn remote position safely):
- `git status --porcelain` count (dirty tree).
- local `HEAD` vs `origin/main` (ahead/behind/diverged).
- last commit age.

**Classification rules (aligned with the "uncommitted changes unacceptable" hard
rule + "code changes must be committed immediately"):**

| Signal | Class | Tier |
|--------|-------|------|
| dirty tree with >0 uncommitted changes persisting >24h | issue | 1 |
| local `HEAD` behind `origin/main` (unpulled upstream) | issue | 0 (pull is Tier-0; but merge conflicts → 1) |
| diverged (local ahead AND remote ahead) | issue | 1 (needs human-aware merge) |
| last commit older than a cadence threshold | optimization | 1 |
| clean + in sync | — | — |

---

## 2. Findings Queue Schema

### 2.1 Location & format

**Location:** `/root/HermesForge/cache/system-doctor/findings.jsonl`
(append-only JSONL; one JSON object per line; atomic append via write-to-temp +
`os.replace`, matching the existing atomic-write convention).

Rationale for JSONL over markdown: the Orchestrator (US-159) consumes it
programmatically (filter `status=="open"`, select ≤3, update `status`), and JSONL
is trivially append/merge-safe for idempotent re-runs. Vault markdown is reserved
for human-facing digests and ADR records.

A companion index file `findings.state.json` holds scan metadata (last full scan
ts, per-category last verdict) for idempotency and the "not inspected" list.

### 2.2 Field names (exact)

```jsonc
{
  "id": "SRQ-REFRESH-007",                    // stable dedup key (always present)
  "ts": "2026-10-31T06:00:00Z",               // detection timestamp (ISO8601 UTC)
  "category": "data_freshness",               // enum, see 2.3
  "risk_tier": 0,                             // 0 | 1 | 2  (fix-tier it will need)
  "class": "issue",                           // "issue" | "optimization"
  "source": "regime_filter.py",              // canonical source id (job_id|script|domain)
  "summary": "DXY/yields cache stale (age 3.1d > 1d threshold)",
  "evidence": {                                // machine-readable pointer
    "type": "cron_job",                        // cron_job|file_mtime|os_probe|git_state|openrouter
    "ref": "b9fb0afb1e29",                     // job id / path / command
    "detail": "last_error: <...>; failure_streak: 22"
  },
  "fix_suggestion": "Rerun regime_filter.py; see Phase 2 Tier-0 refresh",
  "dedup_key": "sha256(category|source|normalized_summary)",  // computed, 2.4
  "first_seen": "2026-10-31T06:00:00Z",
  "last_seen": "2026-10-31T06:00:00Z",
  "count": 1,                                  // consecutive detections
  "confidence": null,                          // 0..1, only when LLM-classified (usually null: mechanical rules)
  "status": "open"                             // open|digested|suppressed|resolved
}
```

### 2.3 Enumerations

- `category` ∈ `{ cron_error, data_freshness, model_staleness, cost_drift,
  disk_ssh_security, upstream_git, doctor_self }`
- `risk_tier` ∈ `{0,1,2}` (ADR-007 ladder)
- `class` ∈ `{ issue, optimization }`
- `status` ∈ `{ open, digested, suppressed, resolved }`
  - `open` — newly detected, not yet surfaced/consumed
  - `digested` — reported to the human in a digest
  - `suppressed` — human or doctor marked noise (with a `suppress_reason`)
  - `resolved` — fix confirmed (Phase 2; in Phase 1 only via manual human edit)

### 2.4 Dedup / idempotency rules

1. **Deterministic key.** `dedup_key = sha256(category + "|" + source + "|" +
   normalize(summary))` where `normalize` lowercases + strips timestamps/ids/numbers
   so the *same* recurring failure maps to one key ("sweep stale for 38 min" and
   "sweep stale for 41 min" collapse).
2. **Re-run suppression.** On appending a new finding, if an entry with the same
   `dedup_key` AND `status in {open, digested}` already exists AND
   `now - last_seen < STALE_WINDOW` (proposed 24h), **do not append** — instead
   update that entry's `last_seen = now`, `count += 1`, and refresh `evidence`.
   This means a re-run of the doctor never duplicates findings.
3. **Escape-from-window.** If the same key re-appears *after* `STALE_WINDOW` or
   after the prior entry reached `resolved`, append a **new** record (a recurrence
   is a distinct event, and re-resolution is a distinct fact).
4. **Idempotent scan.** Recomputing all category verdicts every run is safe: only
   *materialized* findings are written by rule 2; "healthy, nothing found" is never
   written as a row (avoids queue noise from the 5-min sweeps).

### 2.5 Orchestrator consumption contract (for US-159, documented here)

Later, the Orchestrator (T2) will: read `findings.jsonl` → filter
`status=="open"` → order by `risk_tier DESC`, then `count DESC` → select ≤3 →
delegate per `fix_suggestion` → update `status="digested"` / later `"resolved"`.
Phase 1 ships only the *producer* side of this contract; the consumer is explicitly
out of scope and must not auto-run.

---

## 3. Confidence Digest

### 3.1 Cadence & delivery

- **Cadence:** daily (`0 7 * * *` proposed), after the doctor (06:00) and after the
  overnight cron batch (02:00–05:30) have updated `last_status`.
- **Silent suppression:** if there are **no new open findings and no change** since
  the last digest, emit `[SILENT]` (no message). This keeps the human from tuning
  out a daily "all clear." "Changed" includes: any finding resolved, any new Tier-2
  item, any doctor_self failure.
- **Delivery target:** a dedicated Discord channel (see decision D1). It must NOT be
  `#daily-market-briefing` (channel governance: that channel is briefings-only).
  Optional: also mirror to the human's main thread.

### 3.2 Exact format (template)

```
**🩺 System Doctor — Confidence Digest** · 2026-11-01 07:00 UTC

**Auto-fixed:** 0
_(none — fix layer (Phase 2) is not enabled yet; this is the expected value)_

**Need sign-off (Tier 2):** 1
• sshd `PermitRootLogin yes` — why: active password/root SSH login broadens attack
  surface; deferral consequence: unchanged exposure until someone hardens sshd.
  (human-gated: security posture)

**Tier 1 findings (queued, not acted):** 2
• STR-Q sweep `error` streak 22 — why: no output for ~2h; consequence: missed
  intraday signals, silent data gap in paper logs.
• Daily Signal Scanner `error` streak 27 — why: publisher failing; consequence:
  no stock/crypto setups posted.

**Trading-boundary anomalies:** 0
_(kill-switch, size-cap, secrets, LIVE_TRADING_ENABLED: no change, no touch)_

**NOT inspected this cycle:**
• data_freshness: cache path inventory missing (D5) — no verdict
• (any category that errored or was skipped)

**Queue:** /root/HermesForge/cache/system-doctor/findings.jsonl — N open · M resolved
```

Notes on the format contract:
- **"Auto-fixed"** is always rendered (even at 0) with the explicit "(Phase 2 not
  enabled)" parenthetical so the human can distinguish "no fixes performed" from
  "nothing wrong."
- **"Need sign-off"** = Tier-2 findings only; each carries *why* + *deferral
  consequence* (ADR-007 requires both).
- **"Tier 1 findings"** are reported as *observed, queued, not acted* — they are
  visible without being acted on in Phase 1.
- **"Trading-boundary anomalies"** must always be zero or the boundary is violated;
  a non-zero value here is itself a Tier-2 human-gated finding that halts further
  autonomous review.
- **"NOT inspected"** is mandatory and non-empty whenever any category produced no
  verdict — this is the anti-false-clean mechanism (ADR-007 "Consequences").

### 3.3 Model tier

Digest synthesis = **T3** (`deepseek/deepseek-v4-flash-0731`), with
`--reasoning-effort low` (ADR-001 change-log convention to cap reasoning-token cost).
Digest is formatting + rollup of mechanical findings → T3 is correct. (Any *fix
decision* in Phase 2 = T2 `deepseek-v4-pro-0813`; not used here.)

---

## 4. Cron + Tier Assignments

| Job | Type | Cadence (proposed) | Model tier | Python (US-163) |
|-----|------|--------------------|------------|-----------------|
| **System Doctor** (US-158) | agent job wrapping a mechanical collector | `0 6 * * *` | **T3** `deepseek/deepseek-v4-flash-0731` (`--reasoning-effort low`) | dependency-complete venv (`/root/.hermes/installs/<id>/environments/<id>/venv/bin/python3`) |
| **Confidence Digest** (US-161) | agent job (rollup + Discord post) | `0 7 * * *`, `[SILENT]`-suppressed | **T3** `deepseek/deepseek-v4-flash-0731` (`--reasoning-effort low`) | same venv |

Additional tags: both jobs must be flagged `no_agent: false` for the LLM pass but
must call the **mechanical collector** (pure-stdlib or stdlib-complete) as the
primary, threshold-driven detection layer. The LLM (T3) is used **only** to (a)
write coherent `summary`/`fix_suggestion` strings and (b) synthesize the digest —
not to *decide* what is an issue (thresholds decide). This bounds cost and removes
LLM drift from the detection cutoff itself.

### 4.1 Python interpreter — US-163 dependency standardization

**Confirmed problem:** cron `.sh` wrappers resolving bare `python3` resolve to the
**bare tools Python** (`/root/.hermes/tools/python-3.14.x`), which lacks third-party
deps (yaml, mplfinance, discord, etc.). `hermes update` re-stages this interpreter,
wiping manual installs. This is exactly why `discover_connections` (yaml) and the
Daily Signal Scanner (mplfinance) failed.

**Design requirement:**
- The doctor collector + digest MUST invoke the dependency-complete venv interpreter
  explicitly (absolute path) or via a `.sh` wrapper that pins `PYTHONBIN` to that
  venv — **never** bare `python3`.
- Keep the collector **stdlib-only** where feasible (json, pathlib, sqlite3, hashlib,
  subprocess, urllib) so it runs even if a third-party dep is broken — the doctor
  must not depend on the very thing it is checking.
- Flag this clearly in the IMPLEMENTATION CHECKLIST as a US-163 prerequisite: the
  doctor/delevery jobs are **not reliable until US-163 lands**; they should be
  gated behind it.

### 4.2 Model-tier rationale (ADR-001)

- Detection/classification are mechanical + cheap → T3. T2 would waste cost on
  threshold comparisons.
- Digest synthesis is a formatting/rollup task → T3.
- No Phase-1 component makes a *fix decision*, so **T2 is not consumed** in Phase 1.
  T2 (`deepseek-v4-pro-0813`) is reserved for Phase 2 (US-162 sign-off analysis and
  actual fix delegation).

---

## 5. Safety Rails

### 5.1 Read-only, by construction

- The doctor's **only write** is an append to its own queue (`findings.jsonl`) +
  `findings.state.json`. Both live under `cache/system-doctor/`, outside the trading
  pipeline.
- Every probe (Sections 1.1–1.6) is read-only: `stat`, `head`, `grep`, `git status
  --porcelain`, `git fetch --dry-run`, `df`, `systemctl is-active`, `sshd -T`,
  GET `/models`. **No** `pip install`, no `git pull/push/commit`, no file mutation,
  no `systemctl restart`, no secret access.
- The collector must be written so it has no import/flag path that mutates state:
  a code-review acceptance criterion is "the only syscalls with side effects are
  `open(..., 'a')` on the queue + `os.replace` of the state file."

### 5.2 Fail-closed

- If a category cannot produce a verdict (missing cache path, probe error,
  permission denied, jobs.json unreadable), it is recorded as a **`doctor_self`**
  finding (Tier 1) AND listed under "NOT inspected." A scan that crashes is itself a
  finding, never a clean run.
- If the collector crashes before writing findings, the digest job detects the
  absence of a fresh `findings.state.json` and reports "doctor did not complete"
  rather than "0 findings."
- Empty findings + empty state = "doctor never ran on schedule" → reported, not
  silent.

### 5.3 Trading-boundary invariance

- A dedicated digest line (`Trading-boundary anomalies: 0`) is independently derived
  by checking that the doctor never observed a change to kill-switch, size-cap,
  secrets, or `LIVE_TRADING_ENABLED`. The invariance is *verified by absence of
  writes*, not by actively probing secrets (the doctor never reads secret material).
- Any finding classed Tier 2 is immediately `status=open` + surfaced in the next
  digest as "Need sign-off" — it is **never** batched into a Phase-2 auto-fix path.

### 5.4 Anti false-clean ("what was NOT inspected")

- `findings.state.json` records, per category, a `verdict` ∈
  `{clean, finding, not_inspected, error}` + `last_verdict_ts`.
- The digest renders every `not_inspected`/`error` category verbatim. A diagnostic
  run is only "clean" when **all six categories** returned `clean` or `finding` in
  the current cycle.
- The standing `doctor_self` category catches the doctor's own blind spots (a
  detection script that itself went stale, a cache path that was removed, an
  inventory step that was never completed — see D5).

---

## 6. Decisions — RESOLVED (2026-10-31)

All eight resolved per human sign-off; recommendations accepted as-is:

- **D1** → new `#system-doctor` channel (created 2026-10-31).
- **D2** → daily, `[SILENT]`-suppressed.
- **D3** → doctor 06:00 / digest 07:00 UTC.
- **D4** → 90-day JSONL retention, archive monthly.
- **D5** → do the one-time read-only cache inventory.
- **D6** → $8 soft ceiling, trailing-30d (investigation trigger; within the stated $5–8 range).
- **D7** → Phase-1 digest-only; US-162 consumes the same queue later.
- **D8** → gate on US-163 (explicit venv pin, never bare `python3`).

---

*(Original decision rationale below retained for traceability.)*

- **D1 — Digest Discord channel.** A new dedicated channel (e.g.
  `#system-doctor`), or reuse an existing ops channel? Must NOT be
  `#daily-market-briefing`. (Concrete channel ID required before US-161 build.)
- **D2 — Digest cadence.** Daily with `[SILENT]` suppression (proposed), weekly, or
  "daily but only change-summaries"? Daily-silent proposed to bound noise.
- **D3 — Doctor run time.** `06:00 UTC` proposed (after 02:00–05:30 overnight batch).
  Confirm it sees fresh `last_status`.
- **D4 — Queue retention.** How long to keep `resolved`/`digested` findings before
  archive/rotation? (Proposed: 90 days in JSONL, archive monthly.)
- **D5 — Data-freshness inventory.** Exact cache file paths + per-domain staleness
  thresholds for DXY/yields/VIX/F&G/TVL/stablecoin need a one-time read-only
  inventory (a small US-163-adjacent task). Until then `data_freshness` reports
  `not_inspected`.
- **D6 — Cost cap.** Confirm the cap as **$5 or $8**, hard vs soft, and the rolling
  window (proposed trailing-30d, soft ceiling that triggers investigation).
- **D7 — Tier-2 routing.** Should Tier-2 findings flow *only* to the digest, or also
  pre-seed US-162's sign-off queue (they will overlap — decide now to avoid a
  duplicate-queue design).
- **D8 — US-163 gating.** Confirm that doctor/digest jobs are **blocked until
  US-163's interpreter standardization lands** (my recommendation: yes, otherwise
  these jobs inherit the exact cron-Python failure mode they are meant to catch).

---

## 7. IMPLEMENTATION CHECKLIST (for the coder, later — Phase 2+)

Ordered, path-scoped, each step committed immediately (hard rule):

1. **[US-163 prereq]** Standardize the venv Python resolution for cron `.sh`
   wrappers (single `PYTHONBIN` convention). Don't build doctor/digest on the bare
   tools Python.
2. **[US-158 scaffold]** Create `cache/system-doctor/` + `findings.state.json`
   schema + `findings.jsonl` (empty, with a schema comment header).
3. **[US-158 collector]** Implement the stdlib-only collector: probes for 1.1–1.6,
   read-only; writes only queue + state per Section 5.1. Unit-test each probe against
   the three live failing jobs (sweep 22, scanner 27, connection 1) — assert they are
   detected.
4. **[US-158 classification]** Implement Section 1 classification tables (deterministic
   thresholds) + Section 2.4 dedup/idempotency (sha256 key + STALE_WINDOW + count).
   Test re-run produces zero duplicates.
5. **[US-158 T3 pass]** Wrap the collector in a T3 agent job (06:00) that only
   writes `summary`/`fix_suggestion` prose. Route through swarm per HARD RULE.
6. **[US-161 digest]** T3 digest job (07:00) rendering Section 3.2 template to the
   D1 channel, with `[SILENT]` suppression + mandatory "NOT inspected" + "Auto-fixed
   O (Phase 2 not enabled)".
7. **[Safety gate]** Verify: zero writes outside `cache/system-doctor/`; fail-closed
   `doctor_self` on crash; digest renders non-clean only when all six categories
   verdict-finalized.
8. **[Doc]** Commit this spec + a short `system-doctor` README; do NOT wire US-159
   consumption until Phase 2 approval.

Scope guard (reaffirmed): **US-158 + US-161 only.** No auto-fix, no Orchestrator
self-run (US-159), no T1 escalation (US-160), no sign-off queue (US-162) in this
phase. Deferred items are not touched.