---
status: rejected
source: web
edge_type: meta_factor_crowding_decay
rejection_reason: Not a standalone scanner — this is a meta-overlay on the existing factor screener. Requires modifying the factor weighting system, not creating a new per-ticker signal scanner. Defer to factor-screener improvement task.
composite_score: 49.0
confidence: low
regime_fit: ['all']
created: 20260818
topic: research
has_quotes: false
tags: [meta-signal, factor-crowding, alpha-decay, external]
---
# Edge Candidate: Factor Crowding / Post-Publication Alpha Decay (Meta-Overlay)

## Source
Web / academic research —
- "When Everyone Trades the Same Factor Playbook" / "Anomaly-Driven Demand" (Posselt & Kjær, March 2026, via Alpha Architect): decomposes how investor demand erodes anomaly returns; millions trading the same published factor compress the edge.
- "Crowded spaces and anomalies" (ScienceDirect, J. Banking & Finance 2025): documents **decay in anomaly alpha after publication date** (post-pub dummy is significant); crowded factor quintiles crash harder.
- "Your Research Agent Is an Undisclosed Factor Exposure" (Jonathan Kinlay, Aug 15 2026): argues that LLM-driven research agents accelerate crowding — "eight analysts independently building books out of the published anomaly literature would be more crowded."
- "LLMs and the Shortening Shelf Life of Copyable Alpha" (IBKR Quant News, Apr 28 2026): alpha decays faster after information release as LLMs disseminate/replicate signals quickly.
- Counterpoint (Acadian Asset, Apr 2026): "Misplaced Anxiety" — quant crowding concern is overstated; 2026 environment differs from 2007, factor performance muted, crowding measures noisy. → the edge is *conditional*, not unconditional.

## Signal
- Published anomalies **lose ~30-60% of their out-of-sample alpha within 3-5 years of publication** (per the ScienceDirect decay study). The decay is steepest for the most-cited, easiest-to-replicate factors.
- LLM-driven research is **shortening the shelf life** of copyable alpha: signals that once took months to diffuse now crowd in weeks.
- Our own factor screener (research-2026-08-09) is consistent with decay: of 10 stock factors, 5 are SIGNIFICANT but **all with NEGATIVE annualized returns** (RSI14 -18%, LOWVOL -21%, ATR_PCT -21%, REV1 -17%, BB_WIDTH -16.6%) — possible evidence that these well-known factors are crowded/arbitraged in the current universe. Momentum (MOM12_1, PRICEMOM) is now NOT significant — classic decay signal.

## Hypothesis
A meta-signal can be built from **crowding/decay proxies** to (a) tilt the factor portfolio *away* from crowded, recently-popularized factors and *toward* under-crowded or freshly-discovered ones, and (b) dynamically de-weight any factor whose live rolling performance has decayed below its in-sample benchmark.

This is not a standalone price signal — it is a **meta-overlay** on the existing factor-screener / strategy-selector that adjusts factor weights by a crowding penalty.

## Entry Rules
- **Decay-weight overlay:** For each factor in the screener, compute a "time-since-popularization" penalty (factors published >5 yrs ago and heavily cited get a 0.5-0.7 weight multiplier; novel/under-cited factors keep 1.0). Combine with a live-performance check: if a factor's rolling 1-yr live Sharpe has fallen below 50% of its in-sample Sharpe, halve its allocation.
- **Crowding proxy (price-based):** Compute the **average pairwise correlation of the factor's long-leg constituents** — when constituent correlation spikes (everyone holding the same names), raise the crowding penalty. This is computable from our price data without 13F holdings.
- **Anti-crowding tilt:** When the aggregate crowding index is elevated, shift the portfolio toward factors currently showing *low* constituent correlation and *fresh* (recently discovered) signals.

## Exit Rules
- Re-evaluate the crowding/decay weights monthly. Restore a factor's full allocation when its constituent correlation normalizes AND its live Sharpe recovers above 70% of in-sample.
- Hard-suppress any factor whose live rolling Sharpe has been negative for 12 consecutive months (decay to zero).

## Score Breakdown
- Composite: 49.0 (staged under the "strong external validation" qualifier — 4+ 2026 papers + our own screener data corroborate)
- Signal Strength: 9.0 (decay is real and documented; but magnitude/timing is imprecise)
- Confidence: low (8 pts) — meta-overlay, crowding proxies are noisy, the Acadian counterpoint shows the signal is conditional not clean
- Data Quality: 8 (price-based crowding proxies computable from yfinance/Hyperliquid; true holdings-based crowding needs 13F, unavailable free)
- Actionable: 12 (can be implemented as a weight-overlay on the existing factor screener with modest code)
- Precedent: 12 (well_documented — post-publication decay is one of the most replicated findings in the anomaly literature)

## Regime Fit
['all'] — meta-overlay applies across regimes, though crowding-driven crashes cluster in 'unified' correlation regimes (de-risk factor bets when correlations spike).

## Testability
⚠️ **Partially testable with free data.**
- ✅ Price-based crowding proxy (constituent correlation, factor-portfolio dispersion) — computable from our existing OHLC data.
- ✅ Live-performance decay check — directly from the screener's own rolling output.
- ❌ Holdings-based crowding (13F short-interest-by-factor, fund flow into factor ETFs) — not freely available at the granularity needed.
- The overlay can be backtested by applying decay-weights to the historical factor screener output and comparing net performance vs. equal-weighted factors.

**Overlap with engine:** Engine does NOT currently apply a crowding/decay adjustment to its factor screener or strategy selector. This is a new meta-layer. It directly explains the all-negative-significant-factor result in the latest screener run (a symptom the engine flags but does not interpret).

## Recommended Pipeline Action
**SPECULATIVE →** First, confirm the decay hypothesis on our own data: for each of the 5 SIGNIFICANT-but-negative stock factors, plot rolling 1-yr Sharpe over the 1806-day history — if the early sample was positive and it decayed negative, that's direct in-house evidence of crowding/decay. If confirmed, prototype the price-based crowding proxy (constituent correlation) as a factor-weight overlay and run a backtest comparing decay-weighted vs. equal-weighted factor portfolios. Defer any live deployment until the overlay shows out-of-sample improvement. Medium-priority research item; not a standalone tradable edge but a portfolio-construction improvement.
