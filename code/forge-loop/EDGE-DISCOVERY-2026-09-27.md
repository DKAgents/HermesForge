# External Edge Discovery
**Date:** 2026-09-27  
**Agent:** HermesForge External Edge Discovery  
**Sources:** Blogs, research sites, Reddit

---

## 1. The Volatility Edge — VIX-based SPY Mean Reversion
**Source:** Concretum Group (5th place 2026 Quantpedia Awards)  
**URL:** https://concretumgroup.substack.com/p/a-profitable-strategy-for-short-term

### Strategy
Dual approach using VIX Index to time mean-reverting SPY trades during volatility bursts.

### Entry Rules
- VIX signal identifies **volatility bursts** (temporary stress regimes)
- Position-sizing rules to **exploit prolonged weakness**
- Computed shortly before close, executed via **market-on-close (MOC)** orders

### Exit Rules
- Exit criteria designed to capture market rebound after stress subsides
- Active only during defined volatility regimes

### Reported Performance
- **10.8% CAGR** net of fees (Jan 2007 – Jun 2026)
- Active on only **14%** of trading days
- No continuous intraday monitoring needed

### Instruments
- SPY

### Timeframe
- End-of-day, MOC orders

### Confidence: **Medium** — published Quantpedia award finalist, 19-year backtest, transparent methodology

---

## 2. Hybrid Mean Reversion Strategy (RSI + Bollinger + OU Filter)
**Source:** LuneFi Research  
**URL:** https://lunefi.com/blog/mean-reversion-trading-strategy-2026-backtests-win-rates-risks-hybrid-tips

### Strategy
Multi-indicator mean reversion with regime detection to avoid trending markets.

### Entry Rules
1. **Timeframe:** 5-15 min (avoid news hours)
2. **RSI(14):** <25 for long, >75 for short
3. **Bollinger Bands (20,2SD):** Confirm touch of outer band
4. **OU z-score:** |z| > 1.25 and kappa > 0.05 (fast reversion speed)
5. **Volume filter:** >1.5x average
6. **ADX filter:** <25 (skip strong trends)

### Exit Rules
- **Stop-loss:** 1.5-2x ATR beyond entry
- **Take-profit:** Mean (20-day SMA) or 1:1.5 risk-reward
- **Trailing stop:** Activate after 50% profit

### Reported Performance
- Win rate: **65-75%** mean reversion vs 10-40% trend following
- Sharpe: **2.11** in one 25-year test
- 2025: **+30.4%** returns with **-10.2%** drawdown
- Annualized: up to 15% vs 10% buy-and-hold (S&P 500, 2010-2025)

### Instruments
- ES, NQ futures (primary)
- Crypto during consolidation phases (range-bound BTC)
- Large cap stocks, SPY, QQQ

### Risk Note
Fails catastrophically in prolonged trending markets. Regime detection (ADX/OU) critical.

### Confidence: **Medium-High** — detailed rules, multiple backtest periods, specific indicator thresholds

---

## 3. Leverage Dual Momentum (LDM) — Nasdaq-100
**Source:** r/algotrading Reddit  
**URL:** https://www.reddit.com/r/algotrading/comments/1vb4ajj/leverage_dual_momentum_ldm_a_24year_backtested/

### Strategy
3-state momentum system with increasing leverage based on breadth and trend strength.

### Rules
- **State 1 (Cash/T-Bills):** Exit when trend/momentum rules trigger
- **State 2 (2x QLD):** Moderate risk-on when breadth is recovering/stabilizing
- **State 3 (3x TQQQ):** Full risk-on when broad tech participation is robust

### Reported Performance
- 24-year backtest (2000-2024) — specific metrics not fully extracted (Reddit text truncated)
- 3-state dual momentum approach

### Instruments
- QQQ / QLD (2x) / TQQQ (3x)

### Timeframe
- Long-term/systematic

### Confidence: **Medium** — established dual momentum framework but full spec not accessible from extracted text

---

## 4. High-Frequency US Equity Strategy (1-Second Data)
**Source:** r/algotrading Reddit  
**URL:** https://www.reddit.com/r/algotrading/comments/1w2ymq1/7137trade_backtest_636_win_rate_pf_184_what_would/

### Strategy
Systematic US equity strategy using 1-second tick data. RVOL-based entry with additional undisclosed conditions.

### Entry Rules
- RVOL (relative volume) is a component, not the sole entry signal
- Additional conditions (private)
- Trading window: **9:30 – 11:00 ET** only

### Exit Rules
- Not publicly disclosed

### Reported Performance
- **7,137 trades** (Jan 2 – Jul 31, 2026)
- **63.6% win rate**
- **PF 1.84**
- **+0.17% average trade**
- **6m 7s average hold**
- **-0.9% max drawdown**
- Uses quote/trade data for fills (not bar-touch assumption)

### Instruments
- US equities

### Timeframe
- 1-second data, first 90 minutes of market open

### Confidence: **Medium** — excellent granular stats but entry rules private, short 7-month sample

---

## 5. Two NQ Tick-Data Strategies
**Source:** r/algotrading Reddit  
**URL:** https://www.reddit.com/r/algotrading/comments/1wo6pp6/found_two_strategies_so_far_after_backtesting_7/

### Strategy
Two undisclosed strategies discovered from 7 years of NQ tick data.

### Methodology
- Built on **2019-23** training data
- Graded only on **2024-26** out-of-sample (never seen data)
- Tick data from DataBento (~$2K cost)
- No tweaks after OOS results

### Reported Performance
- "2 strategies found" — exact metrics private

### Instruments
- NQ (Nasdaq-100 futures)

### Confidence: **Low-Medium** — solid OOS methodology but no strategy rules disclosed

---

## 6. ScraperGold EA — XAUUSD
**Source:** MQL5 Blog  
**URL:** https://www.mql5.com/en/blogs/post/776447

### Strategy
MetaTrader 5 Expert Advisor for gold trading.

### Methodology
- Tested in MT5 Strategy Tester with **real tick data** on XAUUSD
- Jan – Sep 2026 backtest

### Reported Performance
- Full results include "less flattering numbers" per author
- Exact metrics: see product page for demo

### Instruments
- XAUUSD (Gold)

### Confidence: **Low** — commercial EA, limited independent verification

---

## 7. Liquidity Sweep + Regime Detection Algo
**Source:** r/algotrading Reddit  
**URL:** https://www.reddit.com/r/algotrading/comments/1u8dkkb/how_would_you_further_validate_this_trading/

### Strategy
Liquidity sweeps + regime detection using EWM volatility + trend continuation probability.

### Reported Performance (net of costs)
- **Precious metals** (XAU, XAG, XPT): PF **1.1-1.6**, max DD 5-10%
- **FX pairs:** Mixed, some profitable, others break-even
- **Indices** (S&P500, Nasdaq): Around break-even
- **Crypto** (BTC/ETH): **Negative expectancy**, DD > 15%

### Insight
Knows where the edge exists and where it doesn't. Only precious metals show consistent positive expectancy.

### Confidence: **Medium** — honest reporting of asset-specific performance, no overfitting claims

---

## 8. Alphabetical Categorization of Expert Edges
**Source:** SetupAlpha / Medium  
**URL:** https://setup4alpha.substack.com/p/60-market-edges-systematic-traders

### Summary
Comprehensive catalog of **60+ market edges** organized into categories:
- Broker/execution edges
- Factor edges (academically proven)
- Information edges
- Strategy/process edges
- Structural edges (e.g., crypto liquidation cascades)
- Volatility edges (VRP: selling options works 85% of time)
- Time-based edges (calendar effects)

### Key Quote
> "One edge fades. A stack of them holds."

### Confidence: **High** — excellent reference catalog, not a single strategy but a framework for edge discovery

---

## Recommended Action Items

1. **HIGH PRIORITY** — X Strategy Scout should deep-read:
   - @RHerman threads (80-83% win rate NQ strategies)
   - @AlphaWizarDD momentum ETF (beat Nifty 6x)
   - @0xTrackmind quant paper (alpha-weeding framework)

2. **DEEP READ FOR SWARM INTEGRATION:**
   - Concretum VIX/SPY strategy — could complement existing edge detection
   - LuneFi mean reversion spec — full rules deployable, can backtest against our STR-Q pipeline
   - LDM 3-state momentum — simple, systematic, long timeframe

3. **FURTHER RESEARCH NEEDED:**
   - Find the author's full thread for @RHerman (strategy rules hidden behind login)
   - Check if LuneFi's full OU filter code is available
   - Investigate the 1-second equity strategy author — may publish full rules later