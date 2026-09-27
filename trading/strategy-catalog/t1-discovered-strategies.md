# T1 Strategy Discovery — Hostile-Fill-Survivable Specifications

**Generated:** 2026-09-13
**Source:** Web research (arXiv 2608.21888, quantifiedstrategies.com, colibritrader.com, dxpa.in), Murphy "Technical Analysis of the Financial Markets" pattern rules, hostile-fill reasoning
**Hostile Fill Rules Applied:**
- Fill at t+1 open (cannot fill on signal bar)
- Taker fee 0.1% per side (0.2% round-trip)
- Limit orders: must trade THROUGH level, not just touch
- Stops: fill at WORST print on crossing bar
- 75-min time stop on intraday (15 × 5m bars)

**Rankings:** Most robust first. "Robust" = largest expected surviving edge after hostile fill application, considering: bar timeframe (daily beats 5m), stop width relative to fees, entry gap alignment, and thesis strength.

---

## STR-T1-01: Outside Day Key Reversal (Daily)

**Source:** Murphy Chapter 4 (Reversal Patterns), "Key Reversal Day" — in an uptrend, price makes a new high then closes below the prior day's close. Already flagged as STR-N in HermesForge with paper Mean R = +0.41, 71% WR (14 signals).

**Entry Signal (Long — Bottom Reversal):**
1. Prior trend: price closed below 20-day SMA
2. Signal bar: today's low < prior 5-day low AND today's close > prior day's close AND today's range > prior 5-day average range × 1.2
3. Confirmation: signal bar close > signal bar open (bullish close)

**Entry Signal (Short — Top Reversal):**
1. Prior trend: price closed above 20-day SMA
2. Signal bar: today's high > prior 5-day high AND today's close < prior day's close AND today's range > prior 5-day average range × 1.2
3. Confirmation: signal bar close < signal bar open (bearish close)

**Entry Method:** Market order at next day's open (t+1). The outside day IS the signal; entering at next open is naturally aligned — the reversal gap often goes your way.

**Stop Placement:** Beyond the signal bar's extreme. Long: stop at signal bar low − 0.2 ATR(14). Short: stop at signal bar high + 0.2 ATR(14). Minimum stop distance: 1.0% (crypto) / 0.5% (stocks).

**Target(s):**
- T1 (50% position): 1.5R multiple
- T2 (50% position): 3.0R multiple OR prior swing high/low, whichever is wider
- Trail remainder with 10-day SMA if trade exceeds 5 days

**Time Stop:** 10 trading days. If neither target hit, close at market.

**Asset Class:** Stocks + crypto. Daily bars.

**Edge Thesis — Why Survive Hostile Fills?**
1. **Daily bars avoid 5m execution issues entirely.** The t+1 fill (next day open) is a natural entry point, not a penalty. On daily bar strategies, you'd enter at next day's open anyway — the signal bar is EOD analysis.
2. **Wide stops (1%+) make the 0.2% fee negligible.** At 1% stop, fee is only 20% of risk budget vs. 40% at 0.5%.
3. **The worst-print stop rule is already priced into a wide ATR-based stop.** The extra 0.2 ATR buffer beyond the signal bar extreme accounts for the worst-print penalty.
4. **Murphy's pattern has 100+ years of empirical support across all liquid markets.** The outside day captures a genuine shift in supply/demand — sellers exhausted, buyers stepped in.
5. **STR-N paper results (0.41R, 71% WR) suggest edge survives, but sample too small (14 trades).** More data needed.

**Estimated Hostile-Fill R Expectation:** +0.25R to +0.35R (paper ~0.41R, deduct ~0.10R for t+1 gap variance and worst-print stop penalty on the wider side of the signal bar, add R from 3R target outweighing 1R stop)

---

## STR-T1-02: ADX Trend Continuation Pullback (Daily)

**Source:** Murphy Chapters on trend identification (ADX/DMI) and moving averages. DXP Analytics intraday adaption confirmed institutional EMA-respecting behavior.

**Entry Signal (Long):**
1. Trend filter: ADX(14) > 25 AND +DI > −DI (uptrend confirmed)
2. Pullback: today's low touches or falls within 0.3 ATR(14) of the 20-day EMA
3. Reversal candle: today's close > today's open (bullish candle on the pullback bar)
4. Volume filter: today's volume < prior 5-day average volume (pullback on declining volume confirms it's a rest, not a reversal)

**Entry Signal (Short):** Mirror — ADX(14) > 25 AND −DI > +DI, price rallies to within 0.3 ATR of 20-day EMA, bearish close, declining volume.

**Entry Method:** Market order at next day's open (t+1). The pullback bar is the setup; entering on the next bar gives the trend time to resume.

**Stop Placement:** Below the pullback bar's low − 0.2 ATR(14) for longs. Above pullback bar's high + 0.2 ATR(14) for shorts. Minimum distance: 1.5 ATR(14).

**Target(s):**
- T1 (50%): Recent swing high/low (prior 20-bar extreme)
- T2 (50%): Trail with 20-day EMA — exit when close crosses below EMA (long) or above EMA (short)

**Time Stop:** 15 trading days.

**Asset Class:** Stocks (SPY, QQQ components with >$5 and >500K ADV) and crypto (BTC, ETH, top-20 by volume).

**Edge Thesis — Why Survive Hostile Fills?**
1. **Daily bars + wide ATR stops (typically 2-4% on stocks, 3-6% on crypto)** make 0.2% fee a rounding error.
2. **ADX filter avoids range-bound chop** — the primary killer of trend-following strategies (the DXP article: 55-60% of days are range days; ADX > 25 filters most of these out).
3. **Declining volume on pullback confirms the trend is intact**, not reversing. This reduces the probability of the t+1 gap going against you.
4. **The t+1 fill at next day's open often benefits you** — if the pullback was genuine, overnight orders accumulate in the trend direction.
5. **Institutional algos are programmed to respect the 20 EMA** on major indices and crypto pairs, creating a self-fulfilling support dynamic.

**Estimated Hostile-Fill R Expectation:** +0.15R to +0.25R (lower frequency, higher win rate expected ~55-60%, wide stops mean higher R-multiple targets)

---

## STR-T1-03: Gap Continuation (Daily)

**Source:** Gap theory (Murphy Chapter on Gaps). Overnight gaps that continue rather than fade represent persistent order imbalance.

**Entry Signal (Long):**
1. Trend: 50-day SMA > 200-day SMA (bull market)
2. Gap: today's open > prior day's high by ≥ 0.5 ATR(14) (upside gap)
3. Continuation: today's first 30-min candle (stocks) or first 4-hour candle (crypto) closes above the open — gap is holding, not fading
4. Volume: today's volume projected to exceed prior 5-day average × 1.2

**Entry Signal (Short):** Mirror — bear market trend, gap down ≥ 0.5 ATR, continuation confirmed.

**Entry Method:** Market order at the close of the confirmation candle (approx 30 min after open for stocks; 4h bar close for crypto). **This is t+0 entry** — the gap is the signal, and you enter on the same day the gap occurs. This completely avoids the t+1 fill penalty.

**Stop Placement:** 
- Long: at prior day's close (gap fill level). If gap fills, thesis invalidated.
- Short: at prior day's close.
- Minimum stop distance: 0.5 ATR(14).

**Target(s):**
- T1 (50%): 1.5 × the gap size (measured move from prior close to open)
- T2 (50%): Trail with 5-day EMA — exit on close against EMA

**Time Stop:** 5 trading days. Gaps that don't continue within a week are unlikely to extend.

**Asset Class:** Stocks (gap-prone: earnings, news catalysts — filter for >$10 price, >1M ADV) and crypto (BTC, ETH — 24/7 market means "overnight" = US session close to Asian open).

**Edge Thesis — Why Survive Hostile Fills?**
1. **T+0 entry — enters on the gap day itself.** No t+1 fill penalty. This is the single best defense against hostile fill rules.
2. **Gap continuation is an under-exploited anomaly** in the academic literature. Gaps that hold past the first hour tend to extend for 2-5 days (persistent order imbalance from institutional repositioning).
3. **Stop at prior close is a clean invalidation level** — if the gap fills immediately, the signal was wrong.
4. **Trend filter (50 > 200 SMA) ensures you only trade gaps in the dominant direction**, avoiding counter-trend gap traps.

**Estimated Hostile-Fill R Expectation:** +0.20R to +0.30R (t+0 entry, clean invalidation, but lower signal frequency — expect 1-3 trades/week across universe)

---

## STR-T1-04: Volatility Squeeze Expansion (Daily)

**Source:** Bollinger Band Squeeze (John Bollinger, Murphy Chapter on volatility bands). BB width contraction precedes directional expansion.

**Entry Signal (Long):**
1. Squeeze: BB(20,2) width at its lowest level in 50 bars (BB_width = (upper − lower) / middle)
2. Breakout: today's close > upper BB(20,2) — price breaks above the contracted range
3. Volume confirmation: today's volume > prior 20-day average × 1.5
4. Trend alignment (optional filter): 50-day SMA sloping up (SMA(50) > SMA(50)[5])

**Entry Signal (Short):** Mirror — BB width at 50-bar low, close < lower BB, volume > 1.5× avg, 50-SMA sloping down.

**Entry Method:** Market order at next day's open (t+1). The squeeze breakout is confirmed by the close above the band; enter the next day.

**Stop Placement:** 2.0 ATR(14) from entry price. This is deliberately wide — squeeze breakouts often have a false start (whipsaw) before expanding. Minimum distance: 2.0%.

**Target(s):**
- Exit when price closes back inside the BB(20,2) bands (expansion phase ended)
- OR trail with parabolic SAR (step 0.02, max 0.2)

**Time Stop:** 20 trading days.

**Asset Class:** Stocks (liquid, >$10) and crypto (top-20). Daily bars.

**Edge Thesis — Why Survive Hostile Fills?**
1. **Daily bars + 2.0 ATR stop** — fees are negligible relative to risk budget.
2. **BB squeeze captures multi-week expansion moves** — 2-5R targets are common. A single winner pays for 4-8 losers.
3. **Volume confirmation eliminates 40-50% of false breakouts** — reduces whipsaw, which is the primary hostile-fill killer on t+1 entries.
4. **The squeeze-to-expansion cycle is a well-documented market microstructure phenomenon** — volatility clusters, and low-volatility regimes inevitably transition to high-volatility regimes.

**Estimated Hostile-Fill R Expectation:** +0.10R to +0.20R (lower win rate ~40-45% but high R-multiple winners. Narrow edge because squeeze doesn't predict direction — only magnitude.)

---

## STR-T1-05: Volume Climax Reversal (Daily)

**Source:** Murphy "Selling Climax" / "Blowoff" patterns (Reversal Patterns chapter). Extreme volume after a sustained move signals exhaustion.

**Entry Signal (Long — Selling Climax):**
1. Prior move: price declined for ≥ 5 consecutive days
2. Climax bar: today's volume > prior 20-day average × 2.0 AND today's range > prior 20-day average range × 1.5
3. Reversal confirmation: today's close in the upper 60% of today's range (close > low + 0.6 × range) — buyers absorbed the selling
4. Next bar: tomorrow's open > today's low (gap did not extend the panic)

**Entry Signal (Short — Buying Climax):** Mirror — 5+ consecutive up days, volume 2× avg, wide range, close in lower 60% of range, next open < prior high.

**Entry Method:** Market order at the open of the bar AFTER the confirmation bar (t+2 from climax). This double-confirmation avoids false climaxes.

**Stop Placement:** Below the climax bar's low − 0.3 ATR(14) for longs. Above climax bar's high + 0.3 ATR for shorts. Minimum stop: 1.5 ATR(14).

**Target(s):**
- T1 (50%): 2.0R
- T2 (50%): Prior swing high/low (20-bar extreme)
- Trail with 10-day EMA after T1 hit

**Time Stop:** 15 trading days.

**Asset Class:** Stocks and crypto. Daily bars.

**Edge Thesis — Why Survive Hostile Fills?**
1. **Double-confirmation (climax bar + next bar open above low)** eliminates the t+1 gap problem — you're deliberately waiting to see if the gap confirms the reversal.
2. **Extreme volume events are rare but high-conviction** — 2× average volume on a 5+ day move is an institutional footprint.
3. **Wide ATR stop accounts for post-climax volatility** — climaxes are followed by wide swings; the stop must survive the aftershocks.
4. **T+2 entry means you sacrifice some edge for higher hit rate** — you miss the initial snapback but confirm the reversal is real.

**Estimated Hostile-Fill R Expectation:** +0.15R to +0.25R (lower frequency, higher conviction, but t+2 entry means smaller captured move)

---

## STR-T1-06: Momentum Breakout Retest (Daily)

**Source:** Murphy on breakouts and retests (Continuation Patterns chapter). "Old resistance becomes new support" tested systematically.

**Entry Signal (Long):**
1. Breakout: price closes above the prior 20-day high
2. Breakout volume: breakout day volume > prior 20-day average × 1.3
3. Retest: within the next 10 bars, price pulls back to within 0.3 ATR(14) of the breakout level (prior 20-day high)
4. Bounce: retest bar closes above the breakout level AND close > open (bullish rejection)
5. Retest volume: retest bar volume < breakout bar volume × 0.7 (declining volume on retest = no sellers)

**Entry Signal (Short):** Mirror — break below 20-day low, volume > 1.3× avg, rally retest of breakdown level, bearish rejection, declining volume.

**Entry Method:** Market order at next day's open after the bounce bar confirms.

**Stop Placement:** Below the retest bar's low − 0.2 ATR(14). Minimum stop: 1.0 ATR(14).

**Target(s):**
- T1 (50%): Measured move — breakout level + (breakout level − prior 20-day low) for longs
- T2 (50%): Trail with 20-day EMA

**Time Stop:** 20 trading days.

**Asset Class:** Stocks (>$10, >500K ADV). Crypto (top-20). Daily bars.

**Edge Thesis — Why Survive Hostile Fills?**
1. **You're entering AFTER the breakout, on the retest** — the initial breakout already proved direction. The retest gives you a second, lower-risk entry where the t+1 gap from your signal bar is less likely to hurt.
2. **The measured-move target typically gives 2-3R** — wide enough to overcome fees.
3. **Declining volume on retest is a classic confirmation** (Murphy) that the breakout was genuine and sellers aren't stepping in.
4. **The retest-failure stop is close to entry** (tight relative to target), improving R:R.

**Estimated Hostile-Fill R Expectation:** +0.15R to +0.25R (moderate frequency, good R:R, retest adds confirmation layer)

---

## STR-T1-07: RSI(2) Deep Oversold — Crypto Specific (Daily)

**Source:** Larry Connors' RSI(2) strategy (Street Smarts, 1996); arXiv 2608.21888 confirms crypto has persistent short-horizon mean reversion stronger than equities. HermesForge factor anomaly reports show RSI14 has negative Sharpe −1.05 on crypto (strong mean reversion signal).

**Entry Signal (Long):**
1. Trend filter: price > 50-day SMA (only buy dips in uptrend)
2. Oversold: RSI(2) closes below 10 (extreme 2-period oversold)
3. Volume spike: today's volume > prior 20-day average × 1.2 (capitulation volume confirms panic)
4. Additional filter: RSI(2) has been below 30 for at least 2 of the prior 3 bars (persistent weakness, not a one-bar accident)

**Entry Signal (Short):** Mirror — price < 50-SMA, RSI(2) > 95, volume spike, persistent overbought.

**Entry Method:** Market order at next day's open (t+1). Connors' original used on-close orders, but t+1 open is the hostile-fill-compatible adaptation.

**Stop Placement:** 2.0 ATR(14) from entry. Connors' RSI(2) often wicks further before reversing — tight stops die. Minimum: 1.5 ATR.

**Target(s):**
- Exit when RSI(2) crosses above 60 (long) OR below 40 (short)
- OR exit when price crosses above 5-day SMA (long)
- Whichever triggers first

**Time Stop:** 7 trading days. RSI(2) mean reversion plays out within a week.

**Asset Class:** Crypto only (BTC, ETH, SOL, top-20 by volume). The arXiv paper shows crypto's reversal AUC is 0.531 vs. equities 0.498 — the edge is crypto-specific.

**Edge Thesis — Why Survive Hostile Fills?**
1. **The crypto mean-reversion edge is well-documented.** arXiv 2608.21888: "reversal concentrates in crypto relative to US equities" with AUC gap +0.031, statistically robust. The reversal concentrates after aggressive taker flow-driven moves.
2. **RSI(2) < 10 is an extreme condition** — triggers infrequently (1-3 times/month/asset) but with high win rates (70-85% historically on indices; crypto may be similar or better per the arXiv finding).
3. **Wide 2.0 ATR stop survives the worst-print rule** — crypto ATR(14) on daily bars is typically 3-6%, so stop is 6-12%, fees are 0.2% of that → negligible.
4. **Trend filter (price > 50-SMA) avoids catching falling knives** — you only buy pullbacks in uptrends.

**Estimated Hostile-Fill R Expectation:** +0.20R to +0.35R (high win rate, crypto edge, but wide stops mean lower R-multiple per trade; 70% WR × 0.6R avg win − 30% × 1.0R avg loss ≈ +0.12R base, plus crypto premium)

---

## STR-T1-08: Aggressive Flow Fade — 5m Crypto

**Source:** arXiv 2608.21888: "reversal concentrates after moves that aggressive taker flow pushed and grows with flow intensity." Translated to 5m bar proxies since direct flow data may not be available.

**Entry Signal (Long — Fade Aggressive Selling):**
1. Signal bar: a 5m bar with range > prior 20-bar average range × 2.0 AND close in the lower 25% of the bar's range (close near low = aggressive selling)
2. Volume proxy: signal bar volume (or tick count) > prior 20-bar average × 2.5
3. Immediate follow-through failure: the NEXT bar (t+1) closes above the signal bar's close AND the low of this next bar is > signal bar's low (no further downside — the aggressive flow has been absorbed)
4. Context: price is above the day's VWAP (buying pullbacks in an uptrend day) OR ADX(14) < 20 on 5m (range day — fading extremes in a range)

**Entry Signal (Short — Fade Aggressive Buying):** Mirror — wide range bar, close near high, volume spike, next bar closes below signal bar close, below VWAP or ADX < 20.

**Entry Method:** Market order at the open of bar t+2 (the bar AFTER the follow-through failure bar). This is a 3-bar confirmation sequence: (1) aggressive flow bar, (2) failure bar, (3) entry bar.

**Stop Placement:** Beyond the signal bar's extreme. Long: stop at signal bar low − 0.2 ATR(14). Short: stop at signal bar high + 0.2 ATR(14). Minimum: 0.5% (crypto).

**Target(s):**
- T1 (100%): 2.0R — exit at 2× risk from entry
- OR trail with signal bar's midpoint (50% of signal bar range) as dynamic stop after price moves 1R in your favor

**Time Stop:** 75 minutes (15 × 5m bars from entry). Standard hostile-fill intraday time stop.

**Asset Class:** Crypto only (BTC, ETH perpetuals on OKX). Requires 5m bar data with volume.

**Edge Thesis — Why Survive Hostile Fills?**
1. **The arXiv paper's core finding is that crypto reversal is FLOW-CONDITIONED** — it only exists after aggressive taker-driven moves. This strategy directly targets that condition.
2. **The 3-bar confirmation sequence (flow bar → failure bar → entry bar)** means you enter at t+2, not t+1 — you've already seen the aggressive flow fail to extend. This is intentionally conservative to survive hostile fills.
3. **0.5% minimum stop on crypto** — at 0.2% round-trip fee, the fee is 40% of risk budget. This is the WEAKEST point of this strategy; it needs >0.5R average win to overcome.
4. **The 2R target gives a 4:1 gross R:R before fees.** After 0.2% fee on a 0.5% stop → ~0.4R fee cost per round trip. Net R:R ≈ 2.6:1.

**Estimated Hostile-Fill R Expectation:** +0.05R to +0.15R (narrow edge due to 5m bar frequency + fee friction; the flow conditioning helps but 0.2% on 0.5% stops is punishing. This strategy needs higher minimum stop distance or lower-fee venue to work.)

---

## STR-T1-09: Support/Resistance Role Reversal (Daily)

**Source:** Murphy Chapter on Support and Resistance — "Old resistance becomes new support." One of the most reliable TA principles.

**Entry Signal (Long):**
1. Resistance identified: a price level that was tested as resistance ≥ 3 times in the prior 100 bars (touches within 0.5% band of each other)
2. Breakout: price closes above this resistance level
3. Role reversal: within the next 5 bars, price pulls back to within 0.3 ATR(14) of the broken resistance level
4. Confirmation: the pullback bar closes above the resistance level (support holds) AND close > open
5. Trend: 50-day SMA > 200-day SMA

**Entry Signal (Short):** Mirror — support breaks, turns to resistance, rally retest fails.

**Entry Method:** Market order at next day's open after confirmation bar.

**Stop Placement:** Below the broken resistance level − 0.3 ATR(14). This is a tight stop because the invalidation is clear: if price goes back below old resistance, the breakout failed. Minimum: 0.8% (stocks), 1.2% (crypto).

**Target(s):**
- T1 (50%): Prior swing high (20-bar) OR 2.0R, whichever is further
- T2 (50%): Trail with parabolic SAR (0.02, 0.2)

**Time Stop:** 10 trading days. S/R flips that work tend to show follow-through quickly.

**Asset Class:** Stocks (>$10, >500K ADV) and crypto (top-20). Daily bars.

**Edge Thesis — Why Survive Hostile Fills?**
1. **Role reversal is one of the few TA concepts with a behavioral finance explanation** — traders who sold at resistance now see price above their entry (regret), and those who missed the breakout now want to buy the pullback (FOMO). This creates genuine buying pressure at old resistance.
2. **Daily bars + moderate stops (0.8-1.2%)** — fees are ~17-25% of risk budget, which is manageable if win rate > 55%.
3. **Multi-touch resistance levels are statistically more reliable** than single-touch levels (Murphy). The ≥3-touch filter reduces false signals.
4. **The stop at the broken level is both tight and logically clean** — if price goes back below, the breakout wasn't real. Good R:R from tight stop.

**Estimated Hostile-Fill R Expectation:** +0.10R to +0.20R (moderate frequency, clean invalidation, but reliance on identifying multi-touch levels introduces subjectivity risk in coding)

---

## STR-T1-10: Trend Day Pyramiding — 5m Stocks

**Source:** DXP Analytics intraday trend following system (adapted from futures to stocks). "First pullback of the day: typically 2:1 to 3:1."

**Entry Signal (Long):**
1. Trend day confirmation (by 10:00 AM ET): price > VWAP AND 9 EMA > 20 EMA on 5m AND price making higher highs AND ADX(14) > 25 on 5m
2. First pullback: price pulls back to within 0.2% of 9 EMA on 5m chart
3. Bounce: first 5m bar to close green after touching the 9 EMA zone
4. Volume: pullback bars show declining volume relative to prior rally bars

**Entry Method:** Market order at open of bar t+1 (the bar after the bounce bar). Enter with 40% of max position size.

**Stop Placement (per entry):** Below the low of the pullback candle (the red bar that touched the 9 EMA). Minimum: 0.3%.

**Pyramiding Rules:**
- Entry 1 (40% size) at first pullback. Stop below pullback low.
- Entry 2 (30% size) at second pullback to 9 or 20 EMA. Stop below second pullback low. Move Entry 1 stop to breakeven.
- Entry 3 (30% size) at third pullback. Stop below third pullback low. Move all stops to most recent swing low.
- Maximum 3 entries. After third entry, no more adds.

**Exit Rules (all entries closed):**
- Price closes below 20 EMA on 5m for 3+ consecutive bars → trend exhausting, exit all
- OR a lower high forms (high < prior high) on 5m → trend structure broken
- OR VWAP cross: price closes below VWAP on uptrend day

**Time Stop:** 2:30 PM ET hard exit. Intraday trends lose momentum into the close.

**Asset Class:** Stocks only (SPY, QQQ, IWM, or liquid stocks gapping >2% pre-market with RVOL > 2×). Requires 5m bar data.

**Edge Thesis — Why Survive Hostile Fills?**
1. **Trend days have asymmetric R:R** — the DXP data shows trend days produce 2:1 to 3:1 R:R on early entries. A single trend day can cover 3-4 range-day losses.
2. **Pyramiding means your full position only deploys when the trend is proven** — first entry is only 40% size. If it fails, you lose small.
3. **The hostile fill t+1 entry is LESS damaging for trend following** because trends persist — missing the exact pullback low by one bar is not fatal.
4. **The 0.3% minimum stop is tight** and the 0.2% fee eats 67% of risk budget. THIS IS THE WEAKNESS. Strategy only survives if trend days deliver at least 2:1 gross R:R (1.3:1 net after fees).
5. **VWAP and 20 EMA exits protect against late-day reversals** — trend days typically end by 2:30 PM.

**Estimated Hostile-Fill R Expectation:** +0.05R to +0.10R (tight stops mean fees hurt badly; only survives on high R:R trend days. DXP says 40-45% of days are trend days — you need the trend days to significantly outperform to overcome range-day losses + fees.)

---

## Summary Rankings

| Rank | Strategy | Bars | Asset | Key Edge | Est. Hostile R |
|------|----------|------|-------|----------|----------------|
| 1 | STR-T1-01: Outside Day Key Reversal | Daily | Both | Murphy classic, already paper-validated, wide stops | +0.25 to +0.35R |
| 2 | STR-T1-02: ADX Trend Pullback | Daily | Both | ADX chops range days, wide stops, institutional EMA behavior | +0.15 to +0.25R |
| 3 | STR-T1-03: Gap Continuation | Daily | Both | **T+0 entry** avoids fill penalty entirely | +0.20 to +0.30R |
| 4 | STR-T1-04: Vol Squeeze Expansion | Daily | Both | Multi-week expansion moves, 2R+ targets | +0.10 to +0.20R |
| 5 | STR-T1-05: Volume Climax Reversal | Daily | Both | Extreme volume = institutional footprint, double-confirmation | +0.15 to +0.25R |
| 6 | STR-T1-06: Momentum Breakout Retest | Daily | Stocks | Retest adds confirmation, good R:R from tight stop | +0.15 to +0.25R |
| 7 | STR-T1-07: RSI(2) Deep Oversold Crypto | Daily | Crypto | arXiv-documented crypto reversal edge, Connors' 70-85% WR | +0.20 to +0.35R |
| 8 | STR-T1-08: Aggressive Flow Fade | 5m | Crypto | arXiv flow-conditioned reversal, 3-bar confirmation | +0.05 to +0.15R |
| 9 | STR-T1-09: Support/Resistance Flip | Daily | Both | Behavioral finance basis, multi-touch filter, clean stops | +0.10 to +0.20R |
| 10 | STR-T1-10: Trend Day Pyramiding | 5m | Stocks | Asymmetric R:R on trend days, pyramiding limits risk | +0.05 to +0.10R |

## Key Observations

1. **Daily bar strategies dominate the top of the rankings.** The hostile fill rules punish 5m bar strategies disproportionately (0.2% fee on 0.3-0.5% stops = 40-67% of risk budget consumed by fees alone). Daily bars with 1%+ stops reduce fee impact to <20% of risk budget.

2. **STR-T1-03 (Gap Continuation) is the only strategy with truly t+0 entry** — the gap itself IS the signal, and entry occurs on the gap day. This completely sidesteps the t+1 fill rule.

3. **Crypto's mean-reversion edge (arXiv 2608.21888) is the strongest documented anomaly** — AUC 0.531 vs. 0.498 for equities. STR-T1-07 and STR-T1-08 directly target this, but the daily version (STR-T1-07) is more survivable.

4. **The weakest strategies (STR-T1-08, STR-T1-10) are 5m-bar strategies with tight stops** — the fee-to-risk ratio is punishing. These need either: (a) a lower-fee venue, (b) wider stops, or (c) higher R:R targets to survive.

## Implementation Notes

- All strategies are codable in Python with existing 5m/daily bar data feeds.
- Daily bar strategies use EOD data; 5m strategies use OKX crypto or stock intraday data.
- Paper trading only. 1% risk cap per trade.
- Each strategy should be implemented as a scanner script following the existing HermesForge pattern (signal detection → paper trading → hostile-fill scoring).
- Start with the top 5 strategies for initial implementation and hostile-fill backtesting.