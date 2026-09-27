---
status: backtest_failed
source: web
edge_type: overnight_drift_return_factor
composite_score: 57.0
confidence: medium
regime_fit: ['neutral', 'risk_on', 'complacent']
created: 20260820
processed: 20260820
topic: research
has_quotes: false
tags: [factor, overnight, intraday-decomposition, cross-sectional, academic, external]
---
# Edge Candidate: Overnight (Close-to-Open) Drift as a Cross-Sectional Factor

## Pipeline Result: BACKTEST FAILED (2026-08-20)

**Scanner:** `scanner_overnight_drift.py` (STR-OVNIGHT-DRIFT)
**Phase 1A Results:**
- Total signals: 17,844 (2511.6/year — very high frequency, monthly rebalance across 529 stocks)
- Mean R: -0.020 (negative)
- Median R: -1.000 (median trade hits stop loss)
- Win rate: 31.7%
- p-value: 0.1103 (not significant)
- t-stat: -1.597
- Sub-periods positive: 2/3 (period1_bull, period3_current positive but overall negative)
- Classification: ❌ KILL (avg_r < KILL_AVG_R threshold of 0.2)

**Analysis:**
The overnight drift factor does not produce a positive edge as a standalone
long-short quintile strategy with ATR stops. The negative mean R is consistent
with the candidate's own caveat: "the capture problem is real (overnight gaps
are hard to trade at the close)." The factor may still be valuable as an
explanatory overlay (explaining why other factors' returns concentrate in one
session) but is not a standalone tradable edge with this implementation.

**What would change my view:** Testing as a pure factor-mimicking portfolio
(monthly rebalance, no ATR stop, equal-weight long-short) to avoid the
stop-incompatibility failure mode that also killed the skewness candidate.
The stop loss is likely the wrong exit mechanism for a factor strategy.
# Edge Candidate: Overnight (Close-to-Open) Drift as a Cross-Sectional Factor

## Source
Web / academic & practitioner research (2025–2026) —
- **ScienceDirect, "Turning cross index overnight returns into feasible forecasts" (Jul 18 2026):** cross-index overnight returns (diffrate) aggregate market/sector conditions and offer stable, forecastable signals vs. noisy individual-stock overnight moves.
- **Wealthsimple (Jul 13 2026):** "overnight drift" anomaly getting fresh mainstream attention — decades-old, still vexing researchers.
- **Elm Wealth, "Still Working the Night Shift" (Mar 2025):** the overnight stock-return anomaly persists; speculative/meme assets soar when markets are closed.
- **LinkedIn / Cacciatore (Sep 2025):** "overnight trading dominates equity returns" — drift is real but access is unequal (delta-one desks, hedge funds capture it; retail cannot easily).
- **QuantPedia "Lunch Effect" / Cooper-Cliff-Gulen "Return Differences between Trading and Non-Trading Hours":** established precedent that the overnight (non-trading) session carries a distinct, persistent return premium separable from intraday returns.

## Signal
Decompose each asset's daily return into **overnight** (open_t / close_{t-1} − 1) and **intraday** (close_t / open_t − 1) components. Rank the cross-section on a rolling cumulative overnight return (e.g., 20-day / 60-day overnight drift). Assets with the strongest *positive overnight drift* have historically carried a premium (institutional/overnight flow, gap behavior, close-auction effects); assets with negative overnight drift underperform. A long-short on overnight-drift rank is a candidate standalone factor, and — like skewness — it is a **decomposition axis none of our 10 screened factors capture** (RSI14, REV1, LOWVOL, ATR_PCT, BB_WIDTH, PRICEMOM, VOL_ROC, ADX_TREND, LIQUID, MOM12_1 all use close-to-close or intraday-high-low, never the open/close gap specifically).

## Hypothesis
The overnight session embeds information that the intraday session does not (after-hours news, international flow, close-to-open positioning). Sorting the cross-section on rolling overnight drift and going **long high-overnight-drift / short low-overnight-drift** captures a premium distinct from momentum, reversal, and volatility factors. If true, it is an orthogonal factor axis (like the staged skewness candidate) and may also help explain *why* some existing factors (e.g., the all-negative-significant stock factors in the 08-09 screener) behave as they do — possibly their returns are concentrated in one session.

## Entry Rules
- **Strategy A (Long-Short Overnight Drift):** Weekly rebalance. For each asset compute 60-day cumulative overnight return = Π(open_t / close_{t-1}) − 1. Rank cross-section; long top quintile, short bottom quintile. Equal or inverse-vol weight. Hold 1 week.
- **Strategy B (Overnight-Drift Tilt Overlay):** From any existing long-only buy list, tilt toward names in the top half of overnight-drift rank (overlay on STR-I/STR-R trend strategies).
- **Strategy C (Crypto Overnight):** Crypto trades 24/7 so "overnight" is ill-defined — instead use a *session* decomposition: define the US-equity-session window (14:30–21:00 UTC) vs. the off-session window for the 35 Hyperliquid assets, and rank on off-session drift. This tests whether the same flow-decomposition logic applies to crypto.

## Exit Rules
- Weekly rebalance; exit all at next rebalance. No fundamental stop (pure factor). Optional vol-target overlay.
- Overlay variant: exit when underlying strategy exits OR asset drops to bottom half of overnight-drift rank.

## Score Breakdown
- Composite: 57.0
- Signal Strength: 11 (fresh 2026 academic + practitioner attention; genuinely new decomposition axis not in screener)
- Confidence: medium (15) — well-established anomaly in the literature, but the *capture* problem is real (overnight gaps are hard to trade at the close; this is the main risk to live tradability even if the factor tests significant)
- Data Quality: 15 (daily OHLC from yfinance 529 stocks — open and close are both provided, so overnight return is a direct one-liner `df['Open']/df['Close'].shift(1)-1`; no external feed)
- Actionable: 10 (long-short is straightforward in backtest; live capture has execution-friction risk at the close auction)
- Precedent: 6 (some_evidence — overnight anomaly is documented but its persistence net of frictions is debated; the "access unequal" critique lowers conviction)

## Regime Fit
['neutral', 'risk_on', 'complacent'] — overnight drift is most pronounced when speculative/flow-driven names gap (complacent/risk-on regimes). Suppress in 'risk_off' (overnight gaps become gap-down risk, factor inverts).

## Testability
✅ **Fully testable with free data.** Overnight return is directly computable from yfinance OHLC. Add an `OVNIGHT_DRIFT` factor to the factor screener alongside the staged `SKEW` factor, run the standard significance test (t-stat, p-value) over the 1806-day stock and 2159-day crypto histories, and check orthogonality to the 10 existing factors + skewness. Crypto session-decomposition (Strategy C) needs UTC-timestamped OHLC which Hyperliquid provides.

**Overlap with engine:** Engine factor screener tests 10 factors, NONE decompose by session. The staged skewness candidate (0818, backtest_failed at weekly rebalance) is the closest sibling — both are "new orthogonal factor" candidates. Overnight drift is a *different* decomposition (temporal vs. distributional). Worth testing in the same factor-screener extension pass as skewness to share the engineering cost.

## Recommended Pipeline Action
**PROMISING →** Add `OVNIGHT_DRIFT` (60-day cumulative overnight return, cross-sectional rank) to the factor screener in the same extension pass as `SKEW`. Test significance on both universes. Two outcomes of interest: (1) standalone t-stat |≥2| → walk-forward long-short backtest with a realistic close-auction friction assumption (5–10bp); (2) if it explains part of the negative-return significant factors (i.e., their returns are intraday-negative/overnight-positive), document as a confound/orthogonal axis. Medium priority — bundle with the skewness re-test to amortize the screener-extension work. Note the skewness weekly-rebalance backtest FAILED; design the overnight backtest with a *monthly* rebalance and no ATR stop (pure factor-mimicking portfolio) to avoid the same stop-incompatibility failure mode.
