# EPIC-017 Phase 4 — US-211 & US-212 full-Gauntlet verdicts (REAL data)

Date: 2026-11-02 · Author: Backtester (HermesForge)
Scope: the two P1 research stories — US-211 (BTC-residualized xsmom) and
US-212 (funding-extreme unwind at swing horizon). Both pre-registered (US-202
frontmatter incl. counterparty), run on real Hyperliquid data, under the
recalibrated G0/G1/G7 gates (ADR-008/009/010, code landed this session). Every
run wrote a fresh `param_hash` to the append-only trials ledger and counts
toward G5. No fabricated data, no look-ahead, cost counted once, no leverage
(MARGIN_CAP 1.0), `LIVE_TRADING_ENABLED` off.

Pre-registration rows: `data/gauntlet/hypotheses.jsonl` — HYP-14 (US-211),
HYP-15 (US-212). Trials: `data/gauntlet/trials.jsonl` (HYP-14 `52fd85be…`,
HYP-15 `6e5a8591…`).

---

## US-211 — BTC-residualized cross-sectional momentum (HYP-14)

### Pre-registered hypothesis
Rank the 31-name Hyperliquid perp universe on **BTC-residualized 30-day
momentum**: regress each coin's daily returns on BTC (rolling 60d beta,
estimated on data through t-1 → look-ahead-free), build the residual-return
series, long the top quintile. Goal of the story: strip the BTC-beta that sank
the raw xsmom (US-182) at G4/G5.

- `counterparty`: "Alt-coin momentum under-reaction idiosyncratic to the coin
  *after* stripping the systematic BTC move — late trend-followers / delayed
  indexers who chase the residual drift, not the beta, and pay the spread."
- falsification (pre-registered): residualizing fails to clear the overfit
  controls (10th-pct split PF < 1.0 OR PBO ≥ 0.30 OR DSR ≤ 0.95 OR the residual
  still concentrates in < 2 beta clusters).

### Gate-by-gate outcome (residualized, kappa=0.5 band=0.25, weekly)

| Gate | Measure | Value | Bar | Result |
|---|---|---|---|---|
| G0 | cost-aware edge (12 bps charged once) | net R +0.19 | > 0 after cost | pass (thin) |
| G1 | measured μ_R=+0.190 / σ_R=3.572 → N_min(power) | **2773** (> 180 episodes) | ≥ max(2773, 200) | **FAIL** |
| G1 | breadth (distinct symbols) | 31 | ≥ 15 | pass |
| G3 | realistic mean R / pessimistic PF | +0.190 / 1.148 | > 0, > 1.0 | pass |
| G4 | CPCV split PF median / 10th-pct / min | 1.136 / **0.670** / 0.342 | 1.3 / 1.0 / budget | **FAIL** |
| G5 | DSR / PBO | **0.479** / **0.439** | > 0.95 / < 0.30 | **FAIL** |

Side-by-side vs the prior RAW run (same harness, reproduced verbatim):

| metric | RAW | RESIDUALIZED | Δ |
|---|---|---|---|
| mean net R | +0.5911 | +0.1900 | −68% |
| PF | 1.351 | 1.163 | |
| net Sharpe | 0.759 | 0.385 | |
| CPCV 10th-pct PF | 0.723 | 0.670 | still < 1.0 |
| PBO | 0.561 | 0.439 | still > 0.30 |
| DSR | 0.704 | 0.479 | worse |
| mean \|BTC beta\| | 1.857 | 0.537 | −71% |

### Verdict — STILL BETA, NOT A GENERALIZABLE ALPHA

Residualizing BTC did exactly what it was supposed to do to the *beta* (mean
|beta| 1.857 → 0.537), but it also stripped **68% of the edge** (+0.591 → +0.190
R). The correct reading of that is the one the raw run already hinted at: the
raw "edge" **was** the BTC beta. What remains after stripping it is a thin,
unstable idiosyncratic momentum signal that:

1. fails G1's recalibrated statistical-power floor (measured μ_R/σ_R imply
   N_min ≈ 2773 weekly-rebalance samples to detect a +0.19 R edge; only 180
   exist),
2. still fails G4 (10th-pct split PF 0.670 < 1.0, median 1.136 < 1.3),
3. still fails G5 (DSR 0.479 < 0.95, PBO 0.439 > 0.30, and DSR actually *fell*
   as the Sharpe collapsed),
4. remains regime-concentrated (bull +0.68 R vs bear −0.47 R).

The residualization is a **successful diagnostic, not a successful strategy**:
it proves the raw xsmom was a directional BTC-beta book wearing a momentum label.
Conclusion: **no promotion; stays Hypothesis.** Do not re-run this construction
with wider windows expecting a different answer — the residual edge is below the
detectability floor on the available ~4y of daily bars.

---

## US-212 — funding-extreme unwind, swing 4-48h (HYP-15)

### Pre-registered hypothesis
Fade crowded positioning when hourly funding > 95th percentile AND OI still
rising, using HL funding percentile + OKX funding spread + OI-delta quadrant.
This is the **positioning-conditioned** replay of the funding signal, distinct
from the naked directional carry that structural analysis (US-179/185) already
rejected (price risk 20–39× funding).

- `counterparty`: "Late retail longs crowding a high-funding regime — they
  accept negative funding carry because they are momentum-chasing, not
  carry-aware, so the unwind pays them to hold and price corrects against them."
- falsification: Sharpe < 0.5 over 200+ trades, OR the honest funding-only edge
  (funding_pnl − cost, basis stripped) disappears below the 80th percentile.

### Data reality (decides what is honestly testable)

| feed | depth | status |
|---|---|---|
| hl fundingHistory | ~400d hourly, 35 coins | **full** |
| hl assetCtx openInterest (OI-delta) | 12 rows | forward-only |
| cross-venue OKX funding spread | 6 rows | forward-only |
| hl assetCtx markPx (directional move) | 12 rows | forward-only |

The **load-bearing** parts of the construction — OI-delta quadrant and the OKX
funding spread, plus the mark-price series needed for the directional unwind —
have **essentially no historical depth** (6–12 hours, begun accumulating this
session). Only the **naked funding-percentile replay** is testable today.

### Gate-by-gate outcome (funding-percentile carry, what is testable)

4,132 episodes across 35 coins; mean hold 9.3 h; 93% exit on percentile revert.

| Gate | Measure | Value | Bar | Result |
|---|---|---|---|---|
| G0 | median funding-only capture | **−11.26 bps** | ≥ ~48 bps (4× cost) | **FAIL** |
| G1 | measured μ_R | **−0.0976** (σ 0.066) | > 0 | **FAIL** (non-positive edge) |
| G3 | funding-only PF / Sharpe | 0.054 / −1.47 | PF > 1.0 | **FAIL** |

The honest decomposition (funding component only, basis stripped and reported
separately as `none` — never folded in):

- funding collected over all episodes: **+$926,483**
- round-trip cost (12 bps × 4,132 episodes on 1× notional): **$4,958,400**
- cost is **5.3× the funding collected** — the mean hold is only ~9.3 h because
  funding reverts from the 95th to the 80th percentile too fast for the carry to
  amortize a 12-bps round trip.

### Verdict — FUNDING CARRY IS NOT THE EDGE; the unwind itself is DATA-GATED

The honest **funding-only** component is decisively negative (−0.10 R mean, PF
0.05): collecting funding while fading extremes does not come close to covering
friction. This is the same "edge < friction" failure the pipeline already
records, and it re-confirms that naked funding carry is not a standalone alpha.

The actual unwind *thesis* (crowded longs mean-revert in price) depends entirely
on (a) the directional move and (b) the positioning conditioning (OI-delta +
OKX spread) that distinguishes it from naked carry — **both are data-gated**
(forward-only feeds, no history). It therefore **cannot be validated or rejected
on merit today**; it dies at G0/G1 on the carry component alone, and the
positioning-conditioned replay cannot yet reach G4/G5.

Conclusion: **no promotion; stays Hypothesis, data-gated.** The correct
follow-up is the Phase-1 Data-depth work (US-197…201) that accumulates OI and
cross-venue spread history — not a re-run of the naked carry, which is already
known to be negative.

---

## Cross-cutting outcome

Both P1 Phase-4 hypotheses produce a **no-promotion** verdict, for opposite
reasons that are each instructive:

- **US-211** was *testable and tested* — and failed because residualizing
  exposed the edge as beta, not alpha (a clean, decisive negative).
- **US-212** was *only partially testable* — the funding component fails on
  friction, and the distinguishing positioning condition is blocked on data
  depth before it can reach the gates that matter (G4/G5).

Neither advances past Hypothesis. The trials ledger now carries two new
pre-registered, hash-chained, counted trials feeding G5's N.

Trials written (append-only, SHA256-chained, integrity verified OK):
- HYP-14 `52fd85beb993…` (btc_residualized, 180 episodes)
- HYP-15 `6e5a8591d993…` (funding_only_carry, 4132 episodes)

Driver sources (read-only research; no production modules mutated):
- `scripts/gauntlet/preregister_us211_us212.py`
- `scripts/gauntlet/revalidate_xsmom_residualized.py`
- `scripts/gauntlet/revalidate_funding_unwind.py`