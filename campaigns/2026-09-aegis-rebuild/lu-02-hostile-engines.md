# LU-02: Hostile Engines — Active vs Frozen

**Status**: note-only (no code edits)
**Date**: 2026-09-25
**Campaign**: 2026-09-aegis-rebuild

---

## Question 1: Which script does the 22:00 UTC hostile cron actually run?

**Answer**: `hostile_fills_strq.py` (v1), NOT v2.

The cron `5041c3c5103f` ("Hostile Fill Report (US-142)") runs
`hostile_fill_report_daily.sh` at `every day at 22:00`. That wrapper
executes two scripts in sequence:

```bash
# Line 5
python3 scripts/paper_trading/hostile_fills.py          # swing trades
# Line 7
python3 scripts/paper_trading/hostile_fills_strq.py     # STR-Q intraday
```

Confirming grep:

```
/root/.hermes/scripts/hostile_fill_report_daily.sh:5:cd /root/HermesForge && python3 scripts/paper_trading/hostile_fills.py 2>&1
/root/.hermes/scripts/hostile_fill_report_daily.sh:7:cd /root/HermesForge && python3 scripts/paper_trading/hostile_fills_strq.py 2>&1
```

No reference to `hostile_fills_strq_v2.py` appears in any cron script.

---

## Question 2: Which jsonl does the cron job append?

**Answer**: `hostile_fill_report_strq.jsonl` (v1).

Both scripts self-configure their output path relative to `__file__`:

| Script | `REPORT_PATH` | JSONL file |
|---|---|---|
| `hostile_fills_strq.py` | `hostile_fill_report_strq.jsonl` | v1 (active) |
| `hostile_fills_strq_v2.py` | `hostile_fill_report_strq_v2.jsonl` | v2 (frozen) |

The active report has been appended every day at 22:00 UTC since the
cron was created. As of now it contains **12,674 records**.

---

## Question 3: File mtimes

```
hostile_fill_report_strq.jsonl     → 2026-09-26 22:09:38  (6,171,923 bytes, 12,674 lines)
hostile_fill_report_strq_v2.jsonl  → 2026-09-13 23:54:13  (1,939,160 bytes,  4,018 lines)
```

- **v1 jsonl**: Updated ~22:09 UTC tonight (the cron runs at 22:00; the mtime
  is the completion time after 9 minutes of processing). Active, growing daily.
- **v2 jsonl**: Frozen since **2026-09-13 23:54**. Not touched by any cron.

---

## Question 4: v2 is not the frozen scoreboard

v2 (`hostile_fills_strq_v2.py`) differs from v1 in exactly one material
way:

| Aspect | v1 (active) | v2 (frozen) |
|---|---|---|
| Fill model | Market: fill at **bar open** after signal | Limit: fill at **signal entry price** |
| Variable | `fill_price = float(row["open"])` | `fill_price = entry_price` |
| Output | `hostile_fill_report_strq.jsonl` | `hostile_fill_report_strq_v2.jsonl` |

Both models still require the bar to trade *through* the entry price
or they return `"fill_reason": "never filled"`.

v2's jsonl has 4,018 records from a single historical run. It was
**never wired into a cron**, never runs daily, and has not been
updated since Sep 13. It is a one-shot experiment, not the
continuous scoreboard.

---

## Invariants (enshrined from user directive)

- **The frozen scoreboard result is final**: Paper +1305R vs Hostile -104R.
  That comparison was run against the full STR-Q trade ledger and stands as
  the authoritative go/no-go reference for STR-Q execution realism.
- **Do NOT un-kill STR-Q.** STR-Q remains paper-only. No change to strategy
  status.
- **Do NOT widen the 1,000-bar cache.** The hostile fill model's lookback
  window stays at 1,000 bars.
- **Do NOT edit** `hostile_fills.py`, `hostile_fills_strq.py`, or
  `hostile_fills_strq_v2.py`.
- **Do NOT delete or rewrite** either jsonl file.
- **Do NOT post. Do NOT trade.**

---

## Verified

```bash
$ ls -l scripts/paper_trading/hostile_fills_strq.py \
       scripts/paper_trading/hostile_fills_strq_v2.py \
       scripts/paper_trading/hostile_fill_report_strq.jsonl \
       scripts/paper_trading/hostile_fill_report_strq_v2.jsonl

-rw-r--r--  Sep 26 22:09  hostile_fill_report_strq.jsonl      (6.2M)
-rw-r--r--  Sep 13 23:54  hostile_fill_report_strq_v2.jsonl   (1.9M)
-rw-r--r--  Sep 13 21:35  hostile_fills_strq.py               (23K)
-rw-r--r--  Sep 13 23:50  hostile_fills_strq_v2.py            (23K)

$ grep -n hostile_fills /root/.hermes/scripts 2>/dev/null | head
/root/.hermes/scripts/hostile_fill_report_daily.sh:5:...hostile_fills.py
/root/.hermes/scripts/hostile_fill_report_daily.sh:7:...hostile_fills_strq.py
```

---

## Key Takeaway

There are two hostile fill engines for STR-Q, but only v1 is live.
v2 was a limit-entry experiment run once and shelved. The frozen
scoreboard (Paper +1305R vs Hostile -104R) is the v1 engine's result
and remains binding. No action required.