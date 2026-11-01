# Architect Spec — Round 4: PNL-Accounting Consolidation + Dynamic Fees (US-164/165/166/167)

Date: 2026-10-31
Author: Architect (HermesForge)
Status: DESIGN ONLY — no pipeline code, posts, or cron touched. Awaiting principal sign-off.
Scope: ONE coherent design for US-164 (consolidation), US-165 (dynamic fees),
US-166 (taker-fee direction), US-167 (self-guard). Consolidation is designed FIRST;
the other three fixes land INSIDE the consolidated module as sequential commits.

## 0. Ground truth read (verified, do not re-derive)

Source files read in full:
- scripts/paper_trading/hostile_fills.py          (swing, daily)
- scripts/paper_trading/hostile_fills_strq.py     (STR-Q v1, 5m, market entry)
- scripts/paper_trading/hostile_fills_strq_v2.py  (STR-Q v2, 5m, limit entry)
- scripts/gauntlet/cost_adjuster.py               (G3 static venue costs)
- scripts/gauntlet/execution_sim.py               (TAKER_FEE_BPS = 4.5 per leg)
- scripts/gauntlet/g0_cost_screen.py              (TAKER_FEE_BPS = 9.0 round-trip)
- scripts/gauntlet/g6_regime_robustness.py        (calls cost_adjuster.batch_adjust)
- scripts/gauntlet/tests/test_g6.py               (asserts batch_adjust adds gauntlet_r)
- scripts/data/detect_liquidity_sweeps.py         (CONFIRMATION_BARS = 2)
- cache/architect_pnl_fix_spec.md                 (round-3 decision record)

The three hostile files share byte-identical accounting bodies but were forked
separately. The variant deltas are EXACTLY: entry-fill semantics (bar-open vs
signal-price limit), ENTRY_MODE, REPORT_PATH, and the dedup key field
(trade_id for swing, signal_id for strq/v2).

Live Hyperliquid fee schedule CONFIRMED 2026-10-31 via
`POST https://api.hyperliquid.xyz/info {"type":"userFees","user":"0x0000...0000"}`:
- feeSchedule.cross = "0.00045"  -> 4.5 bps perp taker  (CONFIRMS PROP-001 0.045%)
- feeSchedule.add   = "0.00015"  -> 1.5 bps perp maker  (CONFIRMS PROP-001 0.015%)
- feeSchedule.spotCross = "0.0007" (7 bps), spotAdd = "0.0004" (4 bps)
- tiers.vip: array ascending by ntlCutoff (5M/25M/100M/500M/2B/7B HYPE staked)
- ANOMALY (flagged, do not adopt): the zero-address `userCrossRate` came back
  "0.0004" (4.0 bps) — MORE favorable than the schedule base. We read
  `feeSchedule.cross/.add` (the schedule's declared base tier), NEVER
  `userCrossRate/.addRate`, precisely so a per-account discount is not silently
  adopted. Base-taker = 4.5 bps is the highest (most expensive) tier and is the
  correct fail-closed reference.

---

## 1. US-164 — CONSOLIDATION (foundation, behavior-preserving)

New module: scripts/paper_trading/pnl_accounting.py

### 1.1 Functions that MOVE into the module (single source of truth)

| Function                  | Present in            | Notes |
|---------------------------|-----------------------|-------|
| _apply_taker_fee          | swing, strq, v2       | US-166 threads direction (final sig below) |
| _compute_r                | swing, strq, v2       | byte-identical after round-3 unification |
| _adversarial_cost_drag    | swing, strq, v2       | US-167 adds self-guard; US-165 takes dynamic bps |
| _paper_r                  | swing, strq, v2       | byte-identical |
| _authoritative_close      | strq, v2              | strq-pair only |
| _close_outcome            | strq, v2              | strq-pair only |
| _reconcile_signal_dedup   | strq, v2              | strq-pair only |

Also move (byte-identical, pure, zero variant coupling — reduces the largest
contiguous drift block; recommended, not strictly mandatory):
- _worst_print(bar, direction)
- _trades_through(bar, level, side)
- _bar_touches(bar, level)

### 1.2 What STAYS per-variant (parameterized, NOT forked)

These embody variant-specific behavior and are NOT moved:

- check_entry_hostile — differs 3 ways:
    * swing: scan from signal_bar_idx+1, fill at row["open"]
    * strq v1: scan from signal_bar_idx+1+CONFIRMATION_BARS, fill at row["open"]
    * strq v2: same scan floor as v1, fill at ENTRY_MODE="limit" = signal price
- check_exit_hostile — signature differs:
    * swing: (trade, bars) — iterates bars, MAX_BARS_HELD is a per-strategy dict
    * strq/v2: (trade, bars, entry_bar_idx) — MAX_BARS_HELD scalar 15
- _append_report / _read_existing_keys — report I/O, dedup key field differs
    * swing: key = f"{trade_id}|{stage}", re-reads file per call
    * strq/v2: key = f"{signal_id}|{stage}", preloaded set + add-after-write
- run() and main() — orchestration and summary, differ by variant.

Per-variant CONFIG (moved to module-level constants or module __init__ params,
never re-inlined):
- REPORT_PATH         (swing / strq / v2 .jsonl)
- ENTRY_MODE          ("market" default; "limit" for v2)
- MAX_BARS_HELD       (swing dict; scalar 15 for strq/v2)
- DEDUP_KEY_FIELD     ("trade_id" | "signal_id")
- STRATEGY_ID         ("STR-Q-liquidity-sweep", strq/v2)
- CONFIRMATION_BARS   (import from detect_liquidity_sweeps, already shared)

### 1.3 Final function-by-function signatures (post all four stories)

```python
# scripts/paper_trading/pnl_accounting.py
import math, json

DEGENERATE_RISK_FLOOR = 0.001     # 0.10% — see §5 reconciliation. SINGLE source.
DEFAULT_ROUND_TRIP_BPS = 20.0     # US-164 behavior-preserving placeholder only;
                                  # US-165 call sites pass dynamic fee_source value.

def _apply_taker_fee(price: float, direction: str, is_entry: bool,
                     taker_bps: float) -> float:
    """Adverse per-leg taker fee. buy leg: price*(1+fee) (costs more to buy);
    sell leg: price*(1-fee) (nets less to sell). US-166 fix.
    side = 'buy' iff (direction=='long') == is_entry  (entry<>exit flips the side).
    """

def _compute_r(paper_entry: float, paper_stop: float, direction: str,
               hostile_entry_price: float, exit_price: float) -> float:
    """R = direction_pnl(hostile_entry, hostile_exit) / setup_risk(paper).
    denominator = abs(paper_entry - paper_stop), never the slipped entry."""

def _adversarial_cost_drag(entry_price: float, stop_price: float,
                           round_trip_bps: float | None = None) -> float:
    """US-167 self-guard first: entry_price<=0 or stop_price<=0 -> +inf sentinel.
    risk_pct = abs(entry-stop)/entry; if risk_pct < DEGENERATE_RISK_FLOOR -> +inf.
    else (bps/10000)/risk_pct.  round_trip_bps None -> DEFAULT_ROUND_TRIP_BPS."""

def _paper_r(trade: dict, round_trip_bps: float | None = None) -> tuple:
    """Returns (value: float|None, costed: bool). Preserves round-3 semantics:
    time_zombie_cleanup -> (None, False); gauntlet_r finite -> (v, True);
    else raw r_multiple minus adversarial drag, rejecting entry<=0/stop<=0 up front.
    round_trip_bps None -> DEFAULT_ROUND_TRIP_BPS."""

def _authoritative_close() -> dict: ...       # {signal_id: (exit_reason, r_multiple)}
def _close_outcome(row: dict) -> tuple: ...   # (exit_reason, round(r_multiple,3))
def _reconcile_signal_dedup(strq_trades: list) -> tuple: ...
    # -> (deduped_list, quarantined_count, quarantine_lines)
    # Keep exact-match (reason AND r_multiple 3dp) + quarantine semantics UNCHANGED.

def _worst_print(bar, direction) -> float: ...
def _trades_through(bar, level, side) -> bool: ...
def _bar_touches(bar, level) -> bool: ...
```

Import surface (per dependent file):

```python
# hostile_fills.py (swing)
from pnl_accounting import (_apply_taker_fee, _compute_r, _adversarial_cost_drag,
                            _paper_r, _worst_print, _trades_through, _bar_touches,
                            DEGENERATE_RISK_FLOOR)

# hostile_fills_strq.py / hostile_fills_strq_v2.py
from pnl_accounting import (_apply_taker_fee, _compute_r, _adversarial_cost_drag,
                            _paper_r, _worst_print, _trades_through, _bar_touches,
                            _authoritative_close, _close_outcome,
                            _reconcile_signal_dedup, DEGENERATE_RISK_FLOOR)
```

### 1.4 Behavior-preservation approach (construction, not assertion)

US-164 is a pure refactor. Parity is guaranteed by construction because:
1. Function bodies move verbatim (identical math, identical rounding to 6dp).
2. Constants resolved at call sites to the SAME values they have today:
   - strq/v2 call `_adversarial_cost_drag(entry, stop)` and `_paper_r(trade)` with
     no bps arg -> DEFAULT_ROUND_TRIP_BPS = 20 (their current ROUND_TRIP_BPS).
   - swing also resolves to 20 (currently ROUND_TRIP_BPS = 2*10 = 20).
   - `_apply_taker_fee` call sites pass taker_bps=10 (current TAKER_FEE_BPS).
   - DEGENERATE_RISK_FLOOR = 0.001 replaces the strq/v2 local MIN_RISK_PCT=0.001
     AND replaces swing's `from cost_adjuster import MIN_RISK_PCT` (0.005).
     This is the ONLY numeric change in US-164, and it is the deliberate
     reconciliation in §5 (swing's adversarial floor moves 0.5% -> 0.1%).
     Flag for principal: this tightens one swing edge case, see §5.
3. Dedup-key field, ENTRY_MODE, REPORT_PATH, MAX_BARS_HELD, CONFIRMATION_BARS
   remain per-variant and unchanged.

Acceptance parity targets (re-verify after refactor, must be IDENTICAL except
the flagged swing-floor reconciliation):
- 119 quarantined by _reconcile_signal_dedup.
- time_zombie_cleanup excluded as (None, False).
- win-rate computed over scored / closed / non-degenerate only.
- ~20 bps adversarial penalty on uncosted (until US-165 lands).

`py_compile` clean on all three files + new module. Path-scoped commit.

---

## 2. US-165 — DYNAMIC FEES (single source consumed by both paths)

New module: scripts/gauntlet/fee_source.py

### 2.1 Endpoint + parse (exact)

```
POST https://api.hyperliquid.xyz/info
Content-Type: application/json
Body: {"type": "userFees", "user": BASE_ADDRESS}
BASE_ADDRESS = "0x0000000000000000000000000000000000000000"
```

Response JSON (see §0 ground truth). Parse ONLY the schedule base tier:

```python
def _parse_base_fees(data: dict) -> dict | None:
    fs = data.get("feeSchedule")
    if not isinstance(fs, dict):
        return None
    try:
        taker = float(fs["cross"]) * 10000    # 0.00045 -> 4.5
        maker = float(fs["add"])   * 10000    # 0.00015 -> 1.5
    except (KeyError, TypeError, ValueError):
        return None
    if not (maker >= 0 and taker > 0 and math.isfinite(taker) and math.isfinite(maker)):
        return None
    return {"taker_bps": taker, "maker_bps": maker}
```

Deliberately ignore `userCrossRate`/`userAddRate` (the queried account's
personal, possibly discounted rate) — reading them would let a favorable tier
leak into the base assumption. The schedule's top-level `cross`/`add` IS the
base tier and the most expensive tier, so it is the correct fail-closed anchor.

### 2.2 "Base tier" mapping (confirmed, not assumed)

- perp taker (cross) = 4.5 bps   (CONFIRMED unchanged from PROP-001 0.045%)
- perp maker (add)  = 1.5 bps   (CONFIRMED unchanged 0.015%)

### 2.3 Runtime fetch + cache/TTL

```python
HYPERLIQUID_INFO_URL = "https://api.hyperliquid.xyz/info"
BASE_ADDRESS = "0x0000000000000000000000000000000000000000"
FEE_CACHE_TTL_SECONDS = 6 * 3600        # 6 hours — schedule changes are rare

_cache_state = {"ts": 0.0, "fees": None}

def fetch_hyperliquid_base_fees(timeout: float = 10.0) -> dict | None:
    # urllib.request POST json; on ANY exception/HTTP!=200/non-json -> None (not raise)

def get_venue_costs() -> dict:
    """Returns {'crypto': {...}, 'stock': {...}}. Cached for TTL; on fetch
    failure returns FAIL_CLOSED_FALLBACK. Never caches the fallback as live."""
```

### 2.4 FAIL-CLOSED fallback (conservative; NEVER a more favorable value)

FALLBACK is a static module constant equal to the base-tier schedule values —
i.e. the MOST EXPENSIVE tier. It is the same cost as today's assumption, so a
fetch failure cannot silently make fees look cheaper:

```python
FAIL_CLOSED_FALLBACK = {
    "crypto": {"taker_bps": 4.5, "maker_bps": 1.5,
               "slippage_bps": 2.5, "funding_bps": 0.5},   # all-in round-trip = 12.0 bps
    "stock":  {"taker_bps": 1.0, "maker_bps": 0.0,
               "slippage_bps": 1.0, "funding_bps": 0.0},   # all-in round-trip = 3.0 bps
}
```

Rule: live taker can only be <= fallback (same tier). If the live schedule ever
made crypto taker CHEAPER than 4.5 (it will not — 4.5 is base), the fallback
still resolves to 4.5. Fail-closed is enforced by construction: fallback == base
tier, never a discounted tier.

### 2.5 Realistic non-zero-commission STOCK cost (stated broker assumption)

Broker assumption: Interactive Brokers Pro, tiered pricing, typical $30–$80
mid/large-cap names at >= $20k notional.
- taker commission per side = 1.0 bps  (approx $1 minimum / $0.005-per-share
  amortized over realistic notional; NOT zero-commission)
- slippage/spread         = 1.0 bps
- funding                 = 0.0
- all-in round-trip       = 1.0*2 + 1.0 = 3.0 bps   (up from the flat 2.0 that was
  "zero commission + spread")

This replaces stock=2.0 with stock=3.0. Deliberate behavior change (venue
correctness), flagged for principal.

### 2.6 Exposed API

```python
def get_venue_costs() -> dict                          # cached, fail-closed
def get_taker_bps(asset_class: str) -> float           # per-side taker
def get_maker_bps(asset_class: str) -> float
def get_round_trip_bps(asset_class: str) -> float      # taker*2 + slippage + funding
```

### 2.7 BOTH consumers use the SAME source (no parallel copy)

- cost_adjuster.compute_cost_drag: replace
  `venue_cost_bps = VENUE_COSTS.get(asset_class or "", DEFAULT_COST)`
  with `venue_cost_bps = fee_source.get_round_trip_bps(asset_class or "")`.
  Delete VENUE_COSTS and DEFAULT_COST (or keep as deprecated alias = fallback).
- pnl_accounting._adversarial_cost_drag / _paper_r: the per-variant call sites
  resolve `fee_source.get_round_trip_bps(asset_class)` and pass the value in.
  `_apply_taker_fee` call sites (inside check_entry_hostile/check_exit_hostile,
  which stay per-variant) resolve `fee_source.get_taker_bps(asset_class)`.

Result: exactly ONE fee table exists (fee_source). gauntlet G3 (compute_cost_drag)
and the hostile/live PnL path (adversarial cost_drag, taker fee) both derive from
it. cost_adjuster no longer owns fee magnitudes.

Behavior delta (deliberate, principal sanity-check):
- crypto uncosted adversarial penalty: 20 bps proxy -> 12.0 bps (9 taker + 2.5 slip
  + 0.5 funding), the real venue all-in.
- stock all-in: 2.0 -> 3.0 bps (non-zero commission).
- per-fill taker: 10 bps flat -> 4.5 bps crypto / 1.0 bps stock.

Unit tests required for the fail-closed path: mock the fetch to raise/timeout and
assert get_venue_costs() == FAIL_CLOSED_FALLBACK; assert a "cheaper" live schedule
does NOT drop below fallback on subsequent logic; assert TTL caching (second call
within TTL does not hit network).

---

## 3. US-166 — TAKER-FEE DIRECTION (threads direction/side)

Current bug: `_apply_taker_fee(price, is_entry)` returns `price * (1 + fee_rate)`
unconditionally. `*(1+fee)` is correct ONLY for a BUY leg (long entry, short
exit-cover). For the SELL leg (long exit, short entry) it moves the price the
WRONG (favorable) way. Net effect: no round trip ever pays the second, adverse
half of the fee, so longs and shorts are both overstated by the missing per-leg
fee.

Fix (inside pnl_accounting._apply_taker_fee, final signature from §1.3):

```
side = "buy" if (direction == "long") == is_entry else "sell"
if side == "buy":  return round(price * (1 + taker_bps/10000), 6)
else:              return round(price * (1 - taker_bps/10000), 6)
```

Semantics table (direction, is_entry -> side -> fee direction):
- long,  entry=True  -> buy  -> price*(1+fee)  (pay more to buy)      [correct, was correct]
- long,  entry=False -> sell -> price*(1-fee)  (net less on exit)     [was WRONG: +(fee)]
- short, entry=True  -> sell -> price*(1-fee)  (net less on short)    [was WRONG: +(fee)]
- short, entry=False -> buy  -> price*(1+fee)  (pay more to cover)    [correct, was correct]

Call-site changes (in the per-variant check_entry_hostile / check_exit_hostile):
pass `direction=trade["direction"]` (or the already-computed local) and
`taker_bps=fee_source.get_taker_bps(asset_class)`. `is_entry` stays as the
entry/exit discriminator. Both a long round trip and a short round trip now
charge exactly 2 x taker_bps.

Acceptance: unit test asserts a long round trip and a short round trip both
reduce gross R by the SAME total (2 * taker_bps), and that the old direction-blind
path is gone (no `*(1+fee)` on a sell leg).

---

## 4. US-167 — SELF-GUARD in _adversarial_cost_drag

Add, as the FIRST lines of _adversarial_cost_drag (before any division):

```python
if entry_price <= 0 or stop_price <= 0:
    return float("inf")
```

Sentinel is `float("inf")` (consistent with the existing degenerate-stop return
and the callers' `math.isfinite(...)` guards in _paper_r). This removes the
latent ZeroDivisionError / negative-risk foot-gun at the source rather than
relying on every future call site to guard first. No behavior change to existing
call sites (they already pre-reject non-positive prices in _paper_r; this makes
the function self-defending).

Acceptance: `_adversarial_cost_drag(0, x)` and `_adversarial_cost_drag(-1, x)`
and `_adversarial_cost_drag(x, 0)` return +inf with no exception; unit-test the
zero/negative paths.

---

## 5. RECONCILIATION — MIN_RISK_PCT two-definitions hazard (explicit)

Confirmed inconsistency:
- cost_adjuster.py:30  MIN_RISK_PCT = 0.005  (0.5%)
- hostile_fills_strq.py:56 / v2:56  MIN_RISK_PCT = 0.001  (0.10%)
- hostile_fills.py (swing) `from cost_adjuster import MIN_RISK_PCT` -> 0.005

So even WITHIN the adversarial path today, swing uses 0.5% while strq uses 0.1% —
the swing value is wrong only by accident of importing cost_adjuster's constant
by name.

DECISION — the consolidated module uses:

    DEGENERATE_RISK_FLOOR = 0.001   (0.10%)

WHY 0.10% (not 0.5%):
1. The 0.5% floor would wrongly exclude STR-Q fills whose documented stops sit
   ~0.35% (round-3 Defect-5 finding; prior spec already DECIDED 0.10% for the
   PNL outlier floor). 0.5% would quarantine the bulk of legitimate STR-Q trades.
2. The floor's purpose is to catch DEGENERATE near-zero-risk artifacts (PAXG
   ~0.09% stop, ARB sub-cent stop -> ±43R/-105R blowups), not legitimate tight
   stops. 0.10% kills the artifacts and keeps ~0.35% stops.
3. A single floor must hold for BOTH swing and strq. The current 0.5%/0.1% split
   is itself drift; consolidation must pick one, and 0.10% is the defensible one.

Behavior consequence (flag to principal): swing's adversarial floor narrows from
0.5% -> 0.10%, meaning a handful of swing trades with 0.10%..0.5% risk that were
previously "unscoreable" (inf -> dropped from aggregates) may now be scored.
This is the CORRECT direction (they're legitimate, not degenerate), but it is a
numeric change and must be in the commit message / changelog.

Residual hazard (surface, do NOT silently fold): cost_adjuster.MIN_RISK_PCT=0.005
still serves the gauntlet G3 venue cost path (compute_cost_drag returns inf below
0.5%). It is a DIFFERENT constant with the SAME name and a DIFFERENT value. This
design does NOT change cost_adjuster's 0.005 (G3 scope creep), but:
- the consolidated module renames its constant to DEGENERATE_RISK_FLOOR and does
  NOT import from cost_adjuster (this kills the name collision at the source);
- a follow-up US is recommended to unify cost_adjuster's floor with
  DEGENERATE_RISK_FLOOR=0.001, documenting that this would bring ~0.35%-stop
  STR-Q trades INTO the gauntlet cost model (currently they return inf and are
  effectively uncosted there). That is a separate G3 decision.

### Other constants with the SAME two-definitions hazard (surface all)

1. TAKER_FEE_BPS — FOUR definitions, THREE meanings:
   - hostile_fills.py:40 / strq:44 / v2:44  = 10  ("0.1% proxy taker")
   - execution_sim.py:24  = 4.5   (real per-leg taker)
   - g0_cost_screen.py:22 = 9.0   (ROUND-TRIP taker, "0.045% * 2")
   Consolidation + dynamic fees eliminate this: per-leg taker becomes
   fee_source.get_taker_bps() (4.5 crypto / 1.0 stock); no module re-declares a
   numeric TAKER_FEE_BPS. execution_sim.py and g0_cost_screen.py should later
   import fee_source too (separate, low-risk follow-up), but this design does not
   touch them.

2. ROUND_TRIP_BPS — three definitions, all 20 (2*10). Collapsed to
   DEFAULT_ROUND_TRIP_BPS in pnl_accounting (US-164 placeholder), replaced by
   fee_source.get_round_trip_bps() in US-165.

3. MAX_BARS_HELD — same NAME, different TYPE/meaning:
   - swing: dict {strategy_id -> bars} (per-strategy daily time-stop)
   - strq/v2: scalar 15 (single intraday 75-min time-stop)
   Consolidation keeps BOTH as per-variant config (they are genuinely different
   semantics, not a drift); do NOT unify. Document as intentionally distinct.

4. VENUE_COSTS crypto=12.0 (9 fee + 2.5 slip + 0.5 funding) vs adversarial
   ROUND_TRIP_BPS=20 — two different "crypto cost" numbers feeding two paths.
   US-165 collapses both to fee_source.get_round_trip_bps() = 12.0 crypto.

---

## 6. MODULE LAYOUT (final repository shape)

```
scripts/
  paper_trading/
    pnl_accounting.py            # NEW — shared accounting (US-164 + 166 + 167)
    hostile_fills.py             # swing: imports pnl_accounting (thin orchestration)
    hostile_fills_strq.py        # STR-Q v1: imports pnl_accounting
    hostile_fills_strq_v2.py     # STR-Q v2: imports pnl_accounting
  gauntlet/
    fee_source.py                # NEW — dynamic fee source (US-165), single owner
    cost_adjuster.py             # imports fee_source; drops VENUE_COSTS/DEFAULT_COST
                                 #   ownership; keeps its own MIN_RISK_PCT=0.005 (G3)
  data/
    detect_liquidity_sweeps.py   # unchanged (CONFIRMATION_BARS=2 already shared)
```

Import direction is one-way and acyclic:
  hostile_fills*.py -> pnl_accounting.py -> fee_source.py
                     cost_adjuster.py -> fee_source.py

No module imports back into a hostile file. fee_source has zero coupling to
trade_log / trade_journal / detect_liquidity_sweeps (pure HTTP + cache + math),
so it stays unit-testable without the pipeline.

---

## 7. EXACT IMPLEMENTATION ORDER (one story per commit, each green on its own)

Commit 1 — US-164 consolidation (behavior-preserving refactor):
  1. Create pnl_accounting.py with the §1.1 functions verbatim (bodies copied,
     no logic edits) + DEGENERATE_RISK_FLOOR=0.001 + DEFAULT_ROUND_TRIP_BPS=20.
  2. Rewire the three hostile files to import from it; delete local definitions.
  3. Swing: replace `from cost_adjuster import MIN_RISK_PCT` with
     DEGENERATE_RISK_FLOOR import (the §5 reconciliation).
  4. py_compile clean; run hostile_fills.py --dry-run, strq --dry-run, strq_v2
     --dry-run and diff output against a pre-refactor capture. Parity targets
     from §1.4 must hold (119 quarantine, zombie exclusion, 20 bps penalty).
  5. Path-scoped commit.

Commit 2 — US-167 self-guard (pure additive, zero behavior change):
  1. Add the §4 guard as the first lines of _adversarial_cost_drag.
  2. Unit test zero/negative entry+stop paths. Commit.

Commit 3 — US-166 taker-fee direction (self-contained correctness fix):
  1. Change _apply_taker_fee to the side-aware body in §3.
  2. Update the four call sites in check_entry_hostile / check_exit_hostile to
     pass direction (taker_bps still 10 at this commit to keep magnitude stable).
  3. Unit test: long round trip and short round trip pay identical 2*taker fee;
     old favorable-sell path is gone. Commit.

Commit 4 — US-165 dynamic fees (largest surface; new module + two consumers):
  1. Create fee_source.py (§2) with fetch/parse/cache/TTL/FAIL_CLOSED_FALLBACK.
  2. Rewire cost_adjuster.compute_cost_drag + adjust_trade to
     fee_source.get_round_trip_bps(); drop VENUE_COSTS/DEFAULT_COST ownership.
  3. Rewire pnl_accounting call sites: _adversarial_cost_drag/_paper_r take
     fee_source.get_round_trip_bps(asset_class); _apply_taker_fee takes
     fee_source.get_taker_bps(asset_class).
  4. Unit-test fail-closed path + TTL caching + parity of the fallback numbers.
  5. Commit (with the §2.7 behavior-delta noted in the changelog).

Do NOT reorder. Each commit compiles and passes its tests independently.

---

## 8. Explicit non-goals / cautions

- No edits to detect_liquidity_sweeps.py (CONFIRMATION_BARS import only, already
  shared). No change to detector entry-price assignment (round-3 scope decision
  preserved).
- execution_sim.py TAKER_FEE_BPS=4.5 and g0_cost_screen.py TAKER_FEE_BPS=9.0 are
  NOT touched by this design (flagged as follow-up consumers of fee_source).
- cost_adjuster.MIN_RISK_PCT=0.005 left at 0.005 (G3 scope); only renamed out of
  the consolidated module to kill the name collision.
- Prior campaign note "Do NOT edit hostile_fills*.py" (2026-09-aegis-rebuild/
  lu-02) is SUPERSEDED by the principal's active US-164 directive; the three files
  are edited in this round but ONLY to import the shared module (no logic rewrite).
- None of this touches trades.csv/journal; hostile reports remain append-only JSONL
  with the same dedup keys.

END OF DESIGN.