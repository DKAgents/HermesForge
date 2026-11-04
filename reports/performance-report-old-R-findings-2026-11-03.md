# Findings — Performance Report still presents optimistic (old) R

Date: 2026-11-03
Request: "I thought we fixed the calculations for this, but it still looks like
the old calculations for R are being used."

## Symptom

The paper-trading performance report leads with:
`Managed: +588.78R · Unmanaged: +3734.48R · +0.93R/trade` — optimistic numbers.

## Root cause — three layered defects

1. **`gauntlet_r` was never the honest R.** The field the report reads
   (`gauntlet_r`, written by `cost_adjuster.py`) is `gross_r − fee_drag`
   (fees/slippage only). It does NOT include the bar-level fill-timing
   correction — the correction that turned STR-Q from ~+1.5k R into −8.4k R.
   `trades.csv` has NO `hostile_r` column (0 of 12,514 rows), so the honest
   bar-level R is not even stored alongside trades.

2. **US-169's "drop the optimistic breakdown" was incomplete.** Commit
   `7fe4518e` ("rewire performance_report to bar-level corrected R, drop
   optimistic breakdown") added a buried one-line "Pessimistic R" section but
   LEFT the optimistic "Managed/Unmanaged" section as the lead. The report is
   byte-identical since that commit — the optimistic breakdown was never
   actually dropped.

3. **The honest bar-level data has degraded beyond recovery.** The STR-Q cruel
   ledger (`hostile_fill_report_strq.jsonl`) now scores only **59 trades =
   −12R**; 9,090 of its 9,149 entries are `stage:"skip"` with
   `hostile_fill_reason:"signal bar not found"`. The historical bar data the
   cruel-fill model needs was purged (US-189: `bars_1d.db` empty, 5m retention
   ~17 days). The −8,447R US-169 computed is no longer recomputable.

## Conclusion

The report reverts to the optimistic `gauntlet_r` because (a) it was never fully
rewired to demote it, and (b) the honest bar-level value is both un-surfaced and
— for the pre-purge window — permanently unrecoverable.

## Proposed fix (narrowest)

1. Rewire `performance_report.py` to lead with the fill-realistic (bar-level)
   R, demote `gauntlet_r` to a clearly-labeled secondary line.
2. Document that the pre-purge bar-level history is unrecoverable; surface the
   current bar-level R honestly, labeled as such.
3. Add a fail-closed guard so an un-fill-realistic R can never be the headline.

→ Filed as US-223.