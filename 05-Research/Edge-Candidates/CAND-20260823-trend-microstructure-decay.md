---
status: staged
source: web
edge_type: trend_microstructure_decay
composite_score: 61.0
confidence: medium
regime_fit: ['risk_on', 'neutral', 'diversified']
created: 20260823
topic: research
has_quotes: true
tags: [academic, trend-following, microstructure, alpha-decay, strategy-selection]
---

# Edge Candidate: Trend-Following Microstructure Decay

## Source
Academic paper — **"Is Trend Still Your Friend?: A Microstructural Account of the Demise of Short-Term Trend-Following"** (arXiv:2607.01550, Jul 2, 2026):
- Authors show that trend-following strategies are NOT merely harvesting a pre-existing anomaly. Instead, **trend signals themselves trigger directional trades whose market impact erodes the edge** — the aggressive directional flow, mediated by market impact, systematically compresses the very price moves the strategy is trying to capture.
- Key finding: The alpha of short-term trend (1-20 day) has declined to near-zero or negative post-2015 in liquid US equities. Longer-duration trend (60-250 days) still retains positive expected returns because the signal-trading feedback loop is slower.
- **Harbourfront Quant (Aug 2, 2026):** Popularized summary — "Explaining the Decline of Trend-Following CTAs" confirming the decay in short-term trend strategies.
- **Complementary finding from "Crowded spaces and anomalies" (J. Banking & Finance, 2025/2026):** Post-publication alpha decay is strongest for the most easily-replicated anomalies — trend is the textbook example.

## Signal
A **duration-dependent regime filter for trend-following strategies**: short-term trend strategies (1-20 day lookback) should be suppressed or risk-reduced, while long-duration trend strategies (60+ day lookback) retain viability. The signal is not a price trigger — it's a **strategy-selection directive**:
- **Suppress:** Trend-following strategies with lookback < 20 days (STR-I adaptive trend short-duration variant, STR-R Williams Alligator short-duration signals, STR-V triangle breakout on short timeframes)
- **Boost/Retain:** Long-duration trend strategies (60-250 day lookback) — STR-AJ Intermarket Rotation, STR-I Adaptive Trend on weekly timeframe, 4-Week Rule (STR-AE) if using monthly lookback
- **Watch:** Medium-duration trend (20-60 days) — monitor for performance decay

## Hypothesis
Short-term trend-following strategies in US equities have structurally decayed due to (a) the signal's own microstructure impact compressing price moves, (b) crowding from CTAs and systematic funds all trading the same signals, and (c) LLM-driven research accelerating strategy replication. The expected future alpha of any sub-20-day trend strategy is ≤ 0 in liquid markets. This edge provides a **duration-gate**: only allow trend-following strategies with lookback ≥ 60 days to run at full risk; reduce or suppress short-duration trend strategies regardless of regime.

## Entry Rules
- **Strategy-level gate (apply at pipeline deployment):** When evaluating any new or existing trend-following strategy:
  1. Classify the strategy's primary signal lookback duration (short: <20d, medium: 20-60d, long: >60d)
  2. If short-duration → auto-set risk_multiplier to 0.0 (suppress) unless the strategy has a demonstrated OOS Sharpe > 0.5 in the most recent 2 years of walk-forward
  3. If medium-duration → set risk_multiplier to 0.5 (reduce) unless OOS Sharpe > 0.3
  4. If long-duration → run at full risk (1.0x) with standard regime adjustments
- **Existing strategy audit:** Review all LIVE trend-following strategies (STR-I, STR-R, STR-V, STR-W, STR-X, STR-Y, STR-AD, STR-AE) and apply the duration-gate. Short-duration variants get 0.0 risk.

## Exit Rules
- Re-evaluate annually. If the academic literature shows a reversal in the microstructure decay pattern (unlikely), the gate can be lifted.
- Any strategy that passes the gate can have its risk_multiplier normalized.

## Score Breakdown
- Composite: 61.0
- Signal Strength: 18.0 (high-quality academic paper with robust methodology; multiple corroborating sources — Harbourfront, JBF crowding paper; directly observable in CTA performance data)
- Confidence: medium (15) — the paper is peer-reviewed quality (arXiv, July 2026); the decline in CTA/short-term trend returns is well-documented; medium because the effect is strongest in US equities and may not generalize to crypto
- Data Quality: 10 (the paper is freely available on arXiv; backtesting our own strategies requires only our existing walk-forward results — no new data feeds needed)
- Actionable: 12 (directly implementable as a strategy-level gate with zero new data dependencies; no new scanner or backtest needed — it's a filter on existing strategy performance)
- Precedent: 6 (some_evidence — the "trend is decayed" theme is recent; similar arguments exist for other factors but the microstructure-specific mechanism is novel/2026)

## Regime Fit
['risk_on', 'neutral', 'diversified'] — This edge is a structural/strategy-selection directive, not a regime-dependent signal. However, in risk_off regimes, trend strategies are already suppressed by the regime selector, so the edge's marginal impact is highest in risk_on/neutral/diversified where trend strategies would otherwise run at full allocation.

## Testability
✅ **Fully testable with existing data.** No new data feeds, scanners, or backtests needed:
1. For each LIVE trend-following strategy, extract its lookback duration from the strategy config
2. Compare OOS performance (walk-forward Sharpe, mean R) for short vs. medium vs. long-duration strategies
3. If short-duration strategies show declining OOS performance over the most recent 2-year window (2024-2026), the decay hypothesis is confirmed in our universe
4. Apply the duration-gate as a risk_multiplier and measure the portfolio-level impact

**Overlap with engine:** The factor-crowding-decay candidate (CAND-20260818) is a meta-overlay for general factor crowding. This edge is specifically about **trend duration** and the microstructure mechanism — it provides a concrete, immediately-applicable filter (suppress sub-20d trend), not a general crowding proxy. Complementary to the crowding decay candidate but distinct in scope and actionability.

## Recommended Pipeline Action
**PROMISING →** This is a high-leverage, low-cost edge to validate:
1. Run an audit of all LIVE trend-following strategies: classify by lookback duration
2. Extract OOS walk-forward performance for the most recent 2-year window
3. If short-duration trend OOS Sharpe is near-zero or negative → apply the duration-gate immediately (risk 0.0 for short-duration, 0.5 for medium)
4. This is NOT a scanner — it's a strategy-level risk_multiplier gate that the regime selector can incorporate
5. Priority: HIGH — directly improves the LIVE strategy portfolio risk-adjusted returns without requiring new data or backtests. The academic signal is strong and actionable today.