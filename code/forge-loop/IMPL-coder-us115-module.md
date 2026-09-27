# IMPL — US-115: Market Structure Module (Coder Report)

**Author:** Coder agent (T2, glm-5.2)
**Date:** 2026-08-16
**Status:** MODULE + TESTS COMPLETE — scanner modifications deferred to a separate batch
**Design doc:** `04-ForgeLoop/DESIGN-architect-US115-market-structure.md`
**Commit:** `3dfd7ac` — `US-115: Implement market_structure.py module + test suite`

---

## 1. What was built

### 1.1 Module — `scripts/validation/scanners/market_structure.py`

Implements the three primitives + one orchestrator + two shared helpers per the
architect's design:

| Function | Signature (key params) | Returns | Look-ahead cutoff |
|---|---|---|---|
| `_compute_atr` | `(df, period=14)` | `pd.Series` | causal (`close.shift(1)`) |
| `_confirmed_pivots` | `(df, as_of_idx, kind, pivot_distance, lookback)` | `list[int]` | `p + pivot_distance <= as_of_idx` |
| `compute_pullback_entry` | `(df, signal_idx, direction, max_wait_bars, ema_span, fallback)` | `(entry_price, entry_idx)` | levels frozen at `signal_idx` |
| `compute_structure_stop` | `(df, decision_idx, direction, entry_price, max_atr, min_atr, lookback, atr, buffer_atr)` | `float` | `decision_idx` |
| `compute_natural_target` | `(df, decision_idx, direction, entry_price, stop_price, min_rr, lookback, atr, atr_target_mult)` | `float \| None` | `decision_idx` |
| `compute_structure_trade` | `(df, signal_idx, direction, ...)` | `dict \| None` | `decision_idx = entry_idx` |

**Module-level constants** (design §1 / §2.0):
`PIVOT_DISTANCE=5`, `DEFAULT_ATR_PERIOD=14`, `DEFAULT_EMA_SPAN=20`,
`DEFAULT_MAX_WAIT_BARS=5`, `DEFAULT_MAX_ATR=2.0`, `DEFAULT_MIN_ATR=0.5`,
`DEFAULT_BUFFER_ATR=0.5`, `DEFAULT_LOOKBACK_STOP=20`, `DEFAULT_LOOKBACK_TARGET=50`,
`DEFAULT_MIN_RR=1.5`, `DEFAULT_ATR_TARGET_MULT=2.5`.

**Debug-mode assertion guard** (design §4 item 7): when `MARKET_STRUCTURE_DEBUG=1`,
`_assert_confirmed()` asserts every pivot `p` used by any primitive satisfies
`p + pivot_distance <= as_of_idx`, raising a loud `AssertionError` on any look-ahead
regression. Zero cost in production (env flag unset).

### 1.2 Test suite — `scripts/validation/scanners/test_market_structure.py`

All design-doc tests implemented, runnable two ways:
- `python test_market_structure.py` (stdlib `unittest` runner — no pytest required)
- `python -m pytest test_market_structure.py`

The suite forces `MARKET_STRUCTURE_DEBUG=1` at import so the pivot-confirmation
guard runs across every test.

**Test coverage (21 tests, all pass):**

| Group | Tests | What it pins |
|---|---|---|
| T1 | confirmed-pivot guard | US-114 lesson: pivot at p unknown until p+5 |
| T2–T5 | `compute_structure_stop` | normal / cap / no-structure / floor |
| T6–T9 | `compute_natural_target` | meets min_rr / nearest-too-close / ATR fallback / fallback-fails→None |
| T10–T13 | `compute_pullback_entry` | touch / gap-fill / no-touch→signal / no-touch→window_end |
| T14–T15 | `compute_structure_trade` | full happy path (dict+keys) / target None→None |
| L1 | future-bar invariance | appending 50 future bars leaves signal_idx=100 output identical |
| L2 | pivot-confirmation invariance | destroying a peak removes it; pre-confirmation it's filtered |
| L3 | pullback level frozen at signal | a new low confirming *after* signal_idx is NOT used as the support level |
| P1–P3 | property/invariant | all pivots confirmed; stop correct side + risk>0; target None-or-correct-side+R≥1.5 |

---

## 2. Look-ahead safety (the US-114 lesson, centralised)

Every guard from design §4 is implemented:

1. **Single pivot primitive.** All swing detection goes through
   `_confirmed_pivots(as_of_idx, ...)` with the `p + pivot_distance <= as_of_idx`
   filter. Scanners will call `compute_structure_trade`, never `find_peaks` directly.
2. **`decision_idx` discipline.** The orchestrator passes `entry_idx` (the actual
   fill bar, `>= signal_idx`) to stop/target — strictly stricter than signal time.
3. **Support levels frozen at `signal_idx`.** `_confirmed_pivots` is called with
   `as_of_idx=signal_idx` for pullback support selection; a low that confirms during
   the wait window (at `signal_idx+k+PIVOT_DISTANCE > signal_idx`) is excluded. L3
   encodes this as an executable test.
4. **Limit-fill model is causal.** Reading `low[j]/high[j]/open[j]` for
   `j > signal_idx` models a resting limit order (same convention as every
   scanner's `_walk_forward_exit`), not look-ahead.
5. **No future close selects entry/stop/target.** Future bars only test whether a
   resting limit fills and (later, in scanners) test stop/target hits.
6. **ATR & EMA are causal** (`close.shift(1)` Wilder; `ewm(adjust=False)`).

---

## 3. Implementation notes / deviations

- **T2 `max_atr`.** The design's T2 ("entry=100, swing low at 95, ATR=2 → stop=94")
  expects the cap NOT to fire. With default `max_atr=2.0` and ATR=2, the structural
  stop 94 has risk=6 > max_atr×ATR=4, so the cap WOULD clip to 96 — contradicting
  the design's expected 94. The test therefore passes `max_atr=4.0` so the cap stays
  out of the way and the "normal" structural stop (94) is exercised cleanly. This is
  a test-parameter choice, not a module change; production default stays 2.0.
- **T5 `buffer_atr=0`.** To exercise the floor precisely, T5 sets `buffer_atr=0.0`
  so the structural stop equals the swing low (99.5), risk=0.5 < min_atr×ATR=1.0,
  and the floor widens to 99. With the default `buffer_atr=0.5` the buffer would
  push the stop farther (risk 1.5 > 1.0) and the floor would never engage, making
  the test unable to distinguish floor behaviour. Noted here as a deliberate
  test-only parameter.
- **Synthetic-data strategy.** Tests use FLAT OHLC at `base` with clean valleys/peaks
  (only the pivot bar's low/high differs) and a CONSTANT ATR Series passed
  explicitly. This avoids two instabilities that bit the first iteration:
  (a) a swing bar's true range pollutes Wilder ATR and makes stops/targets
  non-exact, and (b) a dip in `close` at the swing bar pulls the EMA below
  `close[signal]`, making the EMA a spurious closer "support" that shadows the
  intended swing-low level. Flat close keeps the EMA flat so the EMA
  dynamic-support branch never fires in the unit tests and the swing-low level is
  the sole support (deterministic). The EMA branch is still exercised by the
  randomised property tests (P1–P3) on noisy series.
- **L3 fill timing.** The new deep low at bar 32 dips *through* the frozen 95
  support, so the resting limit at 95 fills on bar 32 (the first touch) rather
  than bar 33. This is correct limit-order semantics: the SUPPORT LEVEL is frozen
  (fill price stays 95, not 90) even though the fill timing shifts. The test
  asserts `ep_ext==95` (the level is frozen) and documents `ei_ext==32`.
- **`entry_type`.** `"pullback"` when `entry_idx > signal_idx` (the limit filled
  within the window), else `"market"` (the signal-close fallback). A `window_end`
  fallback that fills at `signal_idx + max_wait` is reported as `"pullback"` since
  it represents a late entry, not the signal-bar market entry.

---

## 4. Verification output

```
$ cd ~/HermesForge/scripts/validation/scanners && MARKET_STRUCTURE_DEBUG=1 python test_market_structure.py
... (21 tests) ...
Ran 21 tests in 0.672s
OK

$ python test_market_structure.py   # normal mode, no debug env
Ran 21 tests in 0.742s
OK

$ python -c 'from market_structure import compute_structure_trade; print("import OK")'
import OK
```

---

## 5. Out of scope (separate batch, per task brief)

- **Scanner modifications (11 SWITCH scanners: X, Z, AA, AC, AD, AE, AF, Y, W, R, B).**
  NOT done in this batch — explicitly deferred. The integration pattern
  (design §3.2) is: import `compute_structure_trade`, replace the
  entry/stop/target block, propagate `entry_idx`, make target-R dynamic in
  `_walk_forward_exit`, bump `STRATEGY_VERSION` to `"2.0"`, add a 20-bar
  per-ticker cooldown guard, update docstrings.
- **STR-W reclassification** (KEEP vs SWITCH based on whether its target is
  pattern-derived from pole height) — coder to inspect during the scanner batch.
- **20-bar cooldown** — belongs in each scanner's `scan()` loop, not the module.
  Noted here per the user decision; the module returns price levels only and does
  not enforce cooldown.

---

## 6. Risk notes for the swarm

- The module returns price levels only; it does NOT size positions, execute
  trades, touch exchanges, or choose leverage (SOUL.md hard rules). No
  execution/sizing/API code was added.
- `min_rr=1.5` is the default per the user decision; exposed as a per-call param
  so a scanner can override (e.g. a lower `min_rr` for short-horizon scanners)
  without a global change.
- `fallback="signal"` default per the user decision.
- The module is deterministic given `df` and params (design §5.6).

---

## 7. Next steps (handed back to orchestrator)

1. Separate batch: modify the 11 SWITCH scanners per design §3.2, reclassify W.
2. Per-scanner one-symbol backtest (SPY) + the I1–I4 integration tests (design §7.4).
3. Risk-guardian reviews v1.x→v2.x delta (trade count, win rate, avg R, profit
   factor) per the US-114 protocol before any scanner returns to LIVE.

**End of coder report.**
