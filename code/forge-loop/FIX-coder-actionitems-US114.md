# US-114 Coder Action Items — Completed

**Date:** 2026-08-16
**Commit:** 9750778 — `US-114: Update strategy statuses, verify wiring, add STR-AJ concentration control`
**Agent:** Coder (HermesForge swarm, T2)

---

## ACTION 1 — strategy_status.py Status Updates

**File:** `scripts/discord/strategy_status.py`

### Changes Made

| Strategy | Previous | New | Reason |
|----------|----------|-----|--------|
| STR-S (Elliott Wave) | LIVE | KILLED | US-114 v2: no edge after look-ahead fix removal (p=0.069, avg R=0.077) |
| STR-AH (Island Reversal) | LIVE | KILLED | US-114: survivorship bias artifact (84% time exits, beta not edge) |
| STR-Y (ADX/DMI) | LIVE | WATCH | US-114: OOS not significant, pending parameter sensitivity review |
| STR-AI (Seasonal) | LIVE | WATCH | US-114: OOS not significant, pending parameter sensitivity review |

### Verification — LIVE Strategies (15 confirmed)

All 15 trusted strategies verified as LIVE:

- **US-114 confirmed (8):** STR-T, STR-U, STR-V, STR-W, STR-AB, STR-AG, STR-R, STR-AJ
- **Original audit (7):** STR-X, STR-Z, STR-AA, STR-AC, STR-AD, STR-AE, STR-AF

### Post-Change Status Counts

- **LIVE:** 18 (15 trusted + STR-B, STR-I, STR-Q)
- **WATCH:** 4 (STR-L, STR-P, STR-Y, STR-AI)
- **KILLED:** 14 (including newly killed STR-S, STR-AH)

---

## ACTION 2 — capture_signals.py Wiring Verification

**File:** `scripts/paper_trading/capture_signals.py`

### Changes Made

1. **Removed STR-S (Elliott Wave):**
   - Deleted import: `from scanners.scanner_s_elliott_wave import scan as scan_s`
   - Removed from PAPER_STRATEGIES dict: `"STR-S-elliott-wave": scan_s`
   - Removed from `long_only_stocks` set

2. **Removed STR-AH (Island Reversal):**
   - Deleted import: `from scanners.scanner_ah_island_reversal import scan as scan_ah`
   - Removed from PAPER_STRATEGIES dict: `"STR-AH-island": scan_ah`
   - Removed from `long_only_stocks` set

3. **Verified STR-Y and STR-AI remain registered** (WATCH status, not killed):
   - `"STR-Y-adx-dmi": scan_y` — present
   - `"STR-AI-seasonal": scan_ai` — present
   - Both still in `long_only_stocks` set

### PAPER_STRATEGIES Registration (21 entries after changes)

All 15 trusted LIVE strategies + STR-Y (WATCH) + STR-AI (WATCH) + STR-A, STR-B, STR-D, STR-I (pre-existing, not in scope of this change).

### Import Test

```
capture_signals OK
  PAPER_STRATEGIES keys (21): [all verified present]
  MAX_INTERMARKET_POSITIONS: 3
  All assertions PASSED
```

---

## ACTION 3 — STR-AJ Concentration Control

**File:** `scripts/paper_trading/capture_signals.py`

### Problem

STR-AJ (Intermarket Rotation) fires signals across ALL stocks simultaneously when DXY/TNX trigger a risk-on macro condition. This creates portfolio concentration in a single macro bet — if the macro thesis is wrong, all STR-AJ positions fail together.

### Fix Implemented

1. **Constant added** (line 83):
   ```python
   MAX_INTERMARKET_POSITIONS = 3
   ```

2. **Concentration check** added in `_scan_and_capture()` loop, after the `has_open_trade` check and before opening a new trade:
   ```python
   if strategy_id == "STR-AJ-intermarket":
       aj_open_count = len(trade_log.get_open_trades(strategy_id="STR-AJ-intermarket"))
       if aj_open_count >= MAX_INTERMARKET_POSITIONS:
           summary.setdefault("skipped_aj_concentration", 0)
           summary["skipped_aj_concentration"] += 1
           print(f"  SKIP: {strategy_id}/{ticker} — STR-AJ concentration limit "
                 f"({aj_open_count}/{MAX_INTERMARKET_POSITIONS} open)")
           continue
   ```

3. **Comment explaining rationale:**
   ```python
   # STR-AJ fires correlated signals across all stocks on macro triggers — limit concentration
   MAX_INTERMARKET_POSITIONS = 3
   ```

### Behavior

- When STR-AJ fires signals on multiple stocks simultaneously (which is the normal case for a macro trigger), only the first 3 will open paper trades.
- Subsequent STR-AJ signals are skipped with a clear log message and counted in `summary["skipped_aj_concentration"]`.
- This is a lightweight per-strategy cap, not a full risk guard — it does not affect any other strategy.
- Uses `trade_log.get_open_trades(strategy_id=...)` for an accurate count of currently open positions.

---

## Import Test Results

```
strategy_status OK
  STR-S: KILLED
  STR-AH: KILLED
  STR-Y: WATCH
  STR-AI: WATCH
  STR-AJ: LIVE
capture_signals OK
  All assertions PASSED
```

---

## Notes

- The git commit includes 23 files total: the 2 modified source files plus 21 pre-existing uncommitted files (strategy docs, maintenance logs). Per the hard rule that no uncommitted changes are left in the working tree, all were committed together.
- STR-A and STR-D are KILLED in strategy_status.py but remain in PAPER_STRATEGIES (pre-existing, not in scope of this change). Recommend a follow-up to remove them if desired.
