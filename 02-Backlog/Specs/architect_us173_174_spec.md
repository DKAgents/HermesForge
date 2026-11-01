# Architect Spec — US-173 (Look-Ahead Close-Entry Fix) + US-174 (Mandatory G3 Fill-Realism Gate)

Date: 2026-11-01
Author: Architect (HermesForge)
Status: DESIGN ONLY — no pipeline code, posts, tags, cron, or .env modified.
Scope: ONE coherent design for two stories, sequenced intentionally. US-173 fixes the
discovery-backtest fill convention; US-174 builds the enforcement gate that consumes the
corrected (realistic) fill model. US-174 depends on US-173's fill semantics — land US-173
first, keep each story green on its own.

READ-FIRST (verified in full, do not re-derive):
- 02-Backlog/Stories/US-173-Lookahead-Fill-Fix.md
- 02-Backlog/Stories/US-174-Mandatory-G3-Gate.md
- cache/backtester_reevaluation_report.md
- scripts/validation/run_phase1a.py, run_phase1a_v2_us114.py, run_phase1a_v3_us115.py
- scripts/validation/walk_forward.py, walk_forward_us114.py
- scripts/validation/scanners/market_structure.py  (compute_pullback_entry -> _entry_fallback)
- scripts/validation/scanners/scanner_t_head_shoulders.py, scanner_u_double_top_bottom.py,
  scanner_ag_wedge.py, scanner_v_triangles.py, scanner_w_flags_pennants.py,
  scanner_s_elliott_wave.py  (direct `entry = close[...]` sites)
- scripts/gauntlet/execution_sim.py, fee_source.py, cost_adjuster.py
- scripts/paper_trading/pnl_accounting.py, hostile_fills.py  (the existing t+1-open hostile model)
- scripts/validate_strategy.py  (the strategy-notes gate; sys.exit(1) on fail)
- scripts/research/regime_strategy_selector.py  (STRATEGY_REGISTRY status = LIVE/WATCH/KILLED)
- 03-ADRs/ADR-004-Phase1-Validation-Framework.md  (the validation framework the gate amends)
- trading/proposals/PROP-001-hermes-strategy-gauntlet.md  (G3 wording)

---

## 0. Ground truth — where the look-ahead fill actually lives

The re-evaluation report calls this "bug #4: entry = close[signal bar]". The fill
convention is NOT set in run_phase1a.py or walk_forward.py — it is set UPSTREAM, in two
places, and the discovery runners just consume whatever `entry_price` the scanner emitted:

(A) market_structure.py `_entry_fallback()` (the 11 structure-based scanners X/Z/AA/AC/AD/
    AE/AF/Y/W/R/B all route through it). Its DEFAULT fallback branch returns the signal-bar
    close retroactively:

        market_structure.py:180-182
        if fallback == "window_end":
            j = min(signal_idx + max_wait_bars, n - 1)
            return float(df["close"].iloc[j]), j
        # default "signal": retroactive market entry at signal-bar close.
        return float(df["close"].iloc[signal_idx]), signal_idx

    This is the look-ahead: the signal is only *known* at close[signal_idx], yet the entry
    is priced (and the exit simulation begins) at that very close. The pullback/limit path
    of compute_pullback_entry is already realistic (resting limit filled at a LATER bar);
    only this fallback is wrong.

(B) Direct `entry = close[...]` in the chart-pattern scanners (the US-114 promotion block).
    CONFIRMED sites (grep `entry = close[...]` / `entry = c`):

        scanner_t_head_shoulders.py:123,165    entry = close[j]      (neckline break)
        scanner_u_double_top_bottom.py:108,141  entry = close[j]      (pattern trigger)
        scanner_ag_wedge.py:131,142            entry = c             (c = close at breakout)
        scanner_v_triangles.py:139,156         entry = c
        scanner_w_flags_pennants.py:168,178    entry = c
        scanner_s_elliott_wave.py:140,195      entry = df["close"].values[j]

    AUDIT-LIST (coder MUST grep these two before closing US-173; same transform applies):
        scanner_ab_obv_divergence.py, scanner_aj_intermarket.py,
        scanner_vix_vrp_contango.py, scanner_sector_momentum_pullback.py
        (the last two carry `entry = close[i]` only in doc-strings/comments — confirm the
        live code path, fix the live path and the comment).

DISCREPANCY TO FLAG (do not silently resolve): scanner_w_flags_pennants.py is listed in
DESIGN-architect-US115-market-structure.md as one of the "SWITCH (11)" to
compute_structure_trade, YET still contains live `entry = c` at lines 168/178. Either W was
partially migrated (a residual branch survived) or the migration claim is stale. The coder
must determine whether W's `entry = c` path is reachable and, if so, apply the §1.3 fix; if
unreachable, delete it and record the finding. This is an investigation step, not a
silent assumption.

---

## 1. US-173 — Look-ahead close-entry fix

### 1.1 The correct realistic fill convention (DECIDED)

For a DAILY-bar swing/pattern signal the signal is knowable only at close[signal_idx].
A real fill must therefore occur on a LATER bar. DECIDED convention (identical to the one
hostile_fills.py already implements for paper — "Signal on bar t → fills NO EARLIER than
bar t+1 open"):

    market entry (no resting limit captured) fills at open[signal_idx + 1].

Two sub-decisions resolved explicitly:

  1. Next-OPEN, not next-CLOSE. Next-close would still let a full bar of information leak
     into the fill price (you decide at t close, and next-close is knowable only at t+1
     close — same class of look-ahead). Next-open is the earliest genuinely actionable
     print and matches the existing hostile_fills.py convention. DECISION: next-open.

  2. Intrabar vs daily. execution_sim.py (L2 book, queue position, cross+tick) governs
     INTRADAY CRYPTO (5m/1h/6h) — that path already models realism at sub-bar granularity
     and is OUT OF SCOPE for US-173 (it has no close-entry bug; it replays real L2). The
     close-entry bug is specific to the DAILY-bar discovery backtests and the bar-level
     scanners. US-173 fixes the daily-bar path; US-174 dispatches by timeframe to pick the
     right fill model. See §2.1. This ambiguity is RESOLVED here: next-open applies to
     daily-bar (and 1h/4h swing bar) fills; 5m crypto uses execution_sim, never next-open.

### 1.2 The adverse-selection cost it introduces

For a breakout/continuation signal, close[signal_idx] is a strong-direction close. The next
open is systematically adverse (gaps up on a long breakout, down on a short). The report
bounds the drag at ~0.1–0.4% on daily bars ≈ 0.05–0.3 R on a 1–3% stop, plus the fee round
trip (stock 3 bps / crypto 12 bps via fee_source) which is 0.01–0.12 R. Net realized drag on
the pattern strategies is ~0.1–0.3 R/trade, front-loaded on entry. This is NOT a parameter
to tune — it is the honest consequence of a realistic fill; US-173 must charge it, and
US-174 must reject edges it erases.

### 1.3 Function-by-function changes (the coder's exact edits)

#### 1.3.1 market_structure.py — fix the fallback (covers the 11 structure scanners)

Change `_entry_fallback()` to fill at next-open and split the "fill bar index" from the
"decision bar index" so downstream exit simulation stays self-consistent.

CURRENT signature:
    def _entry_fallback(df, signal_idx, max_wait_bars, fallback) -> tuple[float, int]

NEW behavior (both branches fill at the NEXT bar's open, never the signal close):
    - fallback == "next_open"  (NEW name, replaces "signal" as default):
        j = signal_idx + 1
        if j >= len(df): return float(df["close"].iloc[signal_idx]), signal_idx  # last-bar guard
        return float(df["open"].iloc[j]), j
    - fallback == "window_end":
        j = min(signal_idx + max_wait_bars + 1, len(df) - 1)   # note the +1 now
        return float(df["open"].iloc[j]), j

The RETURNED index is now always the FILL bar index (>= signal_idx + 1). This makes the
exit walk ("start at fill bar + 1") uniform across pullback and market entries.

Change the default in `compute_pullback_entry(...)`:
    fallback: str = "next_open"      # was "signal"
and the default in `compute_structure_trade(...)`:
    entry_fallback: str = "next_open"   # was "signal"

Fix the entry_type classifier, which currently relies on `entry_idx > signal_idx` to
mean "pullback" — that heuristic breaks once the market fallback also advances the index:

    # market_structure.py:457 — REPLACE the index heuristic with an explicit flag
    # (have compute_pullback_entry also return whether the limit actually filled).
    entry_type = "pullback" if filled_limit else "market"

Concretely: change compute_pullback_entry to return a 3-tuple `(entry_price, entry_idx,
filled_limit: bool)` OR add a module-internal out-param. Recommend the 3-tuple (cleanest)
with the one internal caller (compute_structure_trade) updated. No other module imports
compute_pullback_entry directly (verify; the 11 scanners import compute_structure_trade
only).

`decision_idx` for stop/target: KEEP decision_idx = signal_idx for the market fallback
(stop/target are chosen at signal time, not at fill time — freezing them at signal is
correct and more conservative than letting them read the fill bar). This is a deliberate
non-change; document it in a comment so a future editor does not "fix" it back to entry_idx.

#### 1.3.2 Chart-pattern scanners — replace direct close-entry (the US-114 block)

For each confirmed site in §0(B), replace `entry = close[j]` / `entry = c` (where `c` is
the breakout/trigger close) with the NEXT BAR's OPEN:

    entry = open[j + 1]   (guard j + 1 < len(df); if the signal is the last bar, SKIP the
                           signal — you cannot realistically fill a next-day entry that has
                           no next day)

Files + line anchors (post-edit the coder re-greps to confirm no residual `entry = close`):
    scanner_t_head_shoulders.py:123,165
    scanner_u_double_top_bottom.py:108,141
    scanner_ag_wedge.py:131,142
    scanner_v_triangles.py:139,156
    scanner_w_flags_pennants.py:168,178   (confirm reachability first — see §0 discrepancy)
    scanner_s_elliott_wave.py:140,195
    + the §0(B) AUDIT-LIST files

Keep `entry_idx`/the exit walk start index as the SIGNAL bar so the shared
`_walk_forward_exit` (which iterates `range(entry_idx+1, ...)`) naturally begins checking
stop/target on the bar AFTER the signal — which for a next-open fill IS the fill bar.
Update each scanner's doc-string "entry = close[i]" → "entry = open[i+1]" (several carry a
stale v1.x note). This is a comment change, no logic.

NOTE on the shared struct: the 11 structure scanners already share market_structure; the
chart-pattern scanners do NOT. Do NOT refactor them onto market_structure in this story
(scope creep). US-173 is the narrow two-site fix above; a later consolidation may unify.

#### 1.3.3 walk_forward.py — recompute entry before costing (Layer B "with costs")

walk_forward.apply_costs() and apply_gap_risk() today consume the scanner's already-look-
ahead `entry = close[i]`. With §1.3.1/§1.3.2 fixed upstream, re-run scanners emit the
next-open entry and these functions are already correct (they cost whatever entry_price
they receive). The ONE remaining change is that apply_gap_risk() already reads the
next bar's open for stop-gaps; it must NOT double-apply a next-open shift if entry_price
is already next-open. Confirm apply_gap_risk only adjusts the STOP side (it does — it
compares next_open to stop, not entry) — no change needed beyond a confirming test.

If US-173 must run WITHOUT re-scanning (i.e., on EXISTING close-entry phase1a CSVs), add a
CSV-level shim: a new shared helper `apply_next_open_entry(signal, df)` that, given a
signal dict with `entry_price == close[signal]` and a `date`, locates the signal bar,
overwrites `entry_price = open[signal_bar + 1]`, records the adverse delta, and re-rates
`r_multiple` by `(close[s] - open[s+1]) / risk` for longs (mirrored for shorts). This shim
is the backward-compatibility bridge of §1.4 — use it ONLY for legacy CSVs, never for
freshly-scanned output (which is already next-open).

    # walk_forward.py (or a new scripts/validation/fill_convention.py) — DECIDED: new file
    def apply_next_open_entry(signal: dict, df: pd.DataFrame, direction: str) -> dict:
        # locate signal bar by signal["date"]; s = its index; if s+1 >= len(df): return signal
        # old_entry = signal["entry_price"]; new_entry = float(df["open"].iloc[s+1])
        # risk = abs(old_entry - stop); drift_r = (old_entry - new_entry)/risk  (long: adverse>0)
        # r_multiple -= drift_r  ;  entry_price = new_entry ; entry_fill = "next_open"
        # add keys: fill_convention="next_open", lookahead_shim=True, entry_drift_r=drift_r

    Put it in scripts/validation/fill_convention.py so BOTH walk_forward.py and the
    discovery runners import the same function (single owner, mirrors how pnl_accounting
    unified the hostile fill helpers).

#### 1.3.4 run_phase1a.py / run_phase1a_v2/v3_*.py / walk_forward_us114.py — versioning

These runners do NOT set the fill; they call scanner run_backtest() and (walk_forward_us114)
read r_multiple straight from the phase1a CSV. The fix lives upstream (§1.3.1/§1.3.2).
Their US-173 responsibility is ONLY: (a) they must re-run on the corrected scanners to
regenerate CSVs, and (b) the regenerated CSVs must be VERSIONED so historic close-entry
backtests are never silently reinterpreted. See §1.4.

### 1.4 Backward-compatibility / versioning (MANDATORY — user has flagged silent data
loss as unacceptable)

The existing `*-phase1a.csv` / `*-stocks-phase1a*.csv` files in scripts/validation/results/
were produced with close-entry fills. After US-173, regenerating them under next-open
produces DIFFERENT numbers. Do NOT overwrite in place. ENFORCE:

  1. New result files carry a version discriminator: `{id}-phase1a-v4.csv` (or a
     `fill=next_open` token). The runners append `-v{N}` and bump N on ANY fill-semantics
     change. US-114 used v1→v2 and US-115 used v3; US-173 is the next bump (v4).
  2. Add a fill-convention column/record to every emitted CSV: `fill_convention = "next_open"`
     (and `signal_bar_close_entry = False`). walk_forward.py's in-memory signal dicts get
     the keys from §1.3.3. Auditors can then tell a next-open backtest from a close-entry
     one by inspection, not inference.
  3. walk_forward_us114.py / walk_forward.py MUST read `fill_convention` when present and
     REFUSE (raise, fail-closed) to compute a promotion verdict from a CSV that lacks it
     (i.e., a legacy close-entry CSV) unless the §1.3.3 shim is explicitly invoked with
     `--shim-legacy-close-entry`. Default: refuse. This preserves the honest interpretation
     of historic numbers while preventing them being silently re-scored under a fill model
     they were never tested on.
  4. Backtest metadata (phase1a-summary.md, walk-forward reports) gains a
     `fill_convention: next_open (US-173)` line so the re-evaluation trail is citable.

### 1.5 Cost-delta summary (what changes)

- Every market/fallback entry moves from close[signal] to open[signal+1] → systematically
  adverse for breakout/continuation signals (buy higher / sell lower) by ~0.1–0.4% ≈
  0.05–0.3 R on a 1–3% stop.
- Plus the fee round trip already being applied (fee_source: stock 3 bps, crypto 12 bps) →
  0.01–0.12 R.
- Net realistic drag ~0.1–0.3 R/trade for the pattern strategies. Most promoted edges
  (0.08–0.22 R frictionless OOS) collapse to ≤ 0 under this — which is exactly the finding
  US-174 must now enforce. STR-B's ~+1.25 R OOS is the only survivor by margin.

---

## 2. US-174 — Mandatory G3 fill-realism promotion gate

### 2.1 Ambiguity RESOLVED: which fill model "realistic / pessimistic" means

execution_sim.py is an L2-orderbook crypto intraday simulator. It cannot price a daily-bar
stock breakout (no L2 book exists). The gate must be ASSET-CLASS + TIMEFRAME aware and
fail-closed on the conservative interpretation:

  - INTRADAY CRYPTO (5m/1h/6h perps): use execution_sim.batch_simulate() with
    FillMode.REALISTIC and FillMode.PESSIMISTIC over the trade's L2 snapshots. This is the
    existing G3 path; "realistic mean R > 0" reads batch_simulate(REALISTIC)["mean_net_r"],
    "pessimistic PF > 1.0" reads batch_simulate(PESSIMISTIC)["pf"].
  - DAILY-BAR SWING / PATTERN (stocks AND crypto daily): use the BAR-LEVEL hostile model
    already in pnl_accounting.py + fee_source + the US-173 next-open shim:
        * REALISTIC  = next-open entry (§1.3.3) + fee_source round-trip cost drag
          (cost_adjuster.compute_cost_drag) + the scanner's existing _walk_forward_exit
          intrabar stop/target (stop capped at −1R, target fills when reached).
        * PESSIMISTIC = next-open entry + taker both legs + stop at WORST print
          (_worst_print: bar low for longs / high for shorts) + target fills ONLY if the
          bar trades THROUGH (_trades_through). This is hostile_fills.py's model, exposed
          as a reusable function rather than re-implemented.

    This is an EXPLICIT resolution: "realistic/pessimistic" is NOT a single universal mode;
    it is a dispatch. The coders must NOT call execution_sim on daily-bar stock trades
    (it would silently treat a missing L2 book as zero depth → wrong). Put the dispatch in
    one function so the asset-class branch cannot be gotten wrong at call sites.

### 2.2 The exact gate check (thresholds DECIDED)

A strategy MAY be promoted to LIVE or WATCH (status validated in the note, registry status
in regime_strategy_selector.py) IFF ALL of the following hold on its OUT-OF-SAMPLE / most
recent walk-forward trade set:

  G3.1  n_trades >= 10                                  (else fail-closed "INSUFFICIENT DATA";
                                                         reuse walk_forward_us114.MIN_OOS_TRADES)
  G3.2  realistic mean R > 0                            (strictly positive; == 0 ALSO fails —
                                                         the story says "edge is positive",
                                                         not "non-negative")
  G3.3  pessimistic profit factor > 1.0                 (net-positive under worst-case fills;
                                                         matches PROP-001 G3 "pessimistic PF > 1.0")
  G3.4  realistic mean R >= 0.60 × optimistic mean R    (edge-decay cap; matches PROP-001 G3
                                                         "realistic ≥ 60% of optimistic")

G3.2/G3.3 are the hard mandatory gates (the "edge survives realistic/pessimistic fills"
requirement). G3.4 is the decay sanity that catches an edge that survives only because the
optimistic baseline was absurd. All four are fail-closed: any false → REJECT.

Rationale for using BOTH realistic mean R and pessimistic PF: mean R > 0 can be positive
with a losing tail and PF ≤ 1 (and PF is the standard gauntlet metric). Requiring both keeps
the gate consistent with PROP-001 and prevents a strategy that wins narrowly-but-rarely from
slipping through on a positive mean alone.

### 2.3 Where it hooks (the promotion path)

There is NO single existing `promote()` function. Promotion today is agent-driven edits to
(a) the strategy note frontmatter (`status:`, `confidence:`) and (b)
regime_strategy_selector.STRATEGY_REGISTRY status. US-174 must create a single choke-point
and fail closed at BOTH ends.

  NEW MODULE: scripts/gauntlet/g3_gate.py

    from cost_adjuster import compute_cost_drag, batch_adjust
    from fee_source import get_round_trip_bps, get_taker_bps
    import execution_sim as es                       # intraday crypto branch only

    class FillRealismGateError(RuntimeError): ...     # carries strategy_id + reason + metrics

    def evaluate_fill_realism(strategy_id, trades, asset_class, timeframe) -> GateResult:
        # dispatch: intraday-crypto -> execution_sim batch (REALISTIC/PESSIMISTIC);
        #            else          -> bar-level realistic/pessimistic (§2.1)
        # returns { n, optimistic_mean_r, realistic_mean_r, pessimistic_pf,
        #           edge_decay_ratio, passed: bool, reasons: [str] }

    def assert_g3_gate(strategy_id, trades, asset_class, timeframe) -> dict:
        # evaluate_fill_realism(...); if not passed: raise FillRealismGateError
        # with reason "NO CLAIMABLE EDGE UNDER REALISTIC FILLS: realistic mean R = {x} <= 0
        # (pessimistic PF = {pf})"  — fail-closed, no silent downgrade.
        # else return the gate record (to be written into the strategy note).

    def promote_strategy(strategy_id, *, trades, asset_class, timeframe) -> dict:
        # THE ONLY sanctioned promotion entry point. Calls assert_g3_gate() FIRST; on pass,
        # flips the note status -> validated and the registry status -> LIVE/WATCH (or
        # returns the mutation plan for the swarm to apply — see note below). On fail, does
        # NOT mutate anything and raises.

  HOOK 1 — validate_strategy.py (enforcement at the notes gate):
    Add a REQUIRED check in validate_file(): any strategy whose frontmatter `status` is
    `validated` (the only status eligible for LIVE/WATCH) must carry a
    `g3_fill_realism` evidence — either
        (a) a frontmatter field set by promote_strategy: e.g.
            g3_realistic_mean_r: 0.42   g3_pessimistic_pf: 1.31   g3_passed: true
        or (b) a ## Supporting Evidence wikilink to a gate-artifact note recording the same.
    If `status == validated` AND the gate artifact is missing OR records a non-positive
    realistic mean R → return status 'fail' → validate_strategy.py sys.exit(1) → the
    strategy CANNOT be promoted (blocks the note AND, via the swarm gate, the registry edit).

  HOOK 2 — regime_strategy_selector.py (defense-in-depth at runtime):
    get_strategy_directives() currently emits `run`/`boost` for any registry entry not
    KILLED. Add: a strategy whose registry status is LIVE/WATCH but whose gate artifact is
    missing/failing is coerced to `suppress` (risk_multiplier 0.0) with
    reason "no valid G3 fill-realism gate on file". This is the belt-and-suspenders guard so
    a stale registry entry cannot trade even if a note was edited out-of-band.

  Note on who mutates notes/registry: per the swarm hard rule, all code changes route
  through the swarm. promote_strategy() is the FUNCTIONAL gate; the actual file edits remain
  the swarm's job. The coder implements evaluate_fill_realism / assert_g3_gate / the two
  hooks; the orchestration agent calls assert_g3_gate before recording a LIVE/WATCH status
  anywhere.

### 2.4 Failure behavior (DECIDED: REJECT, not flag)

Fail-closed REJECT. On any of G3.1–G3.4 failing:

  - assert_g3_gate raises FillRealismGateError; promote_strategy performs NO mutation.
  - validate_strategy.py returns 'fail' (exit 1), blocking the note and the promotion.
  - The recorded reason is "NO CLAIMABLE EDGE UNDER [REALISTIC/PESSIMISTIC] FILLS" with the
    computed realistic mean R and pessimistic PF — matching the story's exact wording.
  - No "flag-only" or "soft warn" path. A strategy that cannot demonstrate a positive edge
    under realistic fills is NOT promoted; it stays Hypothesis (or is demoted if already
    WATCH). It is not auto-KILLED here — demotion to Hypothesis is the correct default; a
    deliberate KILL is a separate, human/squad decision (scope discipline).

### 2.5 ADR / gauntlet-spec wording change that makes it binding

Two edits, both binding:

  1. PROP-001 G3 ("Execution realism") — APPEND to the Pass line:
       > G3 is MANDATORY and fail-closed for promotion. A strategy cannot be promoted to
       > LIVE/WATCH unless its realistic-fill mean R > 0 AND pessimistic PF > 1.0 (and
       > realistic ≥ 60% of optimistic). A strategy with a non-positive realistic edge is
       > REJECTED ("no claimable edge under realistic fills"), never flagged-through.

  2. ADR-004 — add "Amendment 2 — Fill-Realism Promotion Gate (US-174, 2026-11-01)":
       | Rule | Definition |
       | **Promotion pre-condition** | No strategy is promoted to LIVE or WATCH unless its OOS edge is positive under realistic fills: realistic mean R > 0, pessimistic PF > 1.0, realistic ≥ 60% of optimistic, n ≥ 10. |
       | **Enforcement point** | validate_strategy.py (note gate, exit 1) + a pre-promotion assert (g3_gate.assert_g3_gate). Fail-closed; a non-positive realistic edge REJECTS promotion. |
       | **Fill models** | Intraday crypto → execution_sim REALISTIC/PESSIMISTIC (L2). Daily-bar swing → next-open entry (US-173) + fee_source round-trip + worst-print stops / trade-through targets. |
       | **Consequence of retro-audit** | Any LIVE/WATCH strategy that fails this gate on re-evaluation is demoted to Hypothesis with a "no claimable edge under realistic fills" note (the 16 chart-pattern block and the thin crypto-factor edges are expected to fail it). |

---

## 3. Explicit non-goals / cautions (read before implementing)

- US-173 does NOT refactor the chart-pattern scanners onto market_structure. Two narrow
  sites only (§1.3.1, §1.3.2). Consolidation is a separate, later story.
- US-173 does NOT change execution_sim.py or the intraday crypto path (no close-entry bug
  there). US-174's G3.4 dispatch touches execution_sim only as a CONSUMER, never its body.
- US-174 does NOT auto-KILL strategies that fail the gate — it REJECTS promotion (demote to
  Hypothesis). KILL remains a deliberate decision.
- Do NOT silently overwrite the legacy close-entry CSVs (§1.4). Version them. This directly
  serves the principal's "no silent data loss" hard rule.
- fee_source.py is the SINGLE fee table (already built by US-165). The gate consumes it;
  do not reintroduce a parallel fee constant.
- The scanner_w_flags_pennants.py discrepancy (§0) is flagged, not assumed. The coder
  investigates reachability before editing.
- Order of work: US-173 first (fill semantics), green on its own; then US-174 (gate) which
  consumes the next-open/hostile fill. Do not reorder.

END OF DESIGN.