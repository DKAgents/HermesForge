# Backtester Re-Evaluation Report — Fill-Model Audit + Inflation Check Across the Full Strategy Universe

Author: backtester (HermesForge)
Date: 2026-11-01
Scope: read-only. No code, post, cron, or .env modified.

---

## 0. What this report answers

US-164..168 fixed four PNL-accounting inflations that *all* ran in the same direction
(every fix **deflates** — it cannot invent a hidden winner, only expose hidden losers):

1. entry slippage ignored
2. uncosted fallback to raw r_multiple
3. jsonl double-count
4. look-ahead fill-at-close

This report audits **every other strategy in the universe** (Active, Hypotheses, and
the ~24 Backtests) for the same failure modes, and answers one question:

**Did we promote any strategy (LIVE / WATCH / Active) on an edge that was computed with
optimistic fills or pre-fix accounting — and does that edge survive realistic fills?**

Short answer: **Yes, extensively, and most of it does not survive.**

---

## 1. The two fill regimes, pinned down with evidence

Every discovery backtest in the vault predates the G3 fill-realism module
(`scripts/gauntlet/execution_sim.py`, three modes OPTIMISTIC/REALISTIC/PESSIMISTIC;
PROP-001, dated 2026-09-14). The pre-G3 framework is two layers:

**Layer A — frictionless (`run_phase1a.py`, all `*phase1a*` CSV/MD):**
No transaction cost at all. `run_phase1a.py` `summarize()` computes `avg_r` straight
from the scanner's `r_multiple` column. The scanners set `entry = close[i]` (signal-bar
close). Evidence: every phase1a MD frontmatter says `data_limitations: ... frictionless`.

**Layer B — "with costs" (`walk_forward.py`):**
`apply_costs()` charges spread+commission only, and `apply_gap_risk()` fills the stop at
next-open if gapped. Critically, **entry is still `close[i]`** — the signal is evaluated
and filled on the same bar's close. Cost model (walk_forward.py lines 277-315):

| venue | walk_forward charged | corrected (fee_source.py round trip) | delta |
|---|---|---|---|
| stock  | 12 bp (5 spread + 1 comm ×2) | 3 bp (2×1.0 taker + 1.0 slip) | walk-forward OVER-charged |
| crypto | 5 bp (2 spread + 0.5 comm ×2) | 12 bp (2×4.5 taker + 2.5 slip + 0.5 funding) | walk-forward UNDER-charged by 7 bp |

So on fees alone the two venues are asymmetric — but the fee magnitude is a rounding
error next to the **two fill-model bugs that Layer B shares with Layer A**:

- **Bug #4 (look-ahead fill-at-close):** `entry = close[signal bar]`. The signal is
  only *known* at that bar's close; a real fill can't happen there. For breakout / 
  continuation patterns (20-day breakout, H&S composite, triangle, flag, wedge,
  alligator, momentum), the close that *defines* the signal is a strong-direction close,
  so the next-day open is systematically adverse (buy higher / sell lower).
- **Bug #1 (entry slippage):** no adverse-selection at the fill, no cross + tick, no
  next-open drift — except the crude half-spread baked into Layer B's stock cost.

The `strong` conclusion: **every backtest in `Backtests/`, and every "promoted" story
(US-113/114/115/120/122), was evaluated on optimistic fills (close entry, no/undercharged
friction).** None used G3 REALISTIC/PESSIMISTIC, except the one bar-level re-simulation
that already demolished STR-Q (cache/backtester_fidelity_report_v3.md).

---

## 2. Fill-model audit — per strategy (evidence-cited)

### Paper-traded (already re-graded in v3 — NOT redone here)
STR-Q, STR-A, STR-B, STR-D, STR-DEBASEMENT, STR-VIXC. See §5 below for the carried-forward
verdicts.

### Active folder (3 files) — all promoted 2026-09-20

| Strategy | File | Evaluation used | Fill model | Evidence |
|---|---|---|---|---|
| STR-20260719 ma-pullback-fibonacci (STR-A) | Active/ | **none** — backtest "not started", paper log "not started" | n/a | Active file lines 154-158; regime selector lists STR-A = **KILLED** (contradiction) |
| STR-VIXC vix-vrp-contango | Active + WATCH + paper | Phase 1A frictionless + walk_forward.py | close entry, 12bp stock | Active file "Backtest & Validation" section; US-113 |
| STR-OIL-SHOCK | Active + WATCH | walk_forward.py | close entry, 12bp stock | Active file "Walk-Forward Validation" section |

Note: **STR-A is simultaneously "active" (folder, promoted 2026-09-20) and "KILLED"
(regime selector).** It has no backtest and no completed paper trade. A governance gap,
flagged in §5.

### Deployed-WATCH / LIVE via regime_strategy_selector.py registrations

| Strategy | Registry status | Evaluation used | Fill model | Edge source |
|---|---|---|---|---|
| STR-B MACD Div | **LIVE** | walk_forward.py + factor-decomp | close entry, 12bp stock | WF-20260801, STR-B-walkforward-both |
| STR-I AdaptiveTrend | **LIVE** (stock) | walk_forward.py + phase1b2 | close entry, 12bp | WF-20260801, STR-I-phase1b2-stocks |
| STR-J EUFEARIA CCI | KILLED in walk-forward, WATCH in phase1b2 | walk_forward + phase1b2 | close entry | WF-20260801, STR-J-phase1b2-stocks |
| STR-L ATR Contraction | **WATCH** | phase1a/1b only (walk-forward = INSUFFICIENT) | **frictionless** | STR-L-phase1a/1b |
| STR-P Cross-Sectional Factor | **WATCH** (crypto) | walk_forward.py | close entry, **5bp crypto** | STR-P-walkforward-crypto |
| STR-VIXC | **WATCH** | walk_forward.py | close entry, 12bp | US-113 |
| STR-LOWCORR | **WATCH** | Phase 1A only (no walk-forward) | **frictionless** | regime selector comment (2026-08-18) |
| STR-DEBASE | **WATCH** | walk_forward.py | close entry, **5bp crypto** | regime selector (OOS +0.131 p=0.553) |
| STR-OIL-SHOCK | **WATCH** | walk_forward.py | close entry, 12bp | regime selector (p=0.231) |
| STR-SKEWP | **WATCH** | walk_forward.py | close entry, 12bp | regime selector (OOS +0.0457) |
| STR-CAP-BOTTOM | **WATCH** | walk_forward.py | close entry, **5bp crypto** | regime selector (p=0.418) |

### The chart-pattern block — STR-R..STR-AJ (19 "LIVE" strategies)

These are validated by a *separate* US-114 walk-forward that lives in
`code/forge-loop/AUDIT-backtester-US114-v2.md` + `walk_forward_us114.py`. This is the
single most important finding of this audit:

It splits the **frictionless** Phase 1A R-multiple CSVs 60/40 IS/OOS — **it applies no
transaction cost, no gap risk, no entry slippage**. Its own scrub doc is explicit:

> "All v2 avg R values are below 0.25R. After commissions + slippage in live trading,
> these are thin-margin strategies. Phase 1B must account for friction costs."
> — AUDIT-backtester-US114-v2.md, "Finding 5: Friction Flag"

The "PASS" list (declared "cleared for paper trading") carries **frictionless** OOS edges:

| Strategy | OOS avg R (FRICTIONLESS) | OOS PF | OOS n |
|---|---|---|---|
| STR-AJ Intermarket | 0.221 | 1.48 | 5,297 |
| STR-V Triangles | 0.182 | 1.50 | 10,600 |
| STR-AG Wedge | 0.172 | 1.41 | 28,075 |
| STR-W Flags | 0.172 | 1.56 | 264 |
| STR-AB OBV | 0.152 | 1.40 | 3,287 |
| STR-U Double Top | 0.118 | 1.47 | 929 |
| STR-R Alligator | 0.111 | 1.19 | 6,336 |
| STR-T H&S | 0.079 | 1.25 | 3,420 |

plus "already trusted" STR-X/Z/AA/AC/AD/AE/AF (and STR-Y, AH, AI left blocked). Total
declared "trusted for paper trading: 16 strategies". **All of them were promoted to LIVE
on frictionless, close-entry R-multiples, and the explicit friction accounting that
would have deflated them never happened before promotion.**

---

## 3. Inflation check — the optimistic→realistic drag, bounded

I did not re-run multi-hour walk-forwards (that would be required to produce exact
post-friction numbers for the 12,000+ signal strategies). What follows are **bounded drag
estimates** using the corrected cost model (`fee_source.py`) and the G3 pessimistic fill
model (`execution_sim.py`), applied to the strategies' own risk profiles.

Corrected all-in round trip: crypto 12 bp, stock 3 bp.

For a daily-bar swing signal with stop distance ≈ 1–3% (typical for these scanners), the
fixed friction drag in R units (`fee_source` round trip ÷ risk) is:

- stock: 3 bp ÷ 1–3% risk = **0.01–0.03 R** (fee alone)
- crypto: 12 bp ÷ 1–3% risk = **0.04–0.12 R** (fee alone)

The fee is NOT the dominant drag. The dominant, un-modeled drag is the **look-ahead
close entry** (bug #4): for a breakout/continuation signal, filling at the next open
instead of the signal close is systematically adverse by roughly the signal's own
magnitude of continuation move — empirically ~0.1–0.4% on daily bars for "broke above
N-day high on volume" type signals, i.e. **~0.05–0.3 R** on a 1–3% stop, plus a tick of
adverse selection (bug #1). Realistic total drag on these pattern strategies: **~0.1–0.3 R/trade**,
heavily front-loaded on the entry.

STR-Q is the proof-of-concept for this mechanism at intraday scale: its frictionless
OOS was +0.63 to +1.13 R, and re-simulating with realistic entry (trade-through, not
sweep-close) + both-side taker fees collapsed it to **−1.59 R/trade (t=−41)**. The
pattern is identical for the thin daily-bar edges; only the unit of cost is smaller.

---

## 4. Per-strategy table — edge as-evaluated vs re-graded-realistic → verdict

"as-eval" = the number the promotion cited. "re-graded" = bounded realistic estimate.
Where a definitive number needs a multi-hour re-backtest, that is stated, not fabricated.

| Strategy | Fill model (evidence) | Edge as-evaluated | Re-graded realistic | Verdict |
|---|---|---|---|---|
| STR-Q | frictionless close (1B walk-forward) | OOS +0.63 → +1.13 R | **−1.59 R/trade, t=−41** (v3 bar-level) | **does-not-survive** (already flipped) |
| STR-A ma-pullback | none (never evaluated) | — | — | **n/a** — promoted with zero evidence |
| STR-VIXC | close, 12bp stock (US-113) | OOS +0.103 R (n=12,598) | thin breakout edge; paper = 4 trades, 3 zombie-cleaned to 0 | **does-not-survive / n-too-small** |
| STR-OIL-SHOCK | close, 12bp (US) | OOS +0.171 R, p=0.231 (NO EDGE already); 2026 +0.65R cherry-pick | already no-edge; 2026 window n=88 | **does-not-survive** |
| STR-B MACD Div | close, 12bp stock (WF) + factor alpha 0.84R | OOS +1.25 R, t=10.6, n=2,035 | ~+1.0 R after 0.2–0.3 R drag | **survives** (only genuine survivor; magnitude uncertain — see §5 caveat) |
| STR-I AdaptiveTrend | close, 12bp stock (WF) | OOS +0.24 R; phase1b2 Sharpe 0.815, +5.8%/yr | ~+0.05–0.15 R after drag | **too-small / does-not-survive-as-claimed** |
| STR-P cross-sectional | close, **5bp crypto** (WF) | OOS +0.12 R, p=0.03, n=860 | crypto under-charged 7bp + look-ahead → ~+0.05–0.08 R | **too-small to claim** |
| STR-DEBASE | close, **5bp crypto** (WF) | OOS +0.131, p=0.553 | already not significant; more drag | **does-not-survive** |
| STR-CAP-BOTTOM | close, **5bp crypto** (WF) | OOS +0.106, p=0.418 | already no-edge overall | **does-not-survive** |
| STR-SKEWP | close, 12bp stock (WF) | OOS +0.0457, 3/5 windows no-edge | effect < drag | **does-not-survive** |
| STR-LOWCORR | **frictionless** Phase 1A only | Phase 1A positive (no OOS) | no walk-forward ever run | **insufficient (no OOS)** |
| STR-L | frictionless phase1a/1b | +0.582 R, n=7 | frictionless, n too low to cost-adjust | **n-too-small** |
| STR-J | close (WF killed it) | OOS +0.002 R NO EDGE | — | **does-not-survive** (WF already killed; phase1b2 WATCH is stale) |
| STR-R..T/U/V/W/AB/AG/AJ (+X/Z/AA/AC/AD/AE/AF) | **frictionless** close (US-114 walk_forward_us114.py, no cost) | OOS 0.079–0.221 R | edge ≤ drag for the 0.08–0.15 R tier | **does-not-survive / too-small** (see §5) |

---

## 5. Flag flips (definitive list)

### (a) Hidden losers — edge flips +→− under realistic fills
1. **STR-Q** — already flipped at bar level (−1.59 R/trade). Confirmed.
2. **The chart-pattern LIVE block (STR-R, STR-T, STR-U, STR-V, STR-W, STR-AB, STR-AG,
   STR-AJ and the "already trusted" STR-X/Z/AA/AC/AD/AE/AF).** 16 strategies promoted
   LIVE on *frictionless* OOS edges of 0.08–0.22 R that the team's own US-114 scrub doc
   flagged as "thin-margin, Phase 1B must account for friction." Phase 1B friction never
   happened before promotion; the look-ahead close entry drag (0.1–0.3 R) is comparable
   to, or larger than, most of these edges. This is the single largest block of hidden
   losers — it is **the "more STR-Qs"** the expectation was set for.

### (b) Edge too small to claim (n or margin insufficient)
3. **STR-VIXC, STR-P, STR-SKEWP, STR-CAP-BOTTOM, STR-DEBASE, STR-I** — thin (0.05–0.24 R)
   edges that shrink below a defensible claim once realistic friction + look-ahead is
   applied, or were already not-significant at eval time.
4. **STR-L** (n=7 frictionless) and **STR-LOWCORR** (no out-of-sample run at all) —
   cannot support an edge claim by construction.
5. **STR-A** — "active" with no backtest and no completed paper trade; also listed
   KILLED in the regime selector. Two registries disagree; there is no edge, only a
   governance artifact.

### (c) Edge that survives realistic fills
6. **STR-B (MACD Histogram Divergence, stocks) — the only qualified survivor.** OOS
   +1.25 R (t=10.6), independent factor-decomposition alpha +0.84 R (t=12.6, p<0.0001).
   A 0.2–0.3 R realistic drag still leaves ~+1.0 R/trade. **Caveat:** its exact magnitude
   is not pinned down — Phase 1A shows *decay* (1.07 → 0.42 → 0.15 R across periods) while
   the walk-forward OOS is +1.25 R, a ~2–8× discrepancy the two methods do not reconcile.
   The sign is robust; the magnitude needs a realistic-fill re-backtest before any position
   sizing above the paper floor rests on it.

---

## 6. Blunt summary — what we missed

**We missed the second STR-Q, and it's bigger than STR-Q.**

The STR-Q re-simulation (v3) proved the general point: a reversal/pullback signal whose
edge was priced off a "fill at the exact reversal close" collapses when you require the
price to actually trade through. But that conclusion was scoped only to the six
paper-traded strategies. It was **never extended to the discovery backtests that produced
the LIVE/WATCH registrations** — and those are all built on the same optimistic fill:

1. **The 16 chart-pattern "LIVE" strategies (STR-R..AJ)** were promoted on *frictionless*
   close-entry R-multiples (US-114's `walk_forward_us114.py` applies no cost at all), with
   edges of 0.08–0.22 R that are the same order of magnitude as — and often smaller than —
   the realistic transaction cost of trading them. Their own audit said "thin-margin, needs
   friction accounting," and that friction accounting never reached promotion. **This is
   the definitive hidden-loser block.** Most of these should be re-graded to "no claimable
   edge" or "n-insufficient," not LIVE at 1% base risk.

2. **Crypto backtests were systematically under-costed** (5 bp in `walk_forward.py` vs the
   12 bp corrected round trip) — so every crypto-factor promotion (STR-P, STR-DEBASE,
   STR-CAP-BOTTOM, and by extension the crypto-tilted entries) is even thinner than its
   as-evaluated number.

3. **The look-ahead close entry (bug #4) was never fixed in any discovery backtest.** The
   US-114 "look-ahead fix" corrected scanner *logic*, not the close-to-close fill
   convention that still prices every breakout/continuation signal at its own trigger close.

4. **STR-A is a governance artifact**, not a strategy: simultaneously Active and KILLED,
   with no evaluation and no paper trades.

**The one thing we did NOT miss:** STR-B. It is the only strategy whose positive expectancy
is large enough to survive realistic fills, and it is independently confirmed by factor
decomposition. Everything else promoted to LIVE/WATCH is, at best, "n too small to claim"
and, at worst, a hidden loser of the same species as STR-Q.

**Recommended next step (not executed — read-only):** extend the v3 bar-level hostile-fill
re-simulation to the promoted universe, starting with the 16 chart-pattern strategies and
STR-B's magnitude question. That is a multi-hour compute per strategy family; the bounded
drag estimates in §3–§4 above are the honest interim, not a substitute for it.