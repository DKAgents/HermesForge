# Edge Discovery — Non-X Sources
## Date: 2026-10-01
## Agent: External Edge Discovery

---

## 1. FinLab — Short-Term Mean Reversion Strategy (3-Day Laggard Rule)
**URL:** https://finlab.finance/en/blog/us-mean-reversion-strategy
**Source:** FinLab Research Blog
**Confidence:** High (published code, 10-year backtest, OOS validation)

### Strategy Spec
- **Entry Rules:** Inside a QQQ uptrend regime (QQQ above 200D MA AND 6-month/126-day return positive), hold whichever of TQQQ or TECL lagged over the last 3 trading days.
- **Exit Rules:** Rotate to treasuries/gold/cash when QQQ trend filter flips risk-off. 8% trailing stop on leveraged leg.
- **Timeframe:** Daily rebalancing, 3-day lookback, monthly resampling.
- **Instruments:** 3x leveraged ETFs (TQQQ, TECL), QQQ for trend filter, defensive ETFs for risk-off.
- **Win Rate:** Not directly stated. 67.4% CAGR.
- **Profit Factor:** Not directly stated.
- **Max Drawdown:** -27.6%
- **Volatility:** 33.1%
- **Period:** 2016–2026 (10 years)
- **OOS Sharpe (2022–):** 1.50
- **Monthly Sharpe (full):** 1.43
- **Risk-On Coverage:** 68.4% of trading days

### Key Insight
The regime gate (QQQ trend filter) does most of the work — either leveraged fund returned 4-5%/mo in risk-on regimes vs QQQ's 1.71%. The laggard signal adds ~0.74%/mo edge on top.

---

## 2. FinLab — Post-Earnings Announcement Drift Strategy
**URL:** https://finlab.finance/en/blog/us-earnings-surprise-strategy
**Source:** FinLab Research Blog
**Confidence:** High (19,083-event study + backtest)

### Strategy Spec
- **Entry Rules:** Risk-on when breadth of positive earnings surprises across liquid US universe is high. Hold leveraged ETFs (TQQQ/TECL). Stock-level signal: top decile by recent earnings surprise.
- **Exit Rules:** Monthly rebalancing with 8% intramonth stop. Rotate to defensive ETFs when breadth signal weakens.
- **Timeframe:** Monthly rebalancing, 63-day earnings surprise half-life.
- **Instruments:** TQQQ/TECL/QQQ ETFs, US liquid large-cap universe for breadth signal.
- **Results:** 39.5% CAGR, 1.57 monthly Sharpe, -21.1% max DD.
- **Trades:** ~235 across 10 years (about 4.1x turnover/year).
- **OOS Sharpe:** N/A (part of 10-strategy comparison).

### Key Insight
Single-name earnings surprise edge is small in liquid US large caps (post-2016). The *breadth* of positive surprises across the market is the useful risk-on signal. Beats that fell on report day drifted +0.84% over 60 days; beats with positive day-0 pop showed zero drift.

---

## 3. TradingSim — 7 Swing Trading Strategies (Aug 2026)
**URL:** https://www.tradingsim.com/blog/swing-trading-strategies
**Source:** TradingSim Blog (Al Hill)
**Confidence:** Medium-High (experienced trader, specific rules shared but no formal backtest numbers)

### Strategies & Specs

**Strategy 1: Pullback Buy** (Bread & butter)
- Entry: Stock in uptrend (20 EMA > 50 EMA), pulls back 1-3 days to support (20 EMA or prior swing low), bounces. Buy when high of candle that tested VWAP/support is exceeded.
- Exit: Stop below the reversal candle low. Profit target at next resistance level (~2:1 R/R).
- Fail conditions: Pullback >10% = trend breaking. Near ATH without resistance above. Choppy sideways markets.

**Strategy 2: MA Crossover**
- Entry: 10 EMA crosses above 20 EMA + 50 EMA also aligned bullishly.
- Exit: Cross back below.
- Warning: Alone = whipsaw machine. Must combine with support/resistance, volume, or catalyst.

**Strategy 3+:** Support/Resistance Bounce, Breakout Trade, Fibonacci Retracement (50% & 61.8% levels), VWAP Anchor, Earnings Momentum.
- **Key stat:** 2-10 day holds captured 68% of S&P 500 total return (J.P. Morgan equity derivatives).

---

## 4. QuantifiedStrategies.com — 200 Trading Strategies Catalog
**URL:** https://www.quantifiedstrategies.com/trading-strategies-free/
**Source:** QuantifiedStrategies.com (Oddmund Grotte & Håkan Samuelsson)
**Confidence:** High (published since 2012, former prop traders)

Massive catalog of backtested strategies across categories:
- **Swing trading** (mean reversion, momentum, rotation)
- **Volatility trading**
- **Overnight trading** (overnight edge)
- **Day trading** (price action, outside day, intraday)
- **Seasonality** (calendar-based anomalies)
- **Momentum** (all-time high, bond rotation [TLT/SPY])
- **Trend following** (200D MA, ADX indicator, Supertrend, Golden Cross)
- **MA strategies** (25+ moving average articles)
- **Market-neutral** (pairs trading, arbitrage, long/short combos)
- **Price action** (head & shoulders, double bottoms)
- **Mean reversion** (2 simple MR strategies)
- **2x Leveraged ETF Strategy** (14% annual returns)

Specific strategy extracted: **XLP Mean Reversion**
- Entry: If XLP closes under 2x band below 25-day H-L average, AND IBS > 0.4, go long at close.
- Exit: When close > yesterday's high.
- Results: 389 trades, 0.41% avg gain, 8% CAGR (vs 8.8% B&H), 31% time in market, 17% max DD, PF 1.75.

---

## 5. Reddit r/algotrading — 7,137-Trade Backtest (63.6% WR)
**URL:** https://www.reddit.com/r/algotrading/comments/1w2ymq1/
**Source:** Reddit (anonymous systematic trader)
**Confidence:** Low-Medium (self-reported, no public code)

### Strategy Spec
- **Entry Rules:** US equity strategy using 1-second data. RVOL-based entry + other conditions (kept private).
- **Exit Rules:** Not disclosed.
- **Timeframe:** Jan 2–Jul 31, 2026, trading 9:30–11:00 ET only.
- **Trades:** 7,137
- **Win Rate:** 63.6%
- **Profit Factor:** 1.84

### Key Insight
The thread discusses what to check first at PF 1.84 — the community consensus: check for overfitting, check OOS, check the distribution of winners/losers (are wins concentrated in certain regimes).

---

## 6. Reddit r/algotrading — Backtesting in 2026
**URL:** https://www.reddit.com/r/algotrading/comments/1t4h8ms/backtesting_in_2026/
**Source:** Reddit
**Confidence:** Low (discussion thread, no specific strategy)

Discussion of futures trading strategies in MetaTrader and TradingView. General backtesting methodology questions.

---

## 7. Anny.Trade — 38 Crypto Strategies Backtested (2026)
**URL:** https://anny.trade/blog/top-proven-crypto-trading-strategies-2026
**Source:** Anny.Trade
**Confidence:** Medium (backtests include fees/slippage, OOS validation reported)

### Top Strategies

**#1: Overshoot Fader · Bollinger %B · SUI (4h, short)**
- PF: 2.65
- OOS Sharpe: 0.38 (77.38% degradation — WARNING)
- Instrument: SUI, 4h chart

**#2: Downshift Rider · MACD · DOT (4h, short)**
- OOS Sharpe: 1.60 (0.00% degradation)
- Highest return in the set
- Instrument: DOT, 4h chart

**#4: Structure Slider · Market Structure · AVAX (4h, short)**
- OOS Sharpe: 1.57 (OOS improved over in-sample)
- Instrument: AVAX, 4h chart

**Balance Fader · STOCHRSI LONG · UNI (4h, long)**
- StochRSI on UNI, long side

### Methodology
Backtests include trading fees and slippage, assume full-capital sequential compounding, omit futures funding costs on shorts.

---

## 8. AppliedXL — Biotech Quant Trading Model (Clinical Trial Alpha)
**URL:** https://www.appliedxl.com/research/clinical-trial-alpha-quant-model
**Source:** AppliedXL Research
**Confidence:** Medium-High (107 OOS trades, published methodology)

### Strategy Spec
- **Entry Rules:** Detect real-time changes to clinical trial registrations (ClinicalTrials.gov, SEC filings, press releases, PubMed). Score drug + operations quality. Enter when cross-validation detects structural patterns suggesting asymmetric information.
- **Exit Rules:** Not disclosed (proprietary).
- **Timeframe:** Event-driven (clinical trial amendments).
- **Instruments:** Biotech equities.
- **Results:** 107 OOS trades, +204.7% cumulative return, 1.32 Sharpe, 1.83 Sortino, -7.1% max DD, 72% hit rate.
- **Period:** 2021–2025 OOS.

### Key Insight
Execution risk varies 120-179% between sponsors. Disease area risk varies <10% across companies. The edge comes from tracking amendments in real time rather than looking at today's registry snapshot.

---

## 9. QuantPedia — Multi-Asset Pullback Strategy Discovery (AI-Assisted)
**URL:** https://quantpedia.com/testing-an-ai-assisted-research-workflow-for-multi-asset-pullback-strategy-discovery/
**Source:** QuantPedia
**Confidence:** Medium (AI-assisted, but public methodology)

### Strategy Spec
- **Entry Rules:** Short-term price reversals following adverse daily returns. Volatility-adjusted position sizing. Equal-weighted allocation across active signals.
- **Exit Rules:** Dynamic based on volatility targeting.
- **Timeframe:** Daily.
- **Instruments:** Multi-asset class.
- **Results:** Sharpe 1.25 in most recent 5-year window (2021-2025), win rates >56% throughout.
- **Key:** No evidence of alpha decay — strongest period was most recent.

### AI Tool Evaluation
Claude Opus 4.8 outperformed ChatGPT 5.5 for understanding research goals, producing coherent analysis, and generating structured output.

---

## 10. TradeZella — 5 Swing Trading Strategies (Exact Rules)
**URL:** https://www.tradezella.com/blog/swing-trading-strategies
**Source:** TradeZella Blog
**Confidence:** Medium (specific rules, journaling framework, no published backtest numbers)

### Strategy 1: Mean Reversion to 20 EMA
- Entry: Stock pulls back to 20 EMA in uptrend. Enter on confirmation candle.
- Exit: Stop below low of reversal candle OR below 20 EMA by 1.5% (whichever smaller). Target: next resistance.
- Expected WR: 55-65% in trending markets.

### Strategy 3: Fibonacci Retracement Entry
- Entry: Enter at 50% or 61.8% retracement levels.
- Expected WR: 45-55% (lower WR, larger avg winners).

### Strategy 5: Sector Rotation Play
- Entry: Filter that improves other setups. Not standalone.
- Use sector rotation to avoid trading during sector-wide weakness.

---

## 11. LuneFi — Mean Reversion Strategy 2026
**URL:** https://lunefi.com/blog/mean-reversion-trading-strategy-2026-backtests-win-rates-risks-hybrid-tips
**Source:** LuneFi
**Confidence:** Low-Medium (aggregated/curated, original backtest source unclear)

Key claim: Mean reversion setups delivering +30.4% OOS returns vs Nasdaq +24.4%, 72% WR over 83 trades, -10.2% max DD.

---

## 12. Medium (Kryptera) — Golden Cross 66-Year Backtest
**URL:** https://medium.com/@Kryptera/the-slowest-signal-on-wall-street-66-years-of-the-golden-cross-62ddc215a1a8
**Source:** Medium / Kryptera
**Confidence:** Medium (backtest numbers stated, reproducible methodology claimed)

### Strategy Spec
- **Entry:** 50-day MA crosses above 200-day MA (Golden Cross).
- **Exit:** Death Cross (50 below 200).
- **Results:** 78.8% WR, 15% avg trade return, PF >10.
- **Instrument:** SPY (S&P 500 ETF).
- **Period:** ~66 years.

---

## 13. Medium (Kryptera) — Triple RSI on SPY
**URL:** https://medium.com/@Kryptera/chasing-dips-in-a-bull-market-backtesting-the-triple-rsi-strategy-on-spy-0d3cb307fbfd
**Source:** Medium / Kryptera
**Confidence:** Medium

### Strategy Spec
- **Entry:** Triple RSI configuration buying dips on SPY.
- **Results:** 73.2% WR, PF 3.51.
- **Instrument:** SPY.
- **Period:** 1993-present.

---

## 14. Medium (Kryptera) — Monday Bounce (33 Years SPY)
**URL:** https://medium.com/@Kryptera/the-monday-bounce-what-33-years-of-spy-data-say-about-buying-the-dip-654d252306bb
**Source:** Medium / Kryptera
**Confidence:** Medium

### Strategy Spec
- **Entry:** Buy the Monday dip on SPY.
- **Results:** 73.2% WR, 310 trades.
- **Period:** 1993-2026.

---

## Summary of Top Candidates for Deep Evaluation

| Priority | Source | Edge Type | Key Metric | Why Interesting |
|----------|--------|-----------|------------|-----------------|
| P1 | FinLab Mean Reversion | ETF timing/mean reversion | 67.4% CAGR, -27.6% DD | Published code, 10yr backtest, OOS validated |
| P1 | FinLab Earnings Surprise | Event-driven breadth signal | 39.5% CAGR, 1.57 Sharpe | Novel signal (PEAD breadth), 19K-event study |
| P2 | QS Stochastic Oscillator | Indicator mean reversion | 77.7% WR, PF 2.58 | Simple rules, robust across lookback params |
| P2 | QS RSI Timeframe Study | Timeframe comparison | PF 1.72-2.17 daily RSI | Critical finding on cost sensitivity |
| P2 | QS Calendar Day Strategy | Calendar/seasonality | 65% WR, PF 1.7 | Simple, backtested to 2000 |
| P3 | Anny.Trade DOT MACD | Crypto momentum | OOS Sharpe 1.60, 0% deg | Best OOS stability in crypto set |
| P3 | AppliedXL Biotech Model | Alternative data alpha | 1.32 Sharpe, 72% hit rate | Novel data source (clinical trials) |
| P3 | QuantPedia Pullback | Multi-asset pullback | Sharpe 1.25 recent | No alpha decay evidence |
| P4 | Reddit 7,137-trade | Systematic US equity | 63.6% WR, PF 1.84 | Large sample, specific session window |
| P4 | Medium Kryptera Golden Cross | Trend following | 78.8% WR, PF>10 | 66-year backtest |