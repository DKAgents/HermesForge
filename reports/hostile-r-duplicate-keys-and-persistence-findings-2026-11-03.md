# Findings — hostile R duplicate keys (Q5) + persistence (Q4)

Date: 2026-11-03
Follow-up to US-223.

## Q5 — root cause of the skip+closed duplicate keys

The hostile-fill jsonls are **append-only "transition trails" deduped on
`(signal_id, stage)`** (STR-Q) / `(trade_id, stage)` (swing) — NOT on the trade
identity alone. `hostile_fills_strq.py::_append_report` documents the intent:
"stage preserves the legit skip -> open_entry -> closed transition trail across
cron re-runs."

So a single signal_id can legitimately carry multiple stage rows. The "skip +
closed" duplicates arise because **bar-data availability shifted between
re-runs**: an early cron run wrote `stage:"skip"` (`hostile_fill_reason:"signal
bar not in cached data"` — the 5m bar window was missing/out-of-range), then a
later run wrote `stage:"closed"` once bars were available. The stale "skip" row
is never pruned.

This is NOT corruption — but it is fragile:
- The jsonl grows unboundedly with superseded "skip" rows.
- Any reader must resolve "which stage is authoritative," or it miscounts.
- A "skip" from a *data-gap* is a mis-classification masquerading as a terminal
  "hostile model never entered" verdict.

The US-223 fix already resolves the READ side correctly ("closed row with
non-null hostile_r, latest timestamp wins"), so the report is not wrong today —
but the underlying append-only trail is the debt.

## Q4 — the honest value is not persisted on trades.csv

`trades.csv` has 12,514 rows with zero `hostile_r` column (7,000 have the
cost-adjusted `gauntlet_r`, which is close-fill — NOT the bar-level number). The
bar-level `hostile_r` lives only in the jsonls, keyed by signal_id/trade_id, so
every consumer (report, decay, future analytics) must re-join by identity and
re-resolve the stage ambiguity. Persisting the AUTHORITATIVE `hostile_r` (the
closed stage's non-null value, latest-wins) onto `trades.csv` removes the
jsonl-coupling and the ambiguity in one step.

## Fixes (filed)

- US-224 — persist the authoritative `hostile_r` onto `trades.csv` (schema +
  backfill), consumers read it directly.
- US-225 — prune/stage-authoritative the hostile jsonls so a data-gap "skip" row
  is superseded by a later "closed" row, and the write path no longer accumulates
  a growing trail of stale skip rows.