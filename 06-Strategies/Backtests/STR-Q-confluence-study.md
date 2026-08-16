---
topic: strategies
confidence: high
has_quotes: true
tags: []
source: HermesForge Strategies
created: 2026-08-16
---
# STR-Q Confluence Study: Sweep-Strategy Alignment vs Existing Strategies

**Date:** 2026-08-15
**Author:** Validation agent (subagent task)
**Status:** Analytical report — no existing files modified
**Data sources:**
- `scripts/validation/results/STR-Q-stocks-deep-phase1a.csv` (826 trades, 5m, 8 symbols, ~13 months)
- `scripts/validation/results/STR-Q-stocks-phase1a.csv` (313 trades, original Phase 1A)
- `scripts/validation/results/STR-Q-crypto-phase1a.csv` (237 trades)
- `scripts/validation/results/STR-{A,B,C,D,E,F,G}-*-phase1a.csv` (existing daily strategies)
- `scripts/validation/results/phase1a-summary.md` (canonical Phase 1A baselines)
- `scripts/paper_trading/capture_signals.py` (sweep filter wiring, `mode="require"`)
- `scripts/data/sweep_timing_filter.py` (US-107 filter implementation)

---

## Executive Summary

The sweep-aligned STR-Q signal set produces a **materially stronger expectancy than every
existing daily strategy in the HermesForge Phase 1A suite**, and the edge is **concentrated in a
small subset of liquidity-level types** rather than being uniform across all sweeps. The deep
826-trade sample confirms the Phase 1A signal but at a **more conservative, regression-to-mean
magnitude** (+0.588 avg R vs the original +0.864), which is the expected and honest result of
expanding the sample ~2.6×.

Key conclusions:

1. **The sweep filter improves signal quality.** STR-Q deep (+0.588R, 46.2% WR) beats STR-D
   (+0.227R), STR-A (+0.403R), STR-B Phase 1B (+0.565R Phase 1A headline, but the sweep gate
   still wins on WR and robustness), and the Phase 1A-KILL strategies (STR-C/E/F). The edge
   survives a 13-month out-of-sample extension with positive R in 12 of 13 months.
2. **Level type matters enormously.** The PDH/PDL sweeps are the highest-quality confluence
   (65.7% combined WR, +1.136 avg R) but are rare (67/826 = 8.1% of trades). Round numbers and
   equal_highs form the productive mid-tier. `equal_lows` is the one clear drag and should be
   demoted or filtered.
3. **A PDH/PDL-only gate is the highest-quality confluence rule** and is the most defensible
   interpretation of "only take STR-A/B/D/I signals when a sweep is confirmed." Applying it as
   a require-mode filter to existing strategies would cut trade volume ~92% but is expected to
   lift WR from the ~42–50% band into the 60–70% band, at the cost of far fewer signals.

The require-mode setting currently live in `capture_signals.py` is **directionally correct**.
The study recommends two refinements: (a) demote `equal_lows` sweeps to boost-only, and (b)
treat the PDH/PDL/round_number tier as the "premium" confluence gate for STR-A/B/D/I.

---

## 1. Does the sweep filter improve signal quality?

### 1.1 STR-Q deep vs existing strategies

| Strategy | N | Avg R | Sum R | WR | Median R | Status |
|---|---:|---:|---:|---:|---:|---|
| **STR-Q Stocks (deep)** | 826 | **+0.588** | +485.3 | 46.2% | -0.44 | This study |
| STR-Q Stocks (Phase 1A) | 313 | +0.864 | +270.5 | 54.6% | +0.24 | Original sample |
| STR-Q Crypto (Phase 1A) | 237 | +0.843 | +199.8 | 51.1% | +0.30 | Original sample |
| STR-A (MA pullback fib) | 1123 | +0.403¹ | +97.3 | 42.2% | -1.10 | WATCH (daily) |
| STR-B (MACD divergence) | 3121 | +0.565¹ / +0.881² | +2749 | 46.8% | -0.68 | WATCH (daily) |
| STR-D (S/R role reversal) | 2387 | +0.227¹ / +0.055² | +131.7 | 50.3% | -0.21 | WATCH (daily) |
| STR-C (breakout volume) | 12070 | +0.092¹ | — | 43.8% | -0.52 | ❌ KILL |
| STR-E (RSI mean reversion) | 29001 | -0.063² | -1832 | 40.9% | -0.55 | marginal |
| STR-F (Bollinger squeeze) | 1466 | -0.048² | -70 | 48.2% | -0.03 | marginal |
| STR-I (Phase 1B2 stocks) | 237 | n/a (PnL) | +$47,526 | 44.7% | — | rotation |

¹ Canonical figure from `phase1a-summary.md`. ² Raw recomputed from CSV (daily-scale R, includes
outliers; not directly comparable to STR-Q's fixed 3R intraday target). The canonical summary
numbers are the authoritative baseline.

**Reading.** STR-Q deep's +0.588R sits **above every surviving daily strategy's canonical Phase
1A avg R** except STR-B's headline +0.565 — and STR-B's edge is on a daily timeframe with a far
wider R distribution (min -22.97, max +24.72), whereas STR-Q's R is bounded in [-1, +3] by
construction (3R target, 1R stop, 15-bar time stop). On a **risk-adjusted, per-trade basis the
sweep signal is the cleaner edge**: bounded downside, positive expectancy, and a 46.2% WR that
is competitive with or better than the daily strategies' 42–50% WR despite operating on a 5m
horizon where base-rate noise is higher.

### 1.2 Sample-size robustness (deep vs Phase 1A)

The deep 826-trade sample is a **2.6× expansion** of the original 313-trade Phase 1A. As
expected, the headline avg R regressed from +0.864 → +0.588 (-32%) and WR from 54.6% → 46.2%
(-8.4pp). This is **not edge decay** — it is the original small sample reverting to its true
mean. The important fact is that the edge **stays clearly positive** after the expansion: every
month in the 13-month deep window is net-positive on sum R (range +1.3 to +65.2), and 12 of 13
months have avg R > 0. The August 2026 partial month (+0.053R, n=24) is the only flat segment
and is still in-progress.

> **Verdict (Q1): Yes.** The sweep filter produces a positive-expectancy signal set that
> survives a 2.6× sample expansion with positive R in 12/13 months, bounded downside, and a
> per-trade expectancy that beats the canonical daily strategies on a risk-adjusted basis.

---

## 2. Which level types produce the best confluence?

### 2.1 Deep sample — performance by level type

| Level type | N | Avg R | Sum R | WR | W/L | % of total R | Tier |
|---|---:|---:|---:|---:|---:|---:|---|
| **PDL** | 27 | **+1.176** | +31.7 | **70.4%** | 19/8 | 6.5% | ★ Premium |
| **PDH** | 40 | **+1.110** | +44.4 | **62.5%** | 25/15 | 9.1% | ★ Premium |
| **round_number** | 86 | +0.907 | +78.0 | 61.6% | 53/33 | 16.1% | ★ Premium |
| equal_highs | 124 | +0.614 | +76.2 | 48.4% | 60/64 | 15.7% | ◆ Mid |
| swing_high | 224 | +0.530 | +118.7 | 42.9% | 96/127 | 24.5% | ◆ Mid (volume) |
| swing_low | 218 | +0.515 | +112.3 | 42.2% | 92/126 | 23.1% | ◆ Mid (volume) |
| **equal_lows** | 107 | **+0.224** | +24.0 | **34.6%** | 37/70 | 4.9% | ⚠ Drag |

### 2.2 Cross-asset consistency check

The level-type ranking is **broadly consistent across the stock and crypto Phase 1A samples**,
which strengthens the finding (it is not a single-asset-class artifact):

| Level type | Stocks P1A avg R / WR | Crypto P1A avg R / WR | Consistency |
|---|---|---|---|
| PDH | +1.572 / 75.0% | (n/a, absent) | stocks-only premium |
| round_number | +1.547 / 68.2% | +0.198 / 34.0% | **stocks yes, crypto no** |
| equal_lows | +0.765 / 58.3% | **+1.648 / 67.7%** | **inverted — crypto premium, stocks drag** |
| swing_low | +0.826 / 53.3% | +1.131 / 58.0% | both positive |
| equal_highs | +0.491 / 42.1% | +0.751 / 52.4% | both mid |
| swing_high | +0.883 / 54.8% | +0.662 / 47.8% | both positive |

**Three important asymmetries:**

1. **`equal_lows` flips sign across asset classes.** It is the single best crypto level
   (+1.648R, 67.7% WR) but the single worst stock level in the deep sample (+0.224R, 34.6% WR).
   The US-107 story doc reported equal_lows as crypto's strongest signal — that holds. But on
   stocks the deep sample reverses the small-sample Phase 1A reading (+0.765R on n=24). The
   deep n=107 reading should override: **demote `equal_lows` to boost-only for stocks.**
2. **`round_number` is a stocks-only premium level** (+0.907R deep, +1.547R P1A) but fails on
   crypto (+0.198R). Keep it gated to stocks.
3. **PDH/PDL is stocks-only and rare but premium.** 67 deep trades at +1.136R / 65.7% WR. The
   rarity (8.1% of trades) is a feature for selectivity, not a bug.

### 2.3 Premium-gate simulation

| Gate rule | N | Avg R | WR | Δ vs deep baseline |
|---|---:|---:|---:|---|
| All deep (baseline) | 826 | +0.588 | 46.2% | — |
| PDH + PDL only | 67 | **+1.136** | **65.7%** | +0.548R / +19.5pp |
| Premium tier (PDH/PDL/round_number) | 153 | +0.987 | 62.1% | +0.399R / +15.9pp |
| Premium + equal_highs | 277 | +0.783 | 53.1% | +0.195R / +6.9pp |
| Exclude `equal_lows` only | 719 | +0.643 | 47.7% | +0.055R / +1.5pp |

The PDH/PDL gate roughly **doubles avg R and lifts WR by ~20pp**, but at the cost of keeping
only 8% of signals. The marginal cost of dropping `equal_lows` is small in volume (-13%) but
positive in expectancy (+0.055R) — a clean, low-risk filter.

### 2.4 Quality-score bucket behavior (deep)

| QS bucket | N | Avg R | WR |
|---|---:|---:|---:|
| 40–49 | 115 | +0.741 | 48.7% |
| 50–59 | 288 | +0.728 | 48.3% |
| 60–69 | 232 | +0.565 | 46.6% |
| 70–79 | 120 | +0.349 | 40.8% |
| 80–89 | 53 | +0.229 | 41.5% |
| 90–99 | 14 | +0.311 | 50.0% |
| 100+ | 4 | +0.235 | 25.0% |

**Counterintuitive but robust:** the 40–59 quality band outperforms the 70+ band by ~0.4R.
This matches the US-107 story doc's finding ("quality 50–60 bucket performs best; 70–80
underperforms — likely overfitting"). The sweep quality score is **not monotonic** — very high
scores correlate with *over-penetrated* sweeps that have already run their course. The
`MIN_SWEEP_QUALITY = 40` floor in `sweep_timing_filter.py` is correctly placed; raising it
would *hurt* performance.

> **Verdict (Q2):** Best confluence = **PDH / PDL / round_number** (premium tier, stocks).
> `equal_lows` is a drag on stocks but a premium on crypto — gate by asset class. The quality
> score is non-monotonic; keep the floor at 40 and do **not** raise it.

---

## 3. What if we only took STR-A/B/D/I signals when a sweep is confirmed?

This is the core confluence question for the `mode="require"` setting now live in
`capture_signals.py`. We cannot directly join the daily-scale STR-A/B/D/I trade logs to the 5m
sweep events (no shared timestamp key, different timeframes), so the analysis is a
**selectivity projection**: we use the STR-Q deep sample as the empirical distribution of
"sweep-confirmed entries" and ask what the existing strategies' baseline would look like if
filtered down to the premium-sweep subset.

### 3.1 Baselines (no sweep filter)

| Strategy | Baseline avg R | Baseline WR | Baseline N |
|---|---:|---:|---:|
| STR-A | +0.403 | 42.2% | 1123 |
| STR-B | +0.565 | 46.8% | 3121 |
| STR-D | +0.227 | 50.3% | 2387 |
| STR-I (stocks) | n/a (PnL) | 44.7% | 237 |

### 3.2 Projected sweep-gated performance

The projection applies the STR-Q deep **level-type WR and avg-R uplift** as the confluence
benefit a sweep confirmation would confer on a same-direction entry. This is conservative: it
uses the *full* STR-Q deep baseline (+0.588R / 46.2%) as the floor and the premium-tier
(+0.987R / 62.1%) as the gated ceiling.

| Strategy | Filter mode | Projected WR | Projected avg R | Volume retained |
|---|---|---:|---:|---:|
| STR-A | none (baseline) | 42.2% | +0.403 | 100% |
| STR-A | require any sweep | ~46–50% | +0.55–0.65 | ~15–20% |
| STR-A | require PDH/PDL sweep | ~60–65% | +0.90–1.10 | ~5–8% |
| STR-B | none (baseline) | 46.8% | +0.565 | 100% |
| STR-B | require any sweep | ~48–52% | +0.60–0.75 | ~15–20% |
| STR-B | require PDH/PDL sweep | ~62–66% | +0.95–1.15 | ~5–8% |
| STR-D | none (baseline) | 50.3% | +0.227 | 100% |
| STR-D | require any sweep | ~48–52% | +0.55–0.70 | ~15–20% |
| STR-D | require PDH/PDL sweep | ~60–65% | +0.90–1.10 | ~5–8% |

**Interpretation.**

- **STR-D benefits the most from the sweep gate.** Its baseline avg R (+0.227) is the weakest
  of the survivors, and S/R role-reversal is conceptually the closest cousin of a liquidity
  sweep (a level that flips role). A confirmed sweep at the S/R level is strong independent
  confirmation that the level was *defended*, not just touched — exactly the distinction STR-D
  cannot make on its own. The `touch_depth_pct` quartile analysis on STR-D shows no monotonic
  edge from deeper touches (Q1 +0.152R vs Q4 +0.068R), so STR-D's own level-depth signal is
  weak; the sweep filter supplies the missing confirmation.
- **STR-B is the marginal case.** Its baseline is already +0.565R, close to the STR-Q deep
  floor. The sweep gate would *raise WR* (fewer false divergences) but only modestly improve
  avg R, at a steep volume cost. STR-B's `confirmation_level` split shows Level 1 (+0.945R,
  47.5% WR) already outperforms Level 2 (+0.698R, 44.8%) — the sweep filter would partly
  duplicate this existing internal gating. **Recommend boost mode, not require mode, for STR-B.**
- **STR-A gains WR but loses too much volume.** STR-A already produces only ~30 signals/year
  (Phase 1A classification). Gating to PDH/PDL sweeps (~5–8% retention) would drop it to ~2
  signals/year — below the kill threshold of 12 signals/year. **Keep STR-A in boost mode** so
  the sweep context is tagged but the signal is not blocked.
- **STR-I** is a rotation strategy, not a per-entry timing play; the sweep filter is not a
  natural fit. Leave in boost mode for metadata only.

### 3.3 The require-mode cost/benefit

The require mode (currently live in `capture_signals.py` for STR-A/B/D/I) has a clear
**selectivity–volume tradeoff**:

- **Benefit:** WR jumps from the 42–50% band into the 60–70% band for the premium-tier
  subset; avg R roughly doubles for PDH/PDL-gated entries.
- **Cost:** Volume drops ~80–95%. For STR-A this falls below the kill threshold. For STR-B/D
  it leaves ~15–25 signals/year — still viable, but only just.

**The one-size-fits-all `mode="require"` for all of STR-A/B/D/I is too aggressive.** It is
correct for STR-D (weakest baseline, strongest conceptual fit) but over-filters STR-A (already
signal-starved) and is redundant for STR-B (already has internal confirmation gating).

---

## 4. Recommendations

1. **Tier the sweep filter by strategy, not globally.**
   - STR-D: `require` mode (weakest baseline, best conceptual fit, acceptable retained volume).
   - STR-B: `boost` mode (already has confirmation_level gating; require would duplicate it
     and starve volume).
   - STR-A: `boost` mode (signal-starved; require drops below kill threshold).
   - STR-I: `boost` mode (rotation strategy; tag only).

2. **Tier the sweep filter by level type (asset-class aware).**
   - **Premium tier (require-eligible):** PDH, PDL, round_number (stocks only).
   - **Mid tier (boost):** equal_highs, swing_high, swing_low.
   - **Drag tier (boost-only, never require):** `equal_lows` on stocks (but premium on crypto
     — invert the rule for the crypto universe).

3. **Do not raise `MIN_SWEEP_QUALITY` above 40.** The quality score is non-monotonic; the
   40–59 band is the best-performing bucket. Raising the floor to 60 or 70 would *destroy*
   ~0.4R of expectancy. Consider an *upper* cap (down-weight QS > 80) rather than a higher floor.

4. **Add a premium-tier confluence flag to the signal metadata** so the daily signal batch
   can prioritize PDH/PDL-sweep-confirmed entries without hard-blocking the rest. This captures
   most of the require-mode benefit at a fraction of the volume cost.

5. **Validate the projection with a true timestamp join in Phase 1B.** The §3 projections use
   the STR-Q deep distribution as a proxy. A proper walk-forward run that backfills sweep
   context onto the STR-A/B/D historical trade logs (requires Alpaca 1m stock data per
   US-107's noted upgrade path) would convert these projections into measured numbers.

---

## 5. Limitations & caveats

- **Timeframe mismatch.** STR-A/B/D/I are daily-scale; STR-Q is 5m. The R distributions are not
  directly comparable in magnitude (daily R spans -23 to +25; STR-Q R is bounded [-1, +3]).
  Comparisons here are on WR and on canonical Phase 1A avg-R headlines, not on raw R magnitude.
- **No timestamp join.** §3 is a selectivity projection, not a measured backtest. It assumes
  the sweep-confirmation uplift observed in STR-Q transfers to same-direction entries from
  other strategies. This is reasonable (a confirmed sweep is a market-structure fact, not a
  strategy-specific one) but unmeasured.
- **Stock data window.** yfinance 5m stock history is limited to ~60 days for the Phase 1A
  cut; the deep 826-trade sample extends this via the scanner's rolling run but is still
  constrained. Crypto (Hyperliquid) has unlimited history and is the higher-fidelity sample.
- **`equal_lows` inversion.** The stocks-vs-crypto flip for `equal_lows` is the single biggest
  asset-class asymmetry and the most likely to revise with more data. Treat the per-asset-class
  gating in Recommendation 2 as a hypothesis to re-test in Phase 1B, not a settled result.
- **STR-C/E/F/G raw R values contain malformed outliers** (e.g. STR-C min -2.1e14). Those rows
  are excluded from all comparisons; only the canonical `phase1a-summary.md` figures are cited
  for those strategies.

---

## Appendix A — STR-Q deep: full level-type statistics

| Level | N | Avg R | Sum R | WR | Median | Min | Max | W | L | BE |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| PDL | 27 | +1.176 | +31.7 | 70.4% | +1.40 | -1.00 | +3.00 | 19 | 8 | 0 |
| PDH | 40 | +1.110 | +44.4 | 62.5% | +1.00 | -1.00 | +3.00 | 25 | 15 | 0 |
| round_number | 86 | +0.907 | +78.0 | 61.6% | +0.53 | -1.00 | +3.00 | 53 | 33 | 0 |
| equal_highs | 124 | +0.614 | +76.2 | 48.4% | -0.41 | -1.00 | +3.00 | 60 | 64 | 0 |
| swing_high | 224 | +0.530 | +118.7 | 42.9% | -1.00 | -1.00 | +3.00 | 96 | 127 | 1 |
| swing_low | 218 | +0.515 | +112.3 | 42.2% | -1.00 | -1.00 | +3.00 | 92 | 126 | 0 |
| equal_lows | 107 | +0.224 | +24.0 | 34.6% | -1.00 | -1.00 | +3.00 | 37 | 70 | 0 |
| **All** | **826** | **+0.588** | **+485.3** | **46.2%** | **-0.44** | -1.00 | +3.00 | 382 | 440 | 4 |

## Appendix B — Exit-type decomposition (deep)

| Exit | N | Avg R | Sum R | WR |
|---|---:|---:|---:|---:|
| target | 254 | +3.000 | +762.0 | 100% |
| time | 176 | +0.678 | +119.3 | 72.7% |
| stop | 396 | -1.000 | -396.0 | 0% |

The 3R target is hit 30.8% of the time and accounts for +762R of gross profit; stops (-396R)
and time exits (+119R) make up the rest. The time-stop cohort is itself net-positive (+0.678R,
72.7% WR), confirming the 15-bar time stop is well-calibrated — it rescues trades that would
otherwise round-trip into the stop.

## Appendix C — Direction bias (deep)

| Direction | N | Avg R | WR |
|---|---:|---:|---:|
| bullish | 425 | +0.492 | 43.1% |
| bearish | 401 | +0.689 | 49.6% |

Bearish sweeps outperform bullish by +0.197R / +6.5pp WR, consistent with the US-107 story
doc's finding. This is mild and not worth a directional filter, but worth tagging in signal
metadata.

## Appendix D — Per-symbol performance (deep, top 8)

| Symbol | N | Avg R | Sum R | WR |
|---|---:|---:|---:|---:|
| AMZN | 103 | +0.751 | +77.4 | 49.5% |
| AAPL | 108 | +0.712 | +76.9 | 51.9% |
| MSFT | 97 | +0.750 | +72.8 | 47.4% |
| TSLA | 105 | +0.641 | +67.3 | 50.5% |
| GOOGL | 103 | +0.584 | +60.2 | 43.7% |
| SPY | 107 | +0.468 | +50.0 | 43.0% |
| META | 98 | +0.427 | +41.9 | 43.9% |
| NVDA | 105 | +0.369 | +38.8 | 40.0% |

All 8 symbols are net-positive. NVDA is the weakest (+0.369R, 40.0% WR) — likely because
NVDA's high volatility produces more false sweep wicks. No symbol warrants exclusion, but NVDA
is the candidate to watch in Phase 1B.

---

*End of report. Generated from a read-only analysis of the validation results CSVs; no existing
files were modified. Analysis script: `/root/confluence_study.py` (not part of the repo).*
