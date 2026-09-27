# EDGE DISCOVERY — 2026-09-22
# HermesForge External Edge Discovery Agent — Phase 3 Extraction
# Non-X sources: strategy specs, entry/exit rules, reported metrics

---

## Candidate 1: 5 Swing Trading Strategies (TradeZella, 2026)
**URL:** https://www.tradezella.com/blog/swing-trading-strategies
**Source:** TradeZella Blog / Education

### Strategy 1A: Mean Reversion to 20 EMA
- **Instruments:** US equities in clear weekly uptrend
- **Timeframe:** Daily chart
- **Entry:** Pullback touches 20 EMA with support confirmation
- **Exit / Take Profit:** First target at most recent swing high; trail stop to breakeven after
- **Stop Loss:** Price closes below 20 EMA for two consecutive days
- **Reported Stats:**
  - Win rate: 55-65% in trending markets
  - Best in: trending; fails in choppy/sideways
  - Expectancy: needs 30-40 trades to measure

### Strategy 1B: Breakout From Multi-Week Consolidation
- **Instruments:** US equities with sector rotation
- **Timeframe:** Daily
- **Entry:** After 15+ trading days consolidation (range ≤8-10%), breakout candle closes above range on volume ≥50% >20d avg, sector ETF in uptrend
- **Exit / Take Profit:** Measured move = height of range projected above breakout (minimum 2:1 R:R)
- **Stop Loss:** Below bottom of consolidation range; exit if closes back inside range within 3 days
- **Reported Stats:** Needs 2:1 R:R minimum; best in trending markets with sector rotation

### Strategy 1C: Fibonacci Retracement Entry
- **Instruments:** Stocks with strong momentum (up 15-30% in 4-8 weeks)
- **Timeframe:** Daily / weekly
- **Entry:** Pullback to 50% or 61.8% Fib level with confluence (support zone, RSI 45-55, reversal candle)
- **Exit / Take Profit:** Prior swing high (T1); 127% or 161.8% Fib extension (T2, often 3:1 to 5:1 R)
- **Stop Loss:** Below 61.8% (if entering at 50%); below 78.6% (if entering at 61.8%); exit if breaks 78.6%
- **Reported Stats:** Win rate 45-55%, but larger avg winners = profitable sub-50% setup

### Strategy 1D: Earnings Gap Hold
- **Instruments:** Post-earnings gap stocks
- **Reported Stats:** Holds 5-15 days

### Strategy 1E: Sector Rotation Plays
- **Reported Stats:** Must track each separately; profit factor >1.5 = solid, >2.0 = strong after 30-40 trades

---

## Candidate 2: QuantifiedStrategies — 10 Best Swing Trading Strategies (2026)
**URL:** https://www.quantifiedstrategies.com/swing-trading-strategies/
**Source:** QuantifiedStrategies.com
**Notes:** Full entry/exit rules behind membership paywall. Public highlights:

- **MACD-Histogram on S&P 500:** $100K → $464,810 equity curve (long-term backtest)
- **RSI-2 strategy with 200-d MA filter:** Profitable since the 1990s
- **Weekend Trend Trader:** 22.9% CAGR, 58% max drawdown (1990–present)
- **Buy 3 consecutive down days / sell first up day:** Persistent profitability
- All backtested in Amibroker; code available to members
- **Reported Stats:** Profit factor 1.6 for top swing strategies

---

## Candidate 3: HyroTrader — Most Profitable Trading Strategy 2026 (Data-Backed)
**URL:** https://www.hyrotrader.com/blog/most-profitable-trading-strategy/
**Source:** HyroTrader Research / Aggregated Studies

### Strategy 3A: Trend Following (Best Long-Run Record)
- **Instruments:** Commodities (corn, gold, oil, natgas), major forex, futures
- **Timeframe:** Weekly analysis
- **Entry:** Identify direction of established price trends via moving averages / breakouts
- **Exit:** Reversal signals
- **Reported Stats:**
  - CAGR: 15-57% annually (published tests)
  - Win rate: 25-50%
  - Jegadeesh & Titman: ~1% avg monthly returns over 3-12 month holding periods
  - Low time commitment

### Strategy 3B: Mean Reversion (Bollinger Bands + RSI)
- **Instruments:** Forex pairs
- **Timeframe:** Not specified
- **Entry:** Price moves outside Bollinger Bands + RSI oversold/overbought
- **Reported Stats:**
  - Win rate: 71% in ranging markets
  - Avg return: 2.3% per trade
  - Risk: catastrophic losses on the 30% losers if trends persist

### Strategy 3C: Pairs Trading (Correlation-Based)
- **Entry:** Correlation coefficient >0.8, trade the divergence
- **Reported Stats:** 68% success rate

### Strategy 3D: False Breakout Strategy
- **Instruments:** Various (LuxAlgo research)
- **Entry:** Trade the false breakout (price breaks level then reverses)
- **Exit:** Standard targets
- **Reported Stats:**
  - Success rate: 62% (vs 54% for traditional breakout)
  - R:R: 1:2.5 (vs 1:1.8 for traditional)

### Strategy 3E: The Wheel (Options)
- **Instruments:** Equities with liquid options
- **Reported Stats:**
  - Avg annual returns: 15-40% (Reddit thetagang)
  - Automated version (PeakBot): 32% avg, 70-75% win rate
  - SteadyOptions: 72.7% win rate, 116.7% gain (2024)

---

## Candidate 4: Reddit — Stairway to Heaven Gold Trend-Following Breakout
**URL:** https://www.reddit.com/r/algotrading/comments/1unk44b/stairway_to_heaven_a_trendfollowing_breakout/
**Source:** Reddit r/algotrading (u/UniversalJS)

### Strategy Specs
- **Instrument:** Gold (XAU)
- **Type:** Trend-following breakout system
- **Timeframe:** Not specified
- **Reported Stats:**
  - 1,136 trades
  - Win rate: 31%
  - Avg win: $126
  - Avg loss: $33
  - Equity curve: stair-shaped (cycles of drawdown then trend capture)
  - Combined version with mean-reversion grid: 8K trades, Sharpe 4.21

### Notes
- Low win rate by design (trend following signature)
- Author also backtested on MNQ
- Oldest algo broke after 8 years live — killed after giving back full year of profits

---

## Candidate 5: Reddit — 124% on 3-Year Backtest
**URL:** https://www.reddit.com/r/algotrading/comments/1wapid7/124_on_3yr_backtest/
**Source:** Reddit r/algotrading (u/Dependent_Stay_6954)

### Strategy Specs
- **Instrument:** Unknown equities (long-only)
- **Type:** Quant-tested edge, full systematic
- **Timeframe:** Not specified
- **Reported Stats:**
  - 2025 performance: 124% profit
  - 3-year backtest: profitable
  - Long-only (suits bull markets)
  - Author acknowledges edges degrade quickly

---

## Candidate 6: SetupAlpha — Scientific Workflow for Generating Alpha (2026)
**URL:** https://medium.com/@setupalpha.capital/my-scientific-workflow-for-generating-alpha-in-quantitative-trading-in-2026-5238b26d4d95
**Source:** Medium / SetupAlpha Capital

### Methodology (not a strategy per se)
- **Pre-build phase:** Test signal via Information Correlation (IC) before coding
- **Framework:** Rolling IC + Information Ratio (IR) across years — used by BlackRock, Goldman
- **Metrics:** T-stats for statistical significance
- **Workflow:** Signal filtering → IC stability check → Walk-forward analysis → Strategy build
- **Key insight:** Edge must be stable, not just high-returning
- **Tools:** RealTest Walk Forward Analysis, ResearchGate for signal ideas

---

## Candidate 7: Build Alpha — Professional Guide to Trading Edges
**URL:** https://www.buildalpha.com/edge-in-trading/
**Source:** Build Alpha (David Bergstrom)

### Framework (not a specific strategy)
- **Types of edge:** Time-of-day, price action, alternative data
- **Key concept:** Edge + time = Law of Large Numbers profitability
- **Tools:** E-ratio, Monte Carlo distributions, equity curves, heat maps
- **Robustness testing:** Largest suite of robustness checks for algo strategies
- **Warning:** Many strategies fail in live markets — stress testing is an edge itself

---

## Candidate 8: Reddit — 16,000 Retail Strategy Backtests
**URL:** https://www.reddit.com/r/algotrading/comments/1q5op3l/backtested_16000_retail_trading_strategies_how_do/
**Source:** Reddit r/algotrading (u/misterdonut11331)

### Methodology (meta-analysis, not strategy)
- **Scope:** 50 stocks × 80 strategies × 4 timeframes = ~16,000 backtests per run
- **Lookback:** Varies by timeframe (5m → 14 days)
- **Composite scoring:** Sharpe, alpha return vs B&H, win rate, trade count (penalize high turnover)
- **Context:** Strategy mining at scale — multiple timeframes per stock

---

## Candidate 9: ThinkMarkets — Best Community TradingView Strategies 2026
**URL:** https://www.thinkmarkets.com/en/trading-academy/trading-view/best-community-tradingview-strategies-to-trade-in-2026/
**Source:** ThinkMarkets Trading Academy

### Guidance (not specific strategies)
- **Recommendation:** Use enough history to cover multiple market phases
- **Metrics:** Profit factor, win rate, drawdown
- **Key point:** Shorter backtest windows can work but statistically meaningful sample required

---

## Summary of High-Interest Candidates

| # | Candidate | Win Rate | PF | Key Metric | Instrument | Vibe |
|---|-----------|----------|----|------------|------------|------|
| 1A | 20 EMA Reversion | 55-65% | >1.5 target | Trending markets | Stocks | High confidence setup |
| 1B | Consolidation Breakout | — | ≥2:1 R:R | Measured move | Stocks | Clean momentum |
| 1C | Fib Retracement | 45-55% | 3:1-5:1 R:T2 | Confluence entry | Stocks | Asymmetric risk |
| 2 | RSI-2 + 200MA | Profitable since 1990s | — | Decades of edge | SPY | Gold standard |
| 2 | Weekend Trend Trader | — | 22.9% CAGR | 58% max DD | SPY | High DD but solid |
| 3A | Trend Following | 25-50% | 15-57% CAGR | Low time commitment | Commodities/FX | Best long-run |
| 3B | Bollinger+RSI Mean Rev | 71% | 2.3%/trade | Ranging markets | Forex | High WR, hidden tail risk |
| 3D | False Breakout | 62% | 1:2.5 R:R | Better than real breakout | Various | Counter-intuitive |
| 4 | Stairway to Heaven Gold | 31% | Avg W $126/L $33 | Trend-following | Gold | Low WR, positive skew |
| 5 | 124% Annual (2025) | — | Long-only | Degrades fast | Equities | High return, short shelf life |