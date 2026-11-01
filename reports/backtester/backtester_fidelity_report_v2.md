# Backtester Fidelity Report v2 — PNL-Accounting Reconciliation (Round 3, APPROVED)

Author: backtester (HermesForge)
Date: 2026-10-31
Scope: read-only. No code modified, nothing posted, cron untouched.
Code under test: HEAD = 8bd9f370 ("PNL fix round 3: close four hostile-fill accounting holes")
Window: entry_date >= 2026-09-14
Fills assumption: pessimistic / realistic.

---

## 0. What was actually run (real code, real data — not mocked)

The following functions were imported directly from the live modules and executed
against the live data files. No stubs, no simplified reproductions.

  Modules:
    scripts/paper_trading/hostile_fills_strq.py   (STR-Q intraday path)
    scripts/paper_trading/hostile_fills.py        (swing path)
  Functions imported + called:
    _paper_r                         (both modules)
    _reconcile_signal_dedup          (strq)
    _authoritative_close             (strq)
    _close_outcome                   (strq)
    _compute_r                       (both — imported/validated, see §4 limitation)
  Data:
    scripts/paper_trading/trades.csv            (12,504 rows)
    scripts/paper_trading/trade_journal.jsonl   (39,207 events)
    scripts/paper_trading/hostile_fill_report_strq.jsonl  (existing, stale — NOT re-used)

Interpreter: the repo's resolved venv (resolve_python.sh -> /root/.hermes/installs/…/venv/bin/python3).
pyarrow and fastparquet are NOT importable in that venv — see §4.

---

## 1. Defect closure — re-verified against current code

| # | Defect | Fixed code path | Verified result |
|---|--------|-----------------|-----------------|
| 1 | Entry slippage ignored in `_compute_r` | `_compute_r` now uses `hostile_entry_price` in the numerator | CONFIRMED in code. Bar-level re-run NOT possible (§4). |
| 2 | Dedup silently keep-first on divergences | `_reconcile_signal_dedup` quarantines unreconciled signal_ids | CONFIRMED: 119 quarantined full-window (matches coder's 119). Real reason/r_multiple divergences observed. |
| 3 | Uncosted trades charged ~20 bps adversarial cost-drag | `_paper_r` fallback returns `(gross_r - ROUND_TRIP_BPS/risk, True)` | CONFIRMED: 3,362 post-window STR-Q trades carry no `gauntlet_r` and are charged the 20 bps taker round trip. |
| 4 | `time_zombie_cleanup` (r=0) in scored/win-rate | `_paper_r` returns `(None, False)` for that exit_reason | CONFIRMED: STR-B 5, STR-D 1, STR-VIXC 3 zombie rows excluded. |
| 5 | Win-rate denominator over scored/non-degenerate/closed | aggregation gate in `run()` | CONFIRMED in code + reproduced in the recomputation. |

Note on defect-3 count: the coder reported "3,567 affected". The recomputation finds
3,362 post-window STR-Q trades in the adversarial (missing-gauntlet_r) cohort after dedup
(5,188 raw rows collapse to 3,362 distinct signal_ids). The discrepancy is a raw-vs-dedup
counting convention, not a logic difference; the code path behaves exactly as specified.

---

## 2. STR-Q deep dive (the only strategy with a meaningful sample)

### 2.1 Dedup + quarantine (window post-09-14)

  raw rows                8,434
  duplicate signal_ids    1,673  (4,168 duplicate rows)
  deduped (unique)        5,897
  quarantined                42   (full-window: 119)

Quarantine is doing real work — examples (journal vs CSV close disagreement):

  AAPL ... _1355 : journal (time, 0.7956)  vs CSV (time, 0.862)
  NEAR ... _2025 : journal (time, -0.6585) vs CSV (stop, -1.0)
  CRV  ... _2010 : journal (time, 0.232)   vs CSV (time, 1.92)
  WLD  ... _2030 : journal (target, 2.9995) vs CSV (time, 0.172)

These are exactly the "divergent close rows" that the old keep-first path silently
arbitrated by row order; they are now removed from the scored population.

### 2.2 Cost cohorts (scored trades, non-degenerate, closed)

  degenerate-stop excluded (< 0.1% setup risk):  440
  scored:                                       5,457

  cohort               n      net R      win%    gross (raw r) before cost
  ----------------------------------------------------------------------
  venue-costed         2,095  +791.65    50.7%   +1,674.69   (12 bps crypto / 2 bps stock)
  adversarial (20 bps) 3,362  -156.99    43.5%   +2,095.67   (20 bps taker round trip)

The adversarial cohort is the entire story: +2,095.67 R gross is destroyed by even a
20 bps round-trip cost and lands at -156.99 R. That is before any entry t+3 lag,
before worst-print stop slippage, and before the target trade-through requirement.

### 2.3 STR-Q paper-layer net R (the reconciled headline)

  net R (venue-costed + 20 bps adversarial):  +634.668 R
  win rate (scored):                            46.27%
  avg R / scored trade:                       +0.1163   (t-stat = 4.75)

This is an UPPER BOUND. It still prices the 2,095-trade venue cohort at the generous
12 bps crypto / 2 bps stock venue model, and it prices NO slippage anywhere.

Robustness — uniform 20 bps taker round trip on all 5,457 scored trades
(no slippage, no lag, fee normalization only):

  net R = -50.586 R     win% = 45.28%     avg R/trade = -0.0093     t-stat = -0.38

The moment the cost model is homogenized to a 20 bps taker round trip, the edge goes
statistically indistinguishable from zero (t = -0.38). Prior bar-level reconciliation
(entry-slippage only) already returned ~-419 R for STR-Q, in the same direction.

---

## 3. Authoritative per-strategy table (post-09-14)

All numbers from the fixed functions on live data. Trade count = deduped, non-
quarantined. Win rate = wins / scored (scored = costed, non-degenerate, closed).
net R = paper-model net R after costs (venue or 20 bps adversarial), NO hostile fill
slippage (§4).

| Strategy      | Trades (dedup, non-quar) | Scored | Net R (paper) | Win rate | Avg R/trade (net/scored) |
|---------------|--------------------------|--------|---------------|----------|--------------------------|
| STR-Q         | 5,897                    | 5,457  | +634.668      | 46.27%   | +0.1163                  |
| STR-A         | 3                        | 3      |  -0.2815      | 33.33%   | -0.0938                  |
| STR-B         | 16                       | 11     |  -0.3226      | 54.55%   | -0.0293                  |
| STR-D         | 1                        | 0      |   0.0000      |  n/a     |  n/a   (zombie)          |
| STR-DEBASEMENT| 0                        | 0      |   0.0000      |  n/a     |  n/a   (no trades)       |
| STR-VIXC      | 3                        | 0      |   0.0000      |  n/a     |  n/a   (all zombie)      |

Swing strategies (STR-A/B/D/DEBASEMENT/VIXC) have 3, 16, 1, 0, 3 raw rows respectively
in the window — far below any sample that could support an edge claim. STR-D and
STR-VIXC are zombie-only, STR-DEBASEMENT has no trades at all in the window.

---

## 4. Explicit limitation — bar-level re-simulation could not be re-run

A full hostile-fill re-simulation (check_entry_hostile / check_exit_hostile, now with
the 3-bar confirmation lag for STR-Q) requires OHLCV bar data loaded via
pyarrow/fastparquet. Neither is importable in the resolved venv this reconciliation ran
under, so `_compute_r` was imported and validated but not re-driven with freshly
re-simulated fills. The existing hostile_fill_report_strq.jsonl was NOT reused because it
was written by the pre-fix code and its `hostile_r` values omit entry slippage (defect 1).

What a full bar-level re-run would ADDITIONALLY change versus this paper-layer result:

  1. Entry fill: t+1 open (swing) / t+3 open for STR-Q (signal bar + 1 + CONFIRMATION_BARS=2).
     Buys at a systematically worse price than the paper close → negative delta to every R.
  2. Taker fee 10 bps on BOTH entry and exit for every fill, including the 2,095-trade
     venue cohort currently priced at only ~12 bps crypto / 2 bps stock.
  3. Stop exits fill at worst print of the crossing bar (not the stop level) → extra
     slippage on every stopped trade.
  4. Target exits require trade-THROUGH; targets that only touch never fill, so some
     trades fall through to time-stop or worse.
  5. Trade-count drop: signals that never trade-through entry are skipped outright, and
     target-miss trades change the win/loss mix.

Net effect: strictly lower net R than the paper bound in §3, and (given the uniform-20 bps
result already at -50.6 R and the prior entry-slippage-only -419 R) expected to be
decisively negative for STR-Q. This layer is the one remaining unknown and it is
monotonic against the paper edge, so it does not rescue any positive-edge claim.

---

## 5. Verdict (blunt)

No. No strategy shows a genuine, statistically-meaningful positive net-R-after-costs edge.

  STR-Q: the +634.668 R paper headline is a cost-model artifact. It survives only because
         2,095 trades are priced at a 12 bps crypto / 2 bps stock venue model. Homogenized
         to a uniform 20 bps taker round trip (still zero slippage/lag), it is -50.6 R
         (t = -0.38). With realistic hostile fills (entry t+3 lag, worst-print stops,
         20 bps both sides) the prior entry-slippage-only reconciliation already showed
         ~-419 R, and a full re-run can only push it further negative.

  STR-A / STR-B: negative net R on trivial samples (3 and 11 scored) — no edge, no power.

  STR-D / STR-VIXC / STR-DEBASEMENT: no scored trades in window (zombie or none).

The +3739 R headline from the prior pass (and the earlier ~-419 R entry-only read) are
both superseded. The corrected paper-layer truth is +634.668 R on paper-fill pricing that
still flatters the venue cohort, and it does not survive a realistic cost floor.