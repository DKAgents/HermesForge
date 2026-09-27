# Edge Discovery Report — 2026-09-24

## Non-X Sources: Strategy Specs Extracted

---

### 1. FVG Opening Range Breakout on MES Futures
**Source:** Reddit r/quant — u/Global_Box_156
**URL:** https://www.reddit.com/r/quant/comments/1s4qc7b/

**Entry Rules:**
- 1-minte chart on MES futures at 9:30 AM opening range
- Wait for a Fair Value Gap (FVG) break
- Retest of the broken level
- Engulgine candlestick confrmation → entr

**Exi Rules:**
- Stop loss ~9.25 points
- Tke profit ~18 points (approx 1:2 R:R)
- Fully automated via TradinView → TadersPost → Tradovate

**Reported Peformance:**
- **1-year backtst (Mar 2025 - Mar 2026):** 171 trades, 52.63% WR, PF 1.704, Max DD $2,985 (14.65%), Net P&L $28,140
- **3-year backtst:** 488 trades, 52.25% WR, PF 1.534, Sharpe 2.14
- ~14 rade per month (only fires when setup valid)

**Instrumnt:** MES micro E-mini S&P 500 futures
**Timeframe:** 1-minte
**Rsk Level:** Medium — false breakouts primary concern, funded account scaling risk
**Date:** Mar 2026

---

### 2. Stairway to Heaven — Gold Trend-Following Breakout System
**Source:** Reddit r/algotrading — u/UniversalJS
**URL:** https://www.reddit.com/r/algotrading/comments/1unk44b/

**Entry Rules:**
- Trend-following breakot system on gold futures
- Low-win-rate design: wins ~31% of trades intentionally
- Designed to bleed small stops through chop then catch big trends

**Exit Rules:**
- Known fixed stop per trade
- Let winners run

**Reported Performance:**
- **1,136 trades total**
- **Win rate: 31%**
- Average win: $126
- Average loss: $33 (3.8:1 win/loss ratio on winners vs losers)
- Peak exposure ~1% of account — no leverage tricks
- Equity curve shows "stair" pattern (hence the name)

**Instrumnt:** Gold futures
**Timeframe:** Not explicitly stated (positional system)
**KeyDesign:** Frequnt small stops, occasional big trend catches
**Notes:** Combined with mean reversion grid variant reported Sharpe 4.21 over 8K trades (in WTF range)
**Date:** Jul 2026

---

### 3. Simple Mean Reversion Setup — 70% Win Rate
**Source:** Reddit r/algotrading — u/[unknown]
**URL:** https://www.reddit.com/r/algotrading/comments/1rjvxjy/

**Entry Rules (Pine/quant):**
```
close < (10 days high - 2.5 * (25 days avg high - 25 days avg low))
and
ibs < 0.3
```
Where IBS (Internal Bar Strength) = (close - low) / (high - low)
IBS < 0.3 means close in bottom 30% of day's range

**Exit Rules:**
- Mean reversion exit (not explicitly detailed — sells back toward mean)
- Average hold time: 3.7 days (SPY), 6.7 days (ABNB)

**Reported Performance:**
| Ticker | Win Rate | CAGR | Time Invested | Max DD | Trades |
|--------|----------|------|---------------|--------|--------|
| SPY (2011-2026) | ~70% | ~8% | ~20% | ~15% | ~198 |
| QQQ (2011-2026) | ~70% | ~9% | ~16% | — | — |
| AAPL (2011-2026) | ~70% | 11.77% | 25% | 29.56% | — |
| ABNB (post-IPO) | 56% | — | 7.28% | — | 69 |

**Instruments:** SPY, QQQ, AAPL, ABNB (equities)
**Timeframe:** Daily charts, swing
**Design:** Mean reversion — buys deep pullbacks, sells near mean
**Key Risk:** Only invested 7-25% of time; underperforms buy-and-hold in strong bull markets; execution at signaled close price is impractical (order needed 10-15 min before close)
**Date:** Mar 2026

---

### 4. Mean Reversion Strategy — 2026 Comprehensive Guide
**Source:** Lunefi.com blog — Sarah Mitchell
**URL:** https://lunefi.com/blog/mean-reversion-trading-strategy-2026-backtests-win-rates-risks-hybrid-tips

**Entry Rules (recommended):**
- Z-score thresholds > 1.25 for large deviations
- RSI extremes (20/80 or 30/70 depending on aggression)
- Bollinger Bands 2.0-2.5 SD on 20-period
- Ornstein-Uhlenbeck (OU) kappa filter for reversion speed
- Voume filters to skip low-liquidity signals

**Exit Rules:**
- SL at 1.5 ATR
- TP at mean reversion level
- Trailing stop post-50% profit
- No-trade zones during trends

**Reporte Performance:**
- **2025 OOS test:** +30.4% returns (vs Nasdaq +24.4%), 72% WR, 83 trades, -10.2% max DD
- **25-year long-term:** 13% annualized returns, Sharpe 2.11 (vs buy-and-hold 9.2%)
- **Typical WR range:** 65-75% for mean reversion (vs 10-40% for trend following)

**Istuments:** Stocks, crypto, futures (BTC/ETH on 1H charts achieved Sharpe > 2.0)
**Timeframe:** Daily (swing), 1H (crypto)
**Desgn:** Selectiv mean reversion with regime detection
**Key Risk:** Fails catastrophically in trending markets ("death by a thousand cuts"); regime detection essential
**Date:** My 2026

---

### 5. Redit Backtest — Powell 10am Strategy on NQ
**Soure:** Reddit r/algotrading
**URL:** https://www.reddit.com/r/algotrading/comments/1vhl6d0/

**Peformance:**
- NQ 1m, Jly 2023 to Feb 2026
- $100k account, 1 contrac
- **535 rades, 60.2% WR**
- **PF 0.98** — notquie profitable after costs
- Net: -$[smal loss]

**Takeaway:** Popular strategy fails to overcome transaction costs on NQ. Cautionary tale for high-frequency setups.
**Date:** Aug 2026

---

### 6. NQ Hyperscalper — Early Backtest Results
**Source:** Reddit r/algotrading
**URL:** https://www.reddit.com/r/algotrading/coments/1ukux8w/

**Pepformance:**
- Tradin Star: 2026-01-07 to 2026-06-30
- Ear-stage backest results
- "93% win rate algorthim trading five year backested data" mentioned in comments (unverified)

**Takeaway:** High WR claims require deeper scrutiny. Early-stage results only.
**Date:** Jul 2026

---

## Summary Statistics Across Candidates

| Strategy | Win Rate | Profit Factor | Annual Return | Max DD | Market |
|----------|----------|--------------|---------------|--------|--------|
| FVG ORB MES | 52.6% | 1.70 | ~$28K/yr | 14.65% | Futures |
| Stairway to Heaven (Gold) | 31% | ~3.4 | N/A | ~1% per trade | Gold Futures |
| Simple MR SPY | 70% | N/A | ~8% CAGR | ~15% | Equities |
| Mean Reversion (2025 OOS) | 72% | N/A | +30.4% | 10.2% | Multi-market |
| Powell 10am NQ | 60.2% | 0.98 | Negative | N/A | NQ Futures |
| Stochastic Oscillator (X) | 77.7% | 2.58 | 0.68%/trade | N/A | N/A |
| Trend Rebalance Map (X) | 78.95% | 1.51 | +$511 in 19 trades | N/A | MNQ |

## Key Thees & Observations
1. **High WR ≠ High returns:** Stairway to Heaven (31% WR) likely has better risk-adjusted returns than the 70% WR mean reversion setups
2. **Execution realism is the #1 killer:** Multiple sources flag that backtest results (especially at close price) are unatainable live
3. **Mean reversion trending: stron out-formance in 2025,** buysideways markts
- **Regime detection is the new edge:** The difference between a 72% WR and a losing strategy is knowing WHEN to trade
5. **Al / autmation increasingly accesible:** Claude for backtesting, GPT-6 for quant screening, automated MES strategies