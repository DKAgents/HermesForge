# LU-03c: Hostile R Sum — Why +1163R ≠ -104R

**Status**: note-only (no code edits)
**Date**: 2026-09-27
**Campaign**: 2026-09-aegis-rebuild

LU-03b rejected. The jsonl sums to +1163R but the frozen scoreboard says
-104R. This note explains why.

---

## From the jsonl

```
Record count:         12,674
  Skip (hostile_r=None):  5,013  (signal bar not in cache — no fill possible)
  Valid (hostile_r set):  7,661

Sum hostile_r:       +1163.20
Sum paper_r (same records): +5663.99

Min date:            2026-09-06
Max date:            2026-09-26
```

---

## Pre- vs Post-Cutoff (2026-09-13)

| Window | Records | Hostile R |
|---|---|---|
| Before 2026-09-13 | 1,452 | **-119.38** |
| On/after 2026-09-13 | 6,209 | +1282.57 |
| **Total** | 7,661 | +1163.20 |

The frozen scoreboard (-104R) was a snapshot when only 1,452 valid records
existed, all before Sep 13. The pre-cutoff hostile R of -119.38 is
consistent with the frozen -104R.

Since Sep 13, the jsonl has absorbed 6,209 additional records (5× the
original count), and those later records are overwhelmingly positive under
hostile fills (+1282.57R). The cumulative sum drifted from negative to
strongly positive.

**Are rows after 2026-09-13 in the sum?** Yes — 6,209 of 7,661 valid
records are post-cutoff. The post-cutoff data dominates 5-to-1, flipping
the sign from -119R to +1163R.

---

## Why the Cron Reports a Smaller Number

The 22:00 UTC cron prints `Hostile R sum: 362.50` (Sep 26 output). This is
the current-run delta — only new records written since the last run — not
the cumulative. The jsonl is append-only across days; the cron summary is
per-invocation. Reading the jsonl in full gives the cumulative +1163.20.

---

## Implications

- The frozen scoreboard (-104R) accurately reflected the data available at
  the time (pre-Sep-13).
- Post-Sep-13 data shows STR-Q performing significantly better under
  hostile fills. Whether this reflects a regime shift, gauntlet-quality
  improvements, or an expanding sample is not determined here.
- The cumulative hostile R (+1163R) and paper R (+5664R) both run positive.
  Hostile R is ~21% of paper R — a realistic discount, not an erasure.

---

## Invariants

- **Do NOT edit** the jsonl.
- **Do NOT edit** `performance_report.py`.
- **Do NOT post.**
- **Do NOT un-kill STR-Q.**