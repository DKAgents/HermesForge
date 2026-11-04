# Architect Spec — US-222 (Record-Reverse-Engineering Builder + Breaker Harness)

Date: 2026-11-02
Author: Architect (HermesForge)
Status: DESIGN ONLY — input schema + builder objective/parsimony + time-seal +
breaker wiring + synthetic acceptance + intake flag. No code, no gate applied,
no data written. Awaiting swarm review + human approval.
Epic: EPIC-017 (Gauntlet Pipeline Productionization)
Depends on: US-202 (counterparty frontmatter), US-165 (fee_source), PROP-001
(G0–G7), US-174 (G3 fill realism), US-191 (signal class intake), US-215/216
(ledger prior / post-mortem).

Ground truth read:
- 02-Backlog/Stories/US-222-Record-Reverse-Engineering-Builder.md
- trading/proposals/PROP-001-hermes-strategy-gauntlet.md (G0–G7, seed pool)
- scripts/gauntlet/g0_cost_screen.py (cost floor + fee wiring)
- scripts/gauntlet/g3_gate.py (promotion gate, asset/timeframe dispatch)
- scripts/gauntlet/cpcv_harness.py (G4 CPCV + G5 DSR/PBO)
- scripts/gauntlet/trials_ledger.py (append-only ledger, N for DSR)
- scripts/gauntlet/fee_source.py (single fee table; taker/maker per asset_class)
- scripts/gauntlet/hypothesis_register.py + 02-Backlog/Specs/architect_us202… (counterparty field)
- scripts/gauntlet/signal_class.py (US-191 intake gate)
- scripts/gauntlet/funding_state.py (funding_z) + oi_delta.py (oi_quadrant, oi_delta_z)

Summary of what this fills: the gauntlet can TEST any rule (G0→G7) but cannot
RECONSTRUCT one from a dated trade/tax/position record. The headline question —
"does THIS trader's/mine/a fund's actual method have edge?" — is unanswerable by
measurement today. The source methodology (sealed time-split builder→breaker
adversarial pair, "no number reported that wasn't computed") maps ~1:1 onto the
gauntlet, but (a) the BUILDER half is missing and (b) the source runs GROSS of
cost — which we must NOT replicate; we charge fees via fee_source/G3.

---

# PART 1 — Record input format (normalized schema + fail-closed handling)

## 1.1 Canonical schema (JSON; CSV is a flat projection of the same rows)

```jsonc
{
  "instrument": "BTC",            // ticker or universe member
  "venue": "hyperliquid",         // passed through to fee_source asset-class routing
  "asset_class": "crypto",        // "crypto" | "stock" | "option" (fee_source key)
  "timeframe": "5m",              // OPTIONAL hint (5m|1h|6h|1d); if absent, detected
  "source": "record",             // provenance label (coach / self / filing / …)
  "records": [
    {
      "timestamp": "2026-09-01T00:00:00Z",   // REQUIRED (ISO-8601 UTC or epoch)
      "direction": "long",        // REQUIRED: "long" | "short" | "flat"
      "price": 12345.0,           // OPTIONAL (usable for PnL reconstruction only)
      "size": 1.0,                // OPTIONAL (qty / contracts / notional)
      "pnl": null                 // OPTIONAL realized pnl (bps or usd) — recorded, never trusted as input
    }
  ]
}
```

## 1.2 Sparse tolerance — two supported shapes, same target

- **Position snapshots** (monthly/periodic): each row states the position AT that
  timestamp. The state CARRIES FORWARD to the next row (a snapshot at t1 "long"
  remains long until a later row says otherwise). Carry-forward is NOT imputation —
  it is the definition of a position snapshot.
- **Individual fills** (entry/exit events): `direction` = the RESULTING position
  after the fill (or the fill side with an explicit `flat` at exit). Consecutive
  fills collapse to a stepwise state timeline.

The builder's reconstruction target is the **state timeline** (long/short/flat
over time), not the fills themselves. `flat` is a first-class state — cash timing
is part of what we reproduce.

## 1.3 Missing/partial fields — fail-closed, never silently imputed

| Field missing | Handling |
|---|---|
| `timestamp` | Row DROPPED entirely (cannot place in time); reported in a coverage count. |
| `direction` | Row EXCLUDED from the target timeline (cannot infer in/out); reported. Never guessed from price. |
| `price` | Row still usable for direction timing; PnL reconstruction for that row is BLOCKED. |
| `size` | Row still usable for direction; PnL reconstruction for that row is BLOCKED. |
| `pnl` | Optional. If absent, harness computes PnL from price+size only where BOTH are present; otherwise reports "no record PnL", does NOT fabricate one. |

Unknown regions (before the first row; after the last row unless it is `flat`)
are EXCLUDED from agreement scoring — they are unknowable, so they are not
counted as either a match or a miss. The harness reports a **coverage** numerator
(observations actually scored) separately from total rows, so a sparse record
cannot silently inflate or deflate agreement.

Rule: the only sanctioned "fill" is EXCLUSION with a report. There is no
imputation path into a backtest.

---

# PART 2 — Builder (rule reconstruction)

## 2.1 Feature library (SMALL, pre-enumerated)

Price-derived:
- `sma_cross_above(n)`  → long when close crosses above SMA(n); exit/flat when crosses below.
- `sma_cross_below(n)`  → short on the inverse crossing.
- `momentum(n, k_bps)`  → long when n-bar return > +k bps; short when < −k bps.
- `breakout_high(n)`    → long when close breaks above the n-bar high.
- `breakout_low(n)`     → short when close breaks below the n-bar low.

Positioning:
- `funding_extreme(z, side)` → long/short when `funding_z` crosses ±z (fade or follow, stated side).
- `oi_change(dz, side)`      → long/short when `oi_delta_z` crosses ±dz.

Each family carries a SMALL discrete parameter grid (n, k, z, dz). The builder
searches single features first, then at most 2-feature conjunctions/disjunctions.
(Exact grid values and whether 2-feature search is in scope at all: see Open Q1,
Q2 — a feature is not invented; each is a thin wrapper over an existing primitive
`compute_funding_z`, `compute_oi_delta_z`, or a rolling window over `close`.)

## 2.2 Objective (agreement %, penalized for feature count)

```
score(rule) = agreement_IS(rule) − λ · feature_count(rule)
```

- `agreement_IS(rule)` = fraction of scored in-sample (train) observations where
  the rule's reproduced state == the record's state timeline.
- `feature_count` = number of primitive features in the rule (1 or 2).
- `λ` = parsimony penalty (see Open Q3).

## 2.3 Parsimony rule (binding discipline)

The builder does NOT return the max-agreement rule. It returns the rule with the
**fewest features** that reaches a minimum in-sample agreement, and — among equal
feature counts — the highest agreement. A k+1 feature rule is only chosen over
the best k-feature rule if it improves `agreement_IS` by at least margin `β`.
Rationale (from the story): a bigger feature set can always fit any record
(overfit); the prefer-fewest rule biases toward the explanation most likely to
HOLD out-of-sample. Final arbitration is the breaker (Part 4), not the builder.

## 2.4 Rule emission — auditable + in-sample accuracy

- The rule is emitted as **structured, deterministic code** (a JSON `rule` dict:
  `{feature, params, direction, exit}` + an equivalent Python function generated
  from a template), NOT an opaque free-form blob.
- Each emission carries a `param_hash` (stable sort of feature+params) so the
  trials ledger can dedupe and so the same rule re-runs identically.
- The emission records `agreement_IS`, the number of scored observations, the
  feature count, and the feature library VERSION (so a later library change never
  silently re-means an old rule).

---

# PART 3 — Time-seal (critical — no random split)

## 3.1 Split rule

- Sort records by `timestamp` ascending.
- `t_split` = the timestamp at the **chronological midpoint** of the record's time
  span (default 50/50; see Open Q4 for fraction).
- **Train** = rows with `timestamp < t_split` (the OLDER half — builder sees only this).
- **OOS / sealed** = rows with `timestamp ≥ t_split` (the RECENT half — builder never sees it).

A **random split is FORBIDDEN**: it scrambles temporal order and lets the future
leak into training. The builder must never know the sealed half before the breaker
runs it.

## 3.2 Boundary purge

Any train row whose carried-forward state would still be "open" at `t_split` (a
position entered in the train half and not yet flattened at the split) is EXCLUDED
from the boundary region — its continuation leaks into OOS. (Equivalent to the
CPCV purge, applied at the single split boundary.)

## 3.3 Data-gate (decline, don't force)

A record is DECLINED as "data-gated" (not reconstructed under a forced split) if it
does not contain enough **state TRANSITIONS** to measure agreement, i.e.:

- too few rows in the OLDER half to build (or fewer than a minimum number of
  long/short/flat transitions, not just rows), OR
- too few transitions in the SEALED half to measure OOS agreement.

The transition-count floor (not a raw-row floor) is the load-bearing guard: a
record that is `flat` throughout has zero signal and ANY rule trivially
"reproduces" it — this must be declined rather than scored. Exact thresholds:
see Open Q5.

---

# PART 4 — Breaker / harness

## 4.1 OOS reproduction (the "learned the market or just this record?" test)

1. Replay the reconstructed rule on the SEALED recent half.
2. Compute `agreement_OOS` (same state-timeline agreement, over the sealed half).
3. Compare `agreement_IS` vs `agreement_OOS` against a **no-skill baseline** (the
   agreement of a trivial always-`flat` rule, and/or the state-imbalance chance
   level). If `agreement_OOS` collapses below the no-skill floor, verdict =
   "learned the record, not the market" → the rule is NOT advanced (it is a
   diagnostic of the trader's method — see Part 6).

## 4.2 Gauntlet handoff — fees CHARGED (the source's known gap, closed)

Only a rule that clears OOS reproduction is handed to the gauntlet. Order and fees:

- **G0 cost** — `g0_cost_screen.screen(...)`, with round-trip fees from
  `fee_source` (taker by default; maker only if G3 demonstrates passive fills —
  ADR-009 fail-closed). The source methodology runs GROSS of cost; we DO NOT.
- **G3 fill realism** — `g3_gate.evaluate_fill_realism(...)` / `promote_strategy`,
  routing by `asset_class`+`timeframe` exactly as G3 dispatches today (intraday
  crypto → `execution_sim` L2; else bar-level hostile: next-open + `compute_cost_drag`
  from `fee_source`). G3 is mandatory and fail-closed.
- **G4 / G5** — only if the rule survives G3. G4 = `cpcv_harness.run_cpcv`
  (CPCV splits + PBO); G5 = DSR/PBO read against the trials ledger N
  (`trials_ledger.count()`).

## 4.3 Trials ledger (every run counts toward G5)

Every builder+breaker run writes exactly ONE entry via
`trials_ledger.increment_trial(hypothesis_id, param_hash, universe_hash, …)` so
G5's DSR reads the growing N and the US-215 ledger-prior can later suppress
re-proposed mechanisms. No run produces a reported metric without writing the
trial.

## 4.4 "No number reported that wasn't computed" (binding invariant)

Every metric in the report is produced by an actual computation on actual data.
A metric that cannot be computed (insufficient rows, missing price/size for PnL,
degenerate split) is reported as `not_computed` / `insufficient_data` with a
reason — never a placeholder, never a default, never a gross-of-cost shortcut.
This mirrors `fee_source`'s fail-closed fallback and Part 1's exclusion rule.

---

# PART 5 — Synthetic validation (acceptance)

Two hermetic, deterministic (seeded) fixtures. No network, no real record.

## 5.1 Fixture A — KNOWN rule (recover AND confirm OOS)

- Seed a PRNG; synthesize an OHLC series with a KNOWN regime, then GENERATE the
  record by applying a fixed rule, e.g. `long when close > SMA(n=10), flat
  otherwise` (a small `n` so the record carries many transitions).
- **Builder pass:** recovered rule's feature FAMILY must be EXACT (SMA-cross),
  and its parameter must match within the library's grid tolerance (recovered
  `n` within the small grid envelope around 10). A recovered `breakout` when the
  truth is `sma_cross` = FAIL.
- **Breaker pass:** `agreement_OOS` on the sealed half ≥ floor (the rule holds
  OOS because the signal is real and deterministic).

## 5.2 Fixture B — OVERFIT record (rebuild allowed, breaker must KILL)

- Generate a record from a rule that fits NOISE with zero true signal (e.g. a
  signal whose "entries" are seeded coin flips that happen to line up with a
  price series — high IS agreement by construction, no OOS content).
- **Builder MAY rebuild it** (high `agreement_IS` is EXPECTED — the builder's job
  is reconstruction, not judgment).
- **Breaker pass = it KILLS it:** `agreement_OOS` collapses below the no-skill
  floor AND/OR G3 rejects (realistic mean R ≤ 0, pessimistic PF ≤ 1.0). The
  harness must emit "no claimable edge under realistic fills", and the rule is
  NOT promoted.

## 5.3 Pass/fail thresholds

The EXACT numeric floors (agreement floor for A, no-skill floor + G3 reject for
B, grid-tolerance envelope around recovered params) are TUNABLE and flagged as
open (Open Q6). The INVARIANT is structural, not numeric: A must be recovered
and confirmed, B must be killed OOS. If either fixture's invariant fails, US-222
acceptance fails regardless of any threshold tuning.

---

# PART 6 — Intake: counterparty flag (never auto-promote without a counterparty)

## 6.1 Where the counterparty requirement lives

Reconstructed rules enter as hypotheses through the EXISTING US-202 frontmatter:
the mandatory `counterparty` field lives in `hypothesis_register.REQUIRED_FIELDS`,
validated by `validate_frontmatter` at intake, before G0. The builder/harness does
NOT bypass this — a reconstructed rule is a hypothesis first.

## 6.2 The diagnostic marker (new, binding)

A reconstructed rule with **no structural counterparty** (empty/un-reason-able
`counterparty`) is a **DIAGNOSTIC**, never auto-promoted:

- The intake step marks the record `diagnostic: true` + a `reason` at write time.
- A `diagnostic: true` rule is BLOCKED from promotion to Active/Live even if it
  later passes G3/G4/G5. It must be human re-authored with a reasoned counterparty
  (which clears `diagnostic`) before any promotion path opens.
- It is RETAINED (for the "we measured it, here's what we found" use case), not
  deleted — contrast with US-202's hard reject, which deletes nothing but refuses
  to register a non-conforming NEW hypothesis. A diagnostic is registered, but
  locked to diagnostic status.

## 6.3 Interaction with US-191 (signal-class gate) — flagged

A reconstructed rule is still subject to the US-191 intake gate. Because
`sma_cross` and `breakout` are exactly the retail-TA keyword families in
`signal_class`, a reverse-engineered "SMA-cross" rule would be fast-failed at
intake as a negative-prior class. This is TENSION worth resolving explicitly:
the builder's purpose is DIAGNOSTIC (measure an external trader), so a recovered
retail-TA rule should be REPORTED as "this method is a retail-TA pattern — negative
prior, likely no OOS edge" rather than silently passed OR silently blocked. See
Open Q7.

---

# Open questions (flagged — no number asserted as fact)

- **Q1** Feature-library parameter grids: exact `n`/`k`/`z`/`dz` values per family.
  Not fixed here; must be a SMALL grid so the search stays cheap and the
  multiple-testing burden (G5) stays tractable.
- **Q2** Is 2-feature search in scope at all, or is US-222 single-feature-only
  for v1 (parsimony leans single-feature; a 2nd feature must clear margin `β`)?
- **Q3** `λ` (objective penalty) and `β` (feature-addition margin). The
  prefer-fewest rule (§2.3) is the binding discipline; these are tuning constants.
- **Q4** Split fraction — default 50/50, but a 60/40 or 70/30 (train/OOS) may be
  warranted for very short records; the "seal recent, chronological, never random"
  principle holds regardless.
- **Q5** Data-gate thresholds: minimum transition counts for train and sealed
  halves (NOT raw-row counts). Values undefined — principle is define-and-decline,
  don't force.
- **Q6** Synthetic threshold magnitudes: agreement floor (A), no-skill floor +
  param-grid tolerance (B).
- **Q7** Builder vs US-191: how a reconstructed retail-TA rule is surfaced
  (report-as-diagnostic vs blocked-at-intake) — needs a decision; both paths must
  never auto-promote.
- **Q8** Market-data dependency: the builder reconstructs SMA/momentum/funding/OI
  rules from the instrument's BAR SERIES (OHLC + funding + OI), not from the
  record alone. Confirm the record must resolve to a stored/feeder-backed series
  (parquet/feeds) for `instrument` over the record's date range, and that a
  missing series declines the build (data-gated), not fabricates prices.
- **Q9** `record`-vs-computed PnL: the record's own `pnl` column is provenance
  metadata, never a backtest input (fail-closed: backtest PnL is always recomputed
  from price/size × fee_source). Confirm this is non-negotiable.

END OF DESIGN.