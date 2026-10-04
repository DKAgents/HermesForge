# EDGE-DISCOVERY-2026-10-04.md
# Non-X sources — Strategy Specs Extracted
# ==========================================

## 1. QuantifiedStrategies — 10 Best Swing Trading Strategies 2026
**URL:** https://www.quantifiedstrategies.com/swing-trading-strategies/
**Source type:** Blog / Strategy aggregator
**Reported metrics:** Various — several strategies backtested since 2012 publication, held up well

## 2. QuantifiedStrategies — 5 Algorithmic Trading Strategies 2026
**URL:** https://www.quantifiedstrategies.com/algorithmic-trading-strategies/
**Source type:** Blog / Strategy guide
**Key entries:**
- Sentiment analysis around earnings announcements for large-cap US stocks (2017-2024)
- Intraday volatility prediction for ES futures using order book features + macro calendar events
- Crypto sentiment analysis on BTC using funding rates, social-media mentions, on-chain metrics
- Trend following on indices — $100K initial capital (1993) grew to ~$2M, ~9.5% annual return
**Timeframe:** Daily to intraday
**Instruments:** ES futures, BTC, US stocks

## 3. CoinQuant — Best Crypto Trading Strategy 2026: Backtested and Ranked
**URL:** https://www.coinquant.ai/blog/best-crypto-trading-strategy-in-2026-backtested-and-ranked
**Source type:** Research / Comparison article
**Test setup:** BTCUSDT spot (Binance), daily candles, $10K initial capital, 100% position size, long only, no leverage, 0.1% taker fee
**Strategies tested:** 5 families — mean reversion, trend following, Bollinger bands, etc.
**Key finding:** Bollinger Mean Reversion had highest WR (65.7%) but worst result (+10.4%, PF 1.07). High WR ≠ profitable. Ranking based on PF + Sharpe + total return.
**Takeaway:** Most popular crypto strategy family was trend following.

## 4. Audacity Capital — 10 Most Profitable Trading Strategies 2026
**URL:** https://audacity.capital/trading-guides/most-profitable-trading-strategies/
**Source type:** Blog / Educational guide
**Listed strategies:** Trend Following, Breakout Trading, Scalping, Swing Trading, News Trading, Carry Trade, Mean Reversion, Smart Money Concepts, Algorithmic Trading, Multi-Timeframe Analysis
**Details per strategy:**
- Trend Following: Beginner, 4H-Daily, Forex/Indices, Low risk — directional trade with trend
- Breakout Trading: Intermediate, 15M-4H, Forex/Crypto, Medium risk — confirmation candle close, volume check
- Scalping: Advanced, 1M-5M, Forex/Indices, High risk — full time scalping
- Swing Trading: Beginner, 4H-Daily, Forex/Stocks, Medium — multi-day holds
- Algorithmic: Advanced, Any timeframe, Multiple markets — automated trade execution
**No reported win rates or PF — this is a strategy catalog, not a quantified test.**

## 5. Trader's Second Brain — 3-Metric Edge Test
**URL:** https://www.traderssecondbrain.com/guides/do-you-have-trading-edge
**Source type:** Educational guide
**Framework:** Three metrics define edge:
- Win rate
- Reward-to-Risk ratio (R:R)
- Expectancy (dollar edge per trade)
**Sample size rules:** Don't make decisions <60 trades, don't bet career <200 trades.
**Key warning:** Confirmation-bias trap — must pre-declare analysis set before computing metrics.
**Verdict:** Measure full set first, filter second, note subset bias.

## 6. Reddit r/algotrading — Is Trading Edge Getting Harder to Find in 2026?
**URL:** https://www.reddit.com/r/algotrading/comments/1r8q206/is_trading_edge_getting_harder_to_find_in_2026/
**Source type:** Community discussion
**Key sentiment:** 55-60% edge not seen as sustainable. Simple strategies (RSI, MA crossovers) being arbed away.
**Consensus:** Edges shifting toward alternative data, market microstructure, novel transforms.

## 7. Reddit r/algotrading — 5,000+ Setup Ranker Backtest (no edge before fees)
**URL:** https://www.reddit.com/r/algotrading/comments/1wr9f3r/i_backtested_my_own_tradesetup_ranker_across_5000/
**Source type:** Community results post
**Key finding:** Tested trade-setup ranker across 5,000+ setups — no edge before fees regardless of stop placement.
**Open question:** What to test next.

## 8. Reddit r/Trading — 584 Trades, 55.1% WR, 1.55 PF
**URL:** https://www.reddit.com/r/Trading/comments/1vp4nx0/584_trades_551_win_rate_155_profit_factor/
**Source type:** Community backtest results
**Strategy:** Mean reversion type, algorithmic
**Metrics:** 584 trades, 55.1% WR, 1.55 PF, 2010-2026 sample
**Note:** Reddit blocked full extraction (prove-humanity gate).

## 9. Reddit r/algotrading — ATR Stop Width Comparison
**URL:** https://www.reddit.com/r/algotrading/comments/1wwahkv/the_tightest_stop_had_the_smallest_drawdown_and/
**Source type:** Community backtest results
**Setup:** Same entry, 3 ATR stop widths, 25-year test on SPY
**Results:**
- 1 ATR stop: 167 trades, 30.5% WR, PF 1.06, +7.8%, max DD 17.2%
- 2 ATR stop: 135 trades, 47.4% WR, PF 1.22, +41.7%, max DD 22.3%
- 3 ATR stop: 125 trades, 60.0% WR, PF 1.41, +92.1%, max DD 21.6%
**Key insight:** Tightest stop felt safest but bled — 30.5% WR is below random. Entry quality was being measured, not exit logic. Trade counts (125-167 over 25yr) too low to be conclusive.
**Instruments:** SPY (S&P 500 ETF), futures account

## 10. Reddit r/algotrading — Regime Dependency of Edge
**URL:** https://www.reddit.com/r/algotrading/comments/1vfgluu/your_strategy_does_not_have_an_edge_it_has_an/
**Source type:** Community discussion
**Key insight:** Strategy edge is an average across market regimes. If your backtest window was heavy on one regime, your edge is mostly that regime's contribution. Split testing by regime is essential.

## 11. PlayingForDoubles Substack — Stress-Test Your Strategy in 5 Minutes
**URL:** https://playingfordoubles.substack.com/p/stress-test-your-trading-strategy
**Source type:** Newsletter / Educational
**Key insight:** Paper edge can be exactly zero at 50% WR but account shrinking ~2%/trade. Must separate expectancy from win rate.
**Method:** Quick stress-test framework.

## 12. TradeZella — Backtesting Trading Strategies: Complete Guide 2026
**URL:** https://www.tradezella.com/blog/backtesting-trading-strategies
**Source type:** Educational guide
**Key benchmark:** Live WR, R-multiple, and PF within 10-15% of backtest = can increase confidence.
**Note:** General methodology guide.

## 13. AlgoTrader.ch — Algorithmic Trading Profitability Statistics (12 Numbers)
**URL:** https://algotrader.ch/blog/algorithmic-trading-profitability-statistics/
**Source type:** Research / Statistics
**Key statement:** No fixed return for algo trading — results depend on strategy, risk, costs, market conditions.
**Reported:** Mean reversion Sharpe ratios 0.8-1.2 historically.

## 14. TradeAlgo — Algorithmic Trading for Retail Investors 2026 Guide
**URL:** https://www.tradealgo.com/trading-guides/ai-trading/algorithmic-trading-for-retail-investors-a-complete-2026-guide
**Source type:** Educational guide
**Key benchmark:** Backtested mean reversion strategies typically show Sharpe ratio 0.8-1.2

## 15. Instagram (Quantified Strategies) — 2026 Trading Plan
**URL:** https://www.instagram.com/p/DTsVb9okotx/
**Source type:** Social media
**Backtest result (combined portfolio on SPY):** 3.0 PF, 13.5% CAGR, 83% market exposure, 16% risk

---

## Summary of Notable Edges Worth Further Investigation

| # | Edge / Pattern | Source | Reported Stats | Priority |
|---|---|---|---|---|
| 1 | RSI+EMA+VWAP combo on QQQ | X @QuantifiedStrat | 79.5% WR, 3.54 PF, 215 trades, 9.1% DD | HIGH |
| 2 | AI-discovered Gold strategy | X @RHerman | 67.39% WR, 1.515 PF, 1392 trades, +74.43% | HIGH |
| 3 | Mechanical 1R weekday-directional strategy | X @RHerman | 63.33% WR, 1.88 PF, 150 trades, 100% mechanical | HIGH |
| 4 | NQ Futures Gap Day Strategy | X @QuantifiedStrat | 64% WR, PF>2, 60min hold, 10yr data | MEDIUM |
| 5 | ATR scalping (TP=ATR) | X @Zabaroptik | 80% WR, 5.42 PF | MEDIUM (flagged) |
| 6 | Pairs Trading Strategy Builder | X @Raghunath_TL | 81% WR, PF~5 | MEDIUM |
| 7 | edgeful algo analyzer | X @edgeful | 57% WR, 4.03 PF | MEDIUM |
| 8 | ATR stop width comparison (3 ATR best) | Reddit r/algotrading | PF 1.06→1.41, WR 30.5%→60% | LOW (thin sample) |
| 9 | Mean reversion algo 2010-2026 | Reddit r/Trading | 55.1% WR, 1.55 PF, 584 trades | MEDIUM |
| 10 | Triple RSI on individual stocks | X @QuantifiedStrat | AMD: 22.29 PF, NVDA: 19.24 PF, TSLA: 0.83 PF | HIGH (variance insight) |
| 11 | Golden Cross (50/200 MA) | X @QuantifiedStrat | Classic trend-change strategy | LOW (well-known) |
| 12 | MACD Histogram strategy | X @QuantifiedStrat | 6669 trades — large sample | MEDIUM |
| 13 | SPY intraday setup (1998 sample) | X @QuantifiedStrat | "Strong combo" — details behind paywall | MEDIUM |
| 14 | RSI timeframe bakeoff (1min-monthly) | X @QuantifiedStrat | Costs change everything, weekly PF highest | HIGH (methodology) |
| 15 | Trend Rebalance Map (short sample) | X @RHerman | 83.33% WR, 2.06 PF, 18 trades | LOW (tiny sample) |