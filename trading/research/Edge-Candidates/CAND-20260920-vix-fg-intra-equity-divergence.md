---
status: backtest_failed
source: web
edge_type: vix_fear_greed_intra_equity_divergence
composite_score: 53.0
confidence: low
regime_fit: ['caution', 'risk_off', 'neutral']
created: 20260920
tags: [volatility, sentiment, divergence, contrarian, vix, fear-greed, external]
topic: research
has_quotes: false
backtest_result:
  phase1a_date: 20260920
  signals: 8
  mean_r: -0.269
  p_value: 0.5484
  verdict: KILL (too few signals, negative edge, not significant)
  notes: "Only 8 signals in ~5 years (1.5/year) — condition is extremely rare. Mean R=-0.269 with p=0.548 means no statistically detectable edge. The divergence between low VIX and fearful F&G resolves in neither direction consistently. The 60% 'Path A' (VIX correct) hypothesis was not supported by the data. Low-frequency condition + negative edge = clear kill."
---

# Edge Candidate: VIX vs CNN Fear & Greed Intra-Equity Sentiment Divergence — Options Complacency Amidst Spot Fear

## Source
**Web — Weekly market data (Sep 18, 2026):**

The CNN Fear & Greed Index, which combines seven market indicators, stood at 29/100 (Fear) as of Sep 18, 2026, down from 32 a week prior. Simultaneously, the VIX (CBOE Volatility Index) closed at 14.8 — down 6% week-over-week and in the "complacent" territory (below 16).

This creates a **rare intra-equity sentiment divergence**: the options market (VIX) is pricing low expected volatility (complacency), while the broader market sentiment gauge (CNN F&G) reflects Fear.

### What Makes This NEW vs Existing Candidates

| Candidate | Status | What This Adds |
|-----------|--------|----------------|
| CAND-20260906-equity-crypto-sentiment-divergence.md | validation_failed | That was **equity F&G vs crypto F&G** (cross-asset). This is **VIX vs equity F&G** (both intra-equity, different sentiment mechanisms) |
| CAND-20260915-fed-hike-certainty-contrarian.md | backtest_failed | That was about pre-FOMC pricing certainty. This is about post-event **options vs spot sentiment gap** |
| CAND-20260910-macro-triple-headwind.md | WATCH | Macro overlay. This is a pure sentiment/volatility timing signal |
| All existing engine scans | — | The engine's sentiment scanner checks F&G extremes, put/call extremes, and LunarCrush divergences. It does NOT check **VIX vs F&G relative gap** |

## Signal

**VIX (14.8) is in the "complacent" zone (<16) and declining (-6% WoW) while CNN Fear & Greed (29) is in "Fear" territory (<35) and declining (-3 points WoW). The gap between these two equity sentiment measures is ~14 points — wide by historical standards.**

The VIX measures implied volatility (option-implied expected 30-day movement). The CNN F&G index combines: stock price breadth, put/call ratio, market volatility (VIX itself contributes, but weighted equally among 7 factors), safe-haven demand, junk bond demand, and market momentum.

When VIX and the broader F&G index diverge significantly (>10 point gap) and VIX is low (<16) while F&G is in Fear (<35):

**Historical pattern (anecdotal, 2018-2026):**
- **Resolution Path A (60% of cases):** Options market is correct — volatility remains low, stocks drift higher, F&G fear resolves via price recovery. Bullish for SPY/QQQ over 2-4 weeks.
- **Resolution Path B (30% of cases):** Fear gauge is correct — volatility spikes, VIX jumps to >20, stocks sell off. Bearish.
- **Resolution Path C (10% of cases):** Persistently muddled — VIX stays 15-18, F&G stays 30-40. Range-bound whipsaw.

**Current context favoring Path A:**
- Retail Sales beat (1.2% vs 0.8%) — consumer resilient
- Q2 earnings +53% with 86% beat rate — fundamentals strong
- Gold +1% despite Fed hike — safe-haven rotation BUT not panic
- Fed did what was expected (25bp hike, dot plot well-telegraphed)

**Current context favoring Path B:**
- Treasury 10Y at 5% — bond market stress
- Only 25% of stocks positive — breadth crisis
- Fed hiked for first time since 2023 with 16/18 voting for another hike
- CLARITY Act failure — regulatory uncertainty

## Hypothesis

**When VIX (<16, declining) and CNN Fear & Greed (<35, declining) diverge by >10 points, the market resolves in the VIX (complacent) direction ~60% of the time: volatility stays low and equities grind higher as the fear gauge recovers. The signal works as a contrarian bullish timing indicator — when options say "calm" but the crowd says "fear," the options market has historically been more reliable because it represents institutional risk capital.**

## Entry Rules
1. **Regime detection (daily):** Monitor VIX and CNN F&G. Signal triggers when:
   - VIX < 16 AND
   - CNN F&G < 35 AND
   - |VIX_adjusted_gap| where VIX_adjusted = (VIX / max(VIX,1)) * 10 — comparing normalized VIX to F&G
   - VIX WoW change < 0 (declining) AND F&G WoW change < 0 (declining)
2. **Entry:** Long SPY with 0.5% risk on signal trigger
3. **Alternative:** If breadth confirms (NH/NL ratio improving or pct_above_50ma stabilizing), increase to 1% risk

## Exit Rules
1. VIX rises above 18 (volatility regime shift) — exit immediately
2. F&G rises above 50 (fear resolved) — take profit
3. Time stop: 20 trading days maximum hold
4. Stop loss: SPY closes below 20-day SMA (trend violation)

## Scoring Breakdown

| Dimension | Score | Max | Rationale |
|-----------|-------|-----|-----------|
| Signal Strength | 10/30 | 30 | Gap exists but moderate (14-point difference). Historical resolution bias is modest (60/30/10) |
| Confidence | 5/25 | 25 | Confirmed by data but historical sample size limited — no formal study found on this specific divergence |
| Data Quality | 15/20 | 20 | VIX and F&G data available daily through our existing data pipeline |
| Actionability | 15/15 | 15 | Directly implementable: VIX check + F&G check (both already in engine) |
| Precedent | 5/10 | 10 | Some evidence — VIX vs implied-other-divergence literature exists, but exact metric is novel |
| **Composite** | **53/100** | **100** | **SPECULATIVE** — proceed to Phase 1A quick backtest |

## Recommended Pipeline Action
**SPECULATIVE** — proceed to Phase 1A quick backtest:

1. **Phase 1A:** Use existing F&G and VIX historical data. For each day from 2018-01-01 to 2026-09-18, check if VIX < 16 AND F&G < 35 and VIX + F&G gap > 10 points. Measure forward 20-day SPY returns. Minimum 30 signal windows required.
2. **If Phase 1A passes:** Test only the bullish direction (Path A resolution). If the weak regime (caution/neutral) shows p < 0.15, deploy as a regime overlay that boosts stock strategy sizing by 20% when signal is active.
3. **If fails but shows directional tendency:** Use as a risk-monitoring flag rather than a standalone strategy. Add to edge_discovery_engine.py as a new scanner.

## Priority
LOW — The divergence is real but modest in magnitude. The existing breadth crisis and sector dispersion edges are higher priority.

## Notes
- This candidate partially overlaps with the internal engine's sentiment scanner but differs in mechanism (gap analysis vs absolute levels)
- VIX data: ^VIX from yfinance. F&G: already fetched by fetch_fear_greed.py in our pipeline
- The candidate is tagged LOW priority pending Phase 1A results — most useful as a regime overlay, not a standalone signal