# LU-06: Research Gate — Can a New Idea Skip the Hostile Pass?

**Status**: note-only (no code edits)
**Date**: 2026-09-25
**Campaign**: 2026-09-aegis-rebuild

**Directories examined**: `06-Strategies/`, `05-Research/Strategy-Validation/`

---

## Answer: Yes — a new idea reaches `capture_signals.py` with NO hostile pass

The pipeline has no hostile-fill gate. A strategy idea becomes an active,
auto-scanned paper strategy through frontmatter alone.

### The actual path (as it exists today)

1. **Drop a file** in `06-Strategies/Hypotheses/STR-*.md` with YAML frontmatter:
   - `status: watch` (or `status: live`)
   - `strategy_id: STR-X-whatever`
   - `scanner_alias: scan_xx` (must match a key in `_SCANNER_ALIASES`)

2. **`_discover_strategies()`** (capture_signals.py:178-230) globs
   `Hypotheses/STR-*.md`, reads frontmatter, and auto-includes any file whose
   `status ∈ {live, watch}` and whose `scanner_alias` resolves to an imported
   scan function.

3. **Next run, `capture_signals.py` auto-scans it**, routes any signal through
   the Jev prefilter (quality gate only — see LU-04), and writes the result to
   `trades.csv` via `trade_log.open_trade()`.

### What gates DO exist

| Gate | What it checks | Is it a hostile pass? |
|---|---|---|
| `status: watch/live` frontmatter | A metadata flag — flipped by a one-line edit | No |
| `scanner_alias` resolution | That a Python function exists | No |
| Jev prefilter | Signal coherence / R:R reasonableness (3 noul calls) | No |
| T1 gate (`T1_ENABLED`) | Phase 1A candidates kept OFF by default | No |

**None of these require a hostile fill series.** The hostile fill model —
`scripts/paper_trading/hostile_fills_strq.py` — runs as a **separate daily
cron** (22:00 UTC) and is hard-scoped to STR-Q only. It is a *reporting
artifact*, not an entry gate. It never blocks a strategy from entering the
capture pipeline.

### Evidence

- `grep -l hostile 06-Strategies/Hypotheses/*.md` → only 3 T1 files.
- Of **33 hypothesis files**, only **10** mention walk-forward / out-of-sample /
  hostile validation at all.
- `capture_signals.py` has **zero** references to `hostile_fills` — the word
  does not appear anywhere in the capture path (grep confirmed empty).
- The comment at capture_signals.py:188-189 states the intended onboarding
  flow is literally "create hypothesis file with `status: watch` … →
  auto-scanned. No code change needed."

So today, a brand-new idea can be flipped to `status: watch`, and it will open
paper trades next capture cycle — **before any out-of-sample, leakage, trial,
or hostile-fill validation has run.**

---

## Required Gate (do not implement here)

A new idea must pass, in order, before it may auto-scan into paper:

1. **Hypothesis** — a falsifiable claim: entry condition, exit condition,
   expected edge, and a pre-registered kill rule.
2. **`shift(1)`** — no look-ahead: every feature computed on bar *t* uses only
   information available at or before *t*. Predictor at *t* → target at *t+1*.
3. **Leakage check** — no target implicitly embedded in features (e.g. close-
   derived RSI feeding a same-bar close target).
4. **Trial count** — N pre-registered trials; the number is fixed before any
   parameter search, and the search itself counts against the trial budget.
5. **Walk-forward on the worst fold** — the strategy must survive its *worst*
   out-of-sample fold, not just the aggregate; report the worst-fold R, not
   the average.
6. **Hostile fill as the label** — the training/validation signal label must be
   the hostile-fill outcome (fill at realistic levels, taker fees applied),
   not the idealized paper exit.

Only after all six, may the hypothesis file be flipped to `status: watch`.

### Explicit constraint

**Do NOT vendor the Insider post's code.** Any gate implementation must be
built from the HermesForge codebase and its own hostile-fill model. Do not
copy, adapt, or inline code from the referenced external post.

---

## Standing Truths

- **T1 stays OFF.** `T1_ENABLED` defaults to false (env `HERMESFORGE_T1_ENABLED`
  unset → false). Passing `--enable-t1` is a manual, deliberate act. Do not
  flip it.
- **Paper R is not a ship signal.** A positive `r_multiple` in `trades.csv` is
  a simulated outcome. It does not authorize live capital. The hostile fill
  series is the only tradability reference.
- **Frozen STR-Q scoreboard**: Paper +1305R vs Hostile -104R. This remains the
  authoritative go/no-go reference. Do not un-kill STR-Q.

---

## Invariants

- **Do NOT add** new scanner functions or `_SCANNER_ALIASES` entries.
- **Do NOT edit** STR-Q or hostile-fill code.
- **Do NOT enable** T1.
- **Do NOT widen** the 1,000-bar cache.
- **Do NOT post. Do NOT trade.**

---

## Verified

```bash
$ test -d 06-Strategies && test -d 05-Research/Strategy-Validation && echo OK
OK
```

`06-Strategies/` contains `Hypotheses/` (33 files), `Active/`, `Backtests/`,
`Live/` (empty), `Regimes/`, `Failure-Modes/`, `Deprecated/`.
`05-Research/Strategy-Validation/` contains only `STR-H-*` (a single
walk-forward example) — no reusable gate pipeline.

---

## Key Takeaway

A new trading idea reaches `capture_signals.py` by a frontmatter flag flip,
with no hostile fill, leakage, or walk-forward check in the path. The hostile
fill model is a separate reporting cron scoped to STR-Q. The six-step research
gate (hypothesis → shift(1) → leakage → trial count → worst-fold walk-forward
→ hostile-fill label) is required but not yet implemented.