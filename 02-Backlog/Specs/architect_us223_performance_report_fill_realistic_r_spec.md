# Architect Spec — US-223 (Performance report leads with fill-realistic R)

Date: 2026-11-04
Author: Architect (HermesForge)
Status: DESIGN ONLY — R source-of-truth + coverage labeling + fail-closed guard +
ledger aggregation. No code changed, no data written, no ledger touched, no
threshold invented. Awaiting swarm review + human approval.
Epic: EPIC-017 (Gauntlet Pipeline Productionization)
Depends on: US-169 (regenerate STR-Q ledger / rewire report), US-189 (bar
ingestion — the cause of the purge), US-142 (hostile fill model), US-123
(append-only journal).

Ground truth read:
- 02-Backlog/Stories/US-223-Performance-Report-Fill-Realistic-R.md
- reports/performance-report-old-R-findings-2026-11-03.md
- scripts/paper_trading/performance_report.py
- scripts/paper_trading/trade_log.py (FIELDS — no `hostile_r` column)
- scripts/paper_trading/hostile_fills.py + hostile_fills_strq.py
- scripts/paper_trading/hostile_fill_report_strq.jsonl (v1, active)
- scripts/paper_trading/hostile_fill_report_strq_v2.jsonl (frozen)
- scripts/paper_trading/hostile_fill_report.jsonl (swing)
- campaigns/2026-09-aegis-rebuild/lu-02-hostile-engines.md (v1 active vs v2 frozen)

Summary of the defect: the report's headline reads `gauntlet_r` (gross_r −
fee_drag, fills at signal close, no bar-level fill-timing correction) and prints
optimistic +0.93 R/trade. The honest bar-level `hostile_r` exists only in the
hostile-fill jsonls, is (a) absent from `trades.csv` (0 of 12,514 rows have a
`hostile_r` column), (b) surfaced as a single buried STR-Q-only line, and (c)
post-purge reduced to 59 scored trades = −11.7 R. This spec defines the single
R source-of-truth, the coverage window labeling, the fail-closed guard, and the
ledger aggregation, without inventing any threshold.

---

# PART 1 — R source-of-truth (single helper, resolved order)

## 1.1 Two R values, one function

There are exactly two R quantities in play; every consumer goes through ONE
helper to resolve headline vs secondary:

| Name | Definition | Fill-realistic? |
|---|---|---|
| `hostile_r` | Bar-level fill-timing corrected R (fill at t+1 open only if bar trades through level; taker fee/slippage; time-stop worst print). Read from the hostile-fill jsonls. | YES — source of truth |
| `gauntlet_r` | `gross_r − fee_drag` from `cost_adjuster.py`; fills at signal close; no bar-level fill-timing correction. Stored in `trades.csv`. | NO (cost-adjusted only) |

## 1.2 Resolution order (binding)

The helper `resolve_fill_realistic(closed_rows) -> {summary, per_trade_map}`:

1. **Primary** — join each closed trade to a bar-level `hostile_r` from the
   hostile-fill jsonls (join key per strategy — see Part 4). This is the ONLY
   value ever permitted as the headline.
2. **Secondary** — `gauntlet_r` (or raw `r_multiple` fallback) is computed ONLY
   to render the explicitly-labeled "not fill-realistic" secondary line. It is
   never permitted to substitute for a missing `hostile_r` in the headline.
3. **Unavailable** — if a given closed trade has no joinable `hostile_r` (purged
   bars, skip stage, open/not-yet-scored), that trade contributes NO fill-realistic R.
   It is counted in a coverage denominator, not silently dropped, and not silently
   filled with `gauntlet_r`.

The helper returns a structured result carrying BOTH quantities plus the
coverage split — callers (the report) decide presentation, but the helper makes
impossible the mistake of passing `gauntlet_r` through the primary slot.

## 1.3 Missing/unavailable rendering (never a silent fallback)

- If the fill-realistic resolution yields **zero scored trades** for the window,
  the headline line MUST read, verbatim in intent: **"Fill-realistic R: unavailable
  for this window"** — plus the reason (no ledger / no scored rows / purge), plus
  the window it WOULD have covered. It must NOT print `gauntlet_r` in that slot.
- If the fill-realistic resolution yields **partial** coverage (some trades have
  `hostile_r`, some do not), the headline states the scored denominator
  ("N fill-realistic trades of M closed") and the bare count of the unscored
  remainder — an explicit gap, not a hidden one.
- The optimistic `gauntlet_r` line, if shown, is ALWAYS prefixed/labeled
  "not fill-realistic" (e.g. "_Cost-adjusted only (NOT fill-realistic): …_"),
  matching the story's acceptance that the optimistic number, if shown at all,
  is labeled so. Design decision: it is shown, demoted, because the story and
  findings assume its continued presence is tolerable once clearly labeled; its
  total omission is left to the coder only if the publisher agrees (see Open Q1).

---

# PART 2 — Coverage window labeling (honest partial number)

## 2.1 What the fill-realistic number covers

The report MUST state, adjacent to the fill-realistic headline, the **coverage
window** the number actually spans:

- The **min–max entry_date** of the scored (fill-realistic) hostile rows in the
  union of ledgers for this report window — NOT the report's `--since` window,
  which is broader but mostly unscorable for pre-purge history.
- A plain statement that the fill-realistic R is **post-retention only**: the
  bar history needed by the cruel-fill model was purged (US-189; `bars_1d.db`
  empty, 5m retention ~17 days), so **pre-purge bar-level R is unrecoverable
  and is not — and cannot be — restated** here.
- When the scored set is empty or trivially small, this labeling must not
  quietly disappear: the window line still prints with an explicit "no scored
  trades in window" and the purge note.

## 2.2 Anti-misleading contract

The reader must never be led to believe a 59-trade −11.7 R partial number is the
full historical P&L. This is enforced structurally (Part 3) AND narratively
(the window + purge sentence is mandatory text, not optional prose). The phrase
"−8,447 R" (US-169's pre-purge figure) is NEVER re-printed as a current result;
if referenced at all it is only as an explicitly-dated historical number that is
"no longer recomputable."

---

# PART 3 — Fail-closed guard (binding)

## 3.1 Invariant

> The report NEVER presents an un-fill-realistic R (`gauntlet_r` / `r_multiple`)
> as its headline.

## 3.2 Structural enforcement (two layers)

1. **Type-level / API-level**: the headline is produced by a dedicated emitter
   that accepts ONLY the primary resolution result (Part 1.2 step 1). The
   `gauntlet_r` value lives in a separate field and a separate emitter that is
   incapable of writing into the headline slot. (No string interpolation that
   silently co-mingles the two.)
2. **Test**: an acceptance test constructs a window where fill-realistic R is
   unavailable (empty ledger / all-skip rows) and asserts:
   - the headline string contains "unavailable" (not a number, not `gauntlet_r`);
   - the demoted `gauntlet_r` total, if present, is absent from the headline slot
     and present only in the labeled "not fill-realistic" line;
   - the coverage/purge sentence is present.
   A second test asserts the reverse: when `hostile_r` IS available, the headline
   number equals the summed `hostile_r` (not `gauntlet_r`), even when the two
   disagree by a large margin (the exact −11.7 vs optimistic delta is the fixture).

## 3.3 Nonnegotiable

This guard is fail-CLOSED: absence of fill-realistic data yields an explicit
"unavailable" headline, and cannot be bypassed by a fallback. No threshold is
introduced (no ">N trades required" floor) — the design asserts availability
vs non-availability only; any minimum-sample gating is deferred (Open Q2).

---

# PART 4 — Ledger coverage + aggregation without double-count

## 4.1 Which strategies have a bar-level hostile ledger

Three jsonls exist; exactly TWO are authoritative for the report:

| Ledger | Engine | Strategies | Status | Join key |
|---|---|---|---|---|
| `hostile_fill_report_strq.jsonl` | `hostile_fills_strq.py` (v1) | `STR-Q-liquidity-sweep` | ACTIVE (cron 22:00 UTC) | `signal_id` |
| `hostile_fill_report.jsonl` | `hostile_fills.py` (daily) | `STR-VIXC-vix-contango-breakout`, `STR-B-macd-histogram-divergence`, `STR-A-ma-pullback-fibonacci`, `STR-I-adaptive-trend`, `STR-D-sr-role-reversal`, `STR-DEBASEMENT-treasury-buyback` | ACTIVE (cron 22:00 UTC) | `trade_id` |
| `hostile_fill_report_strq_v2.jsonl` | `hostile_fills_strq_v2.py` | `STR-Q-liquidity-sweep` | **FROZEN** (limit-fill experiment, never cron-ed, last written 2026-09-13) | — |

The v2 ledger is **excluded**: it is a superseded one-shot experiment whose
fill model differs (limit vs market) and whose values are not the corrected
bar-level numbers. lu-02 enshrines v1 as the authoritative scoreboard. Reading
v2 into the headline would double-count the same STR-Q trades under a different
fill assumption. (`.bak.us169` is a backup; never read.)

## 4.2 Join-key asymmetry (why both keys are needed)

- **STR-Q**: `trade_id` is `STRATEGY_TICKER_YYYY-MM-DD` (date only), so multiple
  intraday entries share one `trade_id`. The ledger's `signal_id` carries the
  HHMM suffix and is the unique per-entry key. STR-Q joins on `signal_id`.
- **Swing (daily)**: one entry per ticker per day; `signal_id == trade_id`, and
  the swing ledger records only `trade_id` (no `signal_id` field). Swing joins on
  `trade_id`.

The helper selects the join key by `strategy_id` (STR-Q → `signal_id`; the six
swing strategy IDs → `trade_id`).

## 4.3 Deduplication rules (three axes, defense-in-depth)

1. **Within-ledger duplicate stage rows**: a single `signal_id` (STR-Q) or
   `trade_id` (swing) can appear in MULTIPLE rows across stages
   (`skip` → `entry` → `open` → `closed`). Observed: 58 STR-Q `signal_id`s have
   both a `closed` and a `skip` row; 40 swing `trade_id`s span multiple stages.
   Rule: the canonical hostile row for a key is the **`closed` row with
   non-null `hostile_r`**; on multiple such rows, the **latest `timestamp_utc`**
   wins. A key with only `skip`/`open`/`entry` rows contributes no fill-realistic
   R but is counted in the unscored remainder.
2. **Outlier exclusion**: honor the existing `outlier_excluded` flag (STR-Q v1
   ledger): an `outlier_excluded: true` scored row is excluded from the scored
   sum, consistent with the US-168 v3 "scored" population. (Currently 0 of 59
   scored rows carry `true`, but the rule is binding for future writes.)
3. **Cross-ledger overlap**: assert the two active ledgers' strategy-id sets are
   disjoint (they are — STR-Q vs six swing IDs) and therefore a canonical
   `(strategy_id, key)` pair cannot resolve in both. Defensively, the helper still
   dedups by canonical `(strategy_id, key)` and aborts loudly (not silently)
   if a duplicate resolution is detected across ledgers. The frozen v2 ledger is
   simply not loaded — that IS the cross-ledger de-dup for STR-Q.

## 4.4 Aggregation

The fill-realistic headline aggregates the **scored-and-deduped** hostile rows
across BOTH active ledgers (STR-Q v1 + swing), keyed as above, using the
`outlier_excluded=false` population. Per-strategy breakdown is surfaced from the
same single deduped map (no second independent read that could double-count).

---

# PART 5 — Report structure (target layout)

Order of sections (design intent; exact prose is coder+'s word choice under
publisher review):

1. **Fill-realistic R (headline)** — summed `hostile_r`, scored-trade count,
   win rate, and the coverage window + purge sentence (Part 2). If unavailable:
   the explicit "unavailable" sentence (Part 1.3).
2. **Cost-adjusted only (NOT fill-realistic)** — summed `gauntlet_r` (the old
   Managed/Unmanaged lead), demoted and labeled.
3. **Open positions** (unchanged).

The "Managed/Unmanaged" simulation and its `gauntlet_r`-based math remain,
but ONLY inside section 2, clearly labeled, and never as the lead.

---

# Open questions (flagged — no number asserted as fact)

- **Q1** Is the optimistic `gauntlet_r` line retained-but-labeled, or fully
  removed? The findings' "narrowest fix" and the story's "if shown at all"
  both permit retention; full removal is a publisher call (branding/cadence),
  not an accounting call. This spec assumes retained-and-labeled; coder should
  confirm with the publisher before removing it entirely.
- **Q2** Should there be a minimum-sample gate on the fill-realistic headline
  (e.g. "too few trades to interpret")? The story does not ask for one; this
  spec asserts availability only. Any such floor is a product decision, not
  invented here.
- **Q3** Swing-ledger provenance under the same purge: the swing
  `hostile_fill_report.jsonl` still scores 44 trades back to 2026-09-01 using
  cached parquet daily bars, while STR-Q degraded to 59 trades (5m retention).
  Confirm the swing daily-bar source is NOT subject to the same US-189 purge
  that emptied `bars_1d.db` / truncated 5m — i.e. verify the swing ledger's
  fill-realistic window is genuinely broader, not a stale cache. This affects
  the coverage-window sentence's accuracy.
- **Q4** `trades.csv` has no `hostile_r` column (0/12,514 rows). Persisting
  `hostile_r` onto the trade row (a schema addition to `trade_log.FIELDS`) would
  make the report join trivially and future-proof the number against further
  ledger churn. That is a SEPARATE story (schema + backfill + writer change),
  out of scope for US-223 — flagged here as the likely follow-up so the report
  is not permanently jsonl-coupled.
- **Q5** The 58 STR-Q duplicate `signal_id`s (closed+skip) and the 40 swing
  multi-stage `trade_id`s are assumed to be legitimate append-only stage
  transitions, not write corruption. The dedup rule (4.3#1) handles both, but a
  root-cause check of WHY a key gets both a skip and a closed row would confirm
  it is re-scoring rather than a duplicate-write bug (the same class US-123/
  `_dedupe_rows` guards against in `trades.csv`).

END OF DESIGN.