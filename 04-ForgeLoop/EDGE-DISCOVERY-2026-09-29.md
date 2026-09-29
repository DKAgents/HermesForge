# EDGE DISCOVERY — 2026-09-29

Sweep of external sources for new strategy edges. X/Twitter URLs saved separately to
`edge-discovery-candidates.txt` for nightly X Strategy Scout deep-read. Below: non-X
sources, extracted strategy specs.

---

## 1. The Volatility Edge — VIX ETN Dual Approach (Concretum Group)
- **Source:** https://concretumgroup.com/the-volatility-edge-a-dual-approach-for-vix-etns-trading/ (+ substack automation writeup)
- **Status:** Research paper, 5th place Quantpedia Awards 2026. Authors: Zarattini, Aziz, Mele (SSRN 5316487).
- **Edge:** Systematic VIX ETN trading using TWO signals — (a) option-market volatility risk premium, (b) slope of VIX term structure (contango/backwardation). Timed increase/decrease of vol exposure.
- **Instrument/Timeframe:** VIX-linked ETNs (e.g., VXX/UVXY class), 2008-2025 backtest, 5 bps cost per trade modeled.
- **Reported results:** 16.3% CAGR, Sharpe ~1.0, low correlation (~15%) with equities.
- **Exit/risk:** Dual-signal regime filter; no explicit per-trade stop published — treat as regime-switching allocation.
- **Notes for swarm:** Great uncorrelated sleeve candidate for a portfolio (VST/CDX-style), not an entry-timing edge. 17-year span incl. vol spikes = robust. Be careful: ETN contango bleed is the hidden killer; strategy presumably handles via signals.

## 2. VIX Stress → SPY Mean-Reversion (Concretum Group, short-term)
- **Source:** https://concretumgroup.substack.com/p/a-profitable-strategy-for-short-term
- **Edge:** Use VIX spike (temporary stress regime) as entry trigger to fade moves in SPY — over-amplified panic moves revert.
- **Instrument/Timeframe:** SPY, short-term (days).
- **Spec incomplete in extract** — substack body truncated; needs deep-read for exact VIX threshold and exit logic.

## 3. Triple RSI Strategy (QuantifiedStrategies / Connors R3 variant)
- **Source:** https://www.quantifiedstrategies.com/triple-rsi-trading-strategy/
- **Edge:** Mean reversion; three RSI conditions + 200-day MA trend filter. Inspired by Larry Connors R3, modified.
- **Entry:** RSI-based oversold conditions; only trades when price above 200-day average.
- **Reported results:** ~90% win rate (SPY backtest); few trades but strong avg gain. On 5 popular stocks (AMZN etc.): 25 trades, 72% WR, +0.80%/trade, PF 1.70 (daily data).
- **Comparison test:** Simple RSI 80.9% WR → Double 83.5% → Triple 88.9% WR, but CAGR shrinks as rules stack. More rules ≠ more profit.
- **Caveat:** High WR but low frequency; small wins/large rare losses — check tail.

## 4. RSI Nasdaq Stock Strategy — PF 2.0, 17% Drawdown (QuantifiedStrategies)
- **Source:** https://x.com/i/article/2099470335242641712 (X article, but non-thread; also on quantifiedstrategies.com)
- **Edge:** RSI-based mean reversion applied to Nasdaq stocks; PF ~2.0, only ~17% drawdown. Also works on S&P 500 stocks per article.

## 5. Stochastic Oscillator Trading Strategy — 77.7% WR, PF 2.58
- **Source:** https://x.com/i/article/2100203214058455102 (X article)
- **Reported results:** Short window 77.7% WR, PF 2.58, avg +0.68%/trade pre-cost. Longer 2016-2026: 107 trades, 75.7% WR, PF 2.23. Recent period weaker.
- **Caveat:** 107 trades over 10 years — low frequency, and recent period degradation noted by author.

## 6. Mean-Reversion Framework 2026 (Lunefi research roundup)
- **Source:** https://lunefi.com/blog/mean-reversion-trading-strategy-2026-backtests-win-rates-risks-hybrid-tips
- **Edge:** MR strategies: 65-75% WR typical vs 10-40% for trend following. BB+RSI on forex showing 71% WR, 2.3% avg per trade (TradeFundrr), pairs trading 68% success with correlation >0.8.
- **Filters:** volume >1.5x avg, ADX <25 (no trend), z-score >1.25; SL 1.5-2x ATR, TP at mean or 1:1.5 RR; trailing after 50% profit.
- **Reference backtest:** r/algotrading "A mean reversion strategy with 2.11 Sharpe" (25-yr test, Sharpe 2.11) — https://www.reddit.com/r/algotrading/comments/1cwsco8/

## 7. Stairway to Heaven — Gold Trend-Following Breakout (r/algotrading)
- **Source:** https://www.reddit.com/r/algotrading/comments/1unk44b/
- **Edge:** Trend-following breakout system on gold. 31% WR (typical low-WR/high-payoff TF profile).
- **Comments highlight:** execution infrastructure reliability is must (net crashes/credentials lose the key trades); long drawdown endurance required.
- **Spec incomplete** — post body not fully extracted; needs deep-read for entry/exit rules. Gold TF edges are HARD to beat — verify.

## 8. r/algotrading benchmarking thread — raw PF thresholds
- **Source:** https://www.reddit.com/r/algotrading/comments/1vgx5dg/
- **Edge:** Community benchmark discussion: raw strategy PF >1.3 / expectancy / CAGR / WR norms; 2022-2026 test period. Useful as sanity-check framework for our pipeline (STR-Q thresholds).

## 9. r/Trading — "Genuinely profitable, mechanically backtested intraday strategy?"
- **Source:** https://www.reddit.com/r/Trading/comments/1ubybkr/
- **Edge:** Thread seeking mechanical intraday strategies with clear entry/exit rules; no paid-signal noise. Good candidate list source; content truncated in extract — deep-read recommended.

## 10. 60+ Market Edges Systematic Traders Use (SetupAlpha, Medium)
- **Source:** https://medium.com/@setupalpha.capital/60-market-edges-systematic-traders-use-in-2026-the-ultimate-guide-cce79989ff10
- **Edge:** Catalog of 60+ edges: broker/execution edges (IBKR smart routing saves 0.5-1%/yr), volatility edges (VRP selling works ~85% of time, tail risk warning), etc. Upcoming deep-dive strategy with RealTest code per their roadmap.
- **Notes:** Framework reference, not a single backtested strategy.

---

## CANDIDATE SUMMARY (ranked by fit to our book)

| # | Candidate | Type | WR/PF | Fit |
|---|-----------|------|-------|-----|
| 1 | Volatility Edge VIX ETN (Concretum) | Vol sleeve | 16.3% CAGR, Sharpe~1, corr 15% | HIGH — uncorrelated sleeve |
| 2 | Triple RSI (Connors variant) | Stock MR | 90% WR / PF 1.70-2.5 | HIGH — matches STR-Q MR style |
| 3 | Stochastic Oscillator strategy | Stock swing | 75.7% WR / PF 2.23 (2016-26) | MED — low frequency, recent decay |
| 4 | RSI Nasdaq stocks | Stock MR | PF 2.0, DD 17% | MED-HIGH |
| 5 | VIX stress → SPY fade | Market-timing MR | TBD (spec incomplete) | MED — needs deep-read |
| 6 | Stairway to Heaven gold TF | Commodity TF | 31% WR | LOW-MED — gold TF hard to beat |
| 7 | Mean-reversion filter kit (Lunefi) | Framework | 65-75% WR norm | MED — filter ideas for our MR book |

## NEXT ACTIONS
- X Scout: deep-read the 17 X URLs (Trend Rebalance Map, Triple RSI threads, Stochastic, edgeful holdout, RyanRRs NQ model).
- Deep-read candidates: Concretum short-term SPY article (spec), Stairway to Heaven rules.
- Gate through PROP-001 gauntlet if any candidate moves forward: cost-first (need ≥45 bps gross), execution realism, DSR >0.95, PBO <0.30.