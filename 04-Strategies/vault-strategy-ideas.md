# Vault Strategy Idea Inventory — Research Sweep

**Generated:** 2026-09-13  
**Sources:** Murphy book (1,257 indexed notes), HermesForge vault (2 research reports), Insights (8 notes), Edge Candidates (49 files), Scanners (37 existing)  
**Context:** Hostile fill modeling (t+1 entry, 0.2% round-trip costs, worst-print stops, 75-min intraday time stop) has killed every paper-trading edge so far. Strategies must survive these conditions.

---

## Ranked Strategy Ideas

Rank | Strategy Concept | Source | Style | Rules Detail | Hostile Survivability
---|---|---|---|---|---
**1** | **40-60% Pullback Entry (Triple Confluence)** | Murphy EN068, EN004, R026; Insights INS-2026-09-05, INS-2026-08-21 | Swing | **Entry:** Buy when price retraces 40-60% of prior swing in uptrend (trend confirmed by EMA50 slope). Target 38% zone for strong trends, 62% for weak trends. **Stop:** Below prior swing low (no tighter than 1 ATR). **Target:** Prior swing high or 2:1 R. **Filter:** RSI > 30 (not oversold divergence). **Confirmation:** 2-day close beyond trendline (R012). | **High** — Wide stops (swing-low based, >2% on daily bars), t+1 entry is forgiving on daily, trend-following reduces mean-reversion whipsaw risk. Partially overlaps with STR-A (NO EDGE) but that used MA pullback without retracement zone specificity.
**2** | **Trendline Pullback + 3% Price Filter** | Murphy EN004, R010, R012 | Swing | **Entry:** In uptrend, buy when price touches up-trendline (3+ touches) and bounces. **Trendline validity:** 2-day close confirmation + 3% price penetration filter for break only. **Stop:** Below trendline − 1 ATR. **Target:** Channel upper line (EX005) or 3:1 R. | **High** — Daily bars, structural support zones, t+1 fill at trendline bounce means you enter at next bar (often still favorable). 3% filter prevents false breaks triggering exits.
**3** | **4-Week Rule (Donchian Breakout)** | Murphy EN030, EN031, R313, R207 | Swing | **Entry Long:** Price closes above highest close of 4 prior calendar weeks. **Entry Short:** Price closes below lowest close of 4 prior calendar weeks. **Stop:** 1 ATR or opposite 4-week extreme. **Exit:** Reverse signal. Already has `scanner_ae_4week_rule.py` — no validation results in any report. | **Medium-High** — Simple, well-known, t+1 entry on weekly highs isn't punishing (you either get continuation or false breakout). Needs volume filter to reduce whipsaws. Not yet tested under hostile fills.
**4** | **RSI Failure Swing (Not Simple OB/OS)** | Murphy N061, EX011 | Swing / Intraday | **Entry Short:** RSI > 70, then RSI peak fails to exceed prior peak, then breaks below prior trough. **Entry Long:** RSI < 30, fails to make new low, breaks above prior peak. **Stop:** Recent swing high/low. **Target:** Next support/resistance or 2:1 R. Different from STR-E (RSI Mean Reversion — NO EDGE), which used simple overbought/oversold. | **Medium** — RSI failure swings are higher-quality divergence signals than simple OB/OS. Daily bars avoid t+1 slippage issues. Pattern is rarer (fewer signals, higher quality).
**5** | **Flag/Pennant Half-Mast Continuation** | Murphy R070, N040, N041, N152, N136 | Swing | **Entry:** Breakout above flag/pennant upper boundary on expanding volume (volume > 20-day avg). **Pre-condition:** Prior sharp move (flagpole) of minimum 10%. Flag duration 1-3 weeks. **Stop:** Below flag lower boundary. **Target:** Flagpole height projected from breakout (half-mast rule). **Volume filter:** Contraction during formation, expansion on breakout (R058). | **Medium** — Continuation patterns survive better than reversal patterns under hostile fills. The measured move target gives strong R:R. Daily bars mean t+1 gap is manageable. Volume filter reduces false breakouts.
**6** | **Ascending Triangle Breakout (Volume-Confirmed)** | Murphy N033, N036, EN012 | Swing | **Entry:** Breakout above flat upper resistance on close, with volume expansion. Rising lower trendline (3+ touches). **Stop:** Below triangle lower boundary or midpoint of pattern. **Target:** Triangle height projected from breakout point. **Filter:** Triangle should form over 1-3 months. | **Medium** — Classic bullish pattern with clear stop/target. Daily bars, so t+1 entry is fine. Volume confirmation reduces false breakouts. Pattern is infrequent (few signals, needs large universe).
**7** | **MACD Divergence + Trend Filter (Refine STR-B)** | Murphy N062, EN043, R138 | Swing | STR-B is LIVE (Mean R=1.00, Sharpe 0.61, p=0.21) but marginal significance. **Enhancement:** Add trend filter (only trade signals aligned with EMA50 direction — R138), add volume confirmation on divergence completion, use RSI failure swing as co-confirmation. This turns a marginal edge into a high-conviction setup. | **Medium-High** — Building on existing LIVE strategy, not starting from scratch. Trend filter should improve signal quality. p=0.21 suggests the raw edge exists but is noisy.
**8** | **Head & Shoulders Neckline Break (Aggressive Entry)** | Murphy N014, N142, EN009, EN010 | Swing | Scanner `scanner_t_head_shoulders.py` exists but no validation results. **Entry:** Break below/across neckline on close with volume expansion. **Aggressive entry:** Buy on return move to neckline after breakout (EN011). **Stop:** Above right shoulder (for top) or below head (for bottom). **Target:** Head-to-neckline distance projected from breakout. | **Medium-Low** — Pattern is well-known, many false signals. Return-move entry improves price but risks missing the move. Daily bars help with t+1 but the pattern itself has high failure rate in modern markets. Volume filter critical.
**9** | **Dark Cloud Cover / Piercing Line (2-Candle Reversal)** | Murphy N077, N078 | Swing | **Short Entry:** After uptrend, Day 1 is long white candle, Day 2 opens above Day 1 high but closes below Day 1 midpoint. **Long Entry:** After downtrend, Day 1 is long black candle, Day 2 opens at new low but closes above Day 1 midpoint. **Stop:** Above Day 2 high (short) / below Day 2 low (long). **Target:** Prior swing. **Filter:** Must be in established trend (not range). | **Low-Medium** — 2-bar patterns are frequent but noisy. t+1 entry on Day 3 may miss the initial reversal thrust. Hostile fills at worst-print for stops is a concern. Better suited as confirmation for other setups.
**10** | **Shooting Star / Hammer Reversal** | Murphy N171, N076 | Swing | **Short Entry:** After uptrend, candle with small body at lower end, long upper shadow (≥2× body). **Long Entry:** After downtrend, candle with small body at upper end, long lower shadow (≥2× body). **Stop:** Above/below shadow extreme. **Target:** Prior support/resistance. **Filter:** Volume > average on reversal candle. | **Low** — Single-candle patterns are the noisiest. Hostile fills kill these in intraday; on daily bars, the t+1 gap is punishing (the initial reversal move already happened). Best used as a filter, not a standalone entry.
**11** | **Outside Day Key Reversal (STR-N Revival)** | Murphy N004; Strategy Revival Report | Swing | STR-N showed Mean R=0.41, p=0.064, 71% hit rate on 14 signals. **Entry:** Day's high exceeds prior day's high AND low exceeds prior day's low, closing opposite to trend direction. Combined with heavy volume. **Stop:** 50% of outside day range. **Target:** Prior swing extreme. | **Low-Medium** — FRAGILE EDGE. Only 14 signals. High mean R but wide confidence interval. Needs walk-forward validation. Hostile fills are punishing because outside days are volatile — t+1 entry may already be deep into the reversal.
**12** | **Rectangle Range Trading + Breakout Reversal** | Murphy R073, EN018 | Swing | **Range phase:** Buy at rectangle support, sell at resistance with tight stops. **Breakout phase:** Reverse last losing trade, follow the breakout. **Stop:** 1% beyond range boundary. **Target:** Rectangle height projected. | **Medium** — Range-trading entry at extremes gives good R:R, tight stops. But hostile fill worst-print rule can turn a 1% stop into a 3% loss if the break is violent. t+1 for reversal entry is fine.
**13** | **Double Top/Bottom with Volume Filter** | Murphy N147, N130, N052 | Swing | Scanner `scanner_u_double_top_bottom.py` exists — no results. **Entry:** Break of middle trough/peak after second top/bottom attempt. **Volume:** Heavier on first peak, lighter on second, spike on breakdown. **Stop:** Above second peak (top) / below second bottom. **Target:** Pattern height projected. | **Medium-Low** — Well-known pattern with moderate reliability. t+1 fill after breakdown confirmation may leave substantial ground already covered. Volume filter helps.
**14** | **Wedge Reversal (Falling/Rising)** | Murphy N045; scanner_ag_wedge.py | Swing | Scanner exists, no results. **Entry Short:** Rising wedge breakdown (converging lines sloping up, break below lower line). **Entry Long:** Falling wedge breakout (converging lines sloping down, break above upper line). **Stop:** Opposite wedge boundary. **Target:** Wedge base height projected. | **Medium** — Wedges have good predictive power but are slow to form and infrequent. Daily bars, so t+1 is fine. Volume contraction during formation + expansion on breakout is key.
**15** | **Bollinger Band Squeeze → Expansion (Refine STR-F)** | Murphy EX010; STR-F results (NO EDGE) | Swing | STR-F showed NO EDGE (53% WR, Mean R=-0.07). **Refinement:** Don't trade the squeeze → breakout direction. Instead, use BB contraction as a *regime filter* — when BB width < 20th percentile, reduce position size or stay flat. When BB expands, directional signals have higher probability. | **Low** — This is a meta-filter, not a standalone strategy. STR-F already tested. Value is as an overlay to other strategies, not a signal generator.

---

## Already-Working Strategies (Don't Duplicate)

Strategy | Status | Mean R | Sharpe | Notes
---|---|---|---|---
STR-B (MACD Divergence) | LIVE | 1.00 | 0.61 | p=0.21, marginal confidence
STR-I (Adaptive Trend) | LIVE | 0.54 | 1.19-1.20 | p=0.01, best live strategy
STR-P (Cross-Sectional) | WATCH | -0.05 | -0.13 | Negative edge, monitoring
STR-L (ATR Contraction) | WATCH | 0.00 | 0.00 | No signals yet
STR-SKEWP (Predicted Skewness) | WATCH | +0.046 | — | Tiny edge, friction-flagged

---

## Factor Anomalies Worth Exploring (from Weekly Research)

Factor | Asset | Sharpe | p-value | Implication
---|---|---|---|---
RSI14 (inverse) | Stocks | -0.94 | 0.01 | Overbought stocks mean-revert; strong anomaly
REV1 (inverse) | Stocks | -0.86 | 0.02 | 1-day reversal; combine with RSI for dual-confirmation entry
LOWVOL (inverse) | Stocks | -0.85 | 0.02 | Low-vol stocks underperform; short low-vol, long high-vol
RSI14 (inverse) | Crypto | -1.05 | 0.002 | Even stronger in crypto; mean reversion at extremes
MOM12_1 × LOWVOL (interaction) | Crypto | +0.58 | 0.09 | Only positive candidate in crypto; needs validation

**Key takeaway:** Inverse-RSI (short overbought stocks/crypto) is the strongest single-factor signal across both asset classes. This is distinct from STR-E (RSI Mean Reversion on long side only — NO EDGE).

---

## Murphy Patterns with Scanners but No Validation Results

Scanner | Pattern | Status
---|---|---
scanner_t_head_shoulders.py | Head & Shoulders | No validation in reports
scanner_u_double_top_bottom.py | Double Top/Bottom | No validation in reports
scanner_aa_williams_r.py | Williams %R | No validation in reports
scanner_ab_obv_divergence.py | OBV Divergence | No validation in reports
scanner_ac_cci.py | CCI signals | No validation in reports
scanner_ad_keltner.py | Keltner Channels | No validation in reports
scanner_ae_4week_rule.py | 4-Week Donchian | No validation in reports
scanner_ag_wedge.py | Falling/Rising Wedge | No validation in reports
scanner_ai_seasonal.py | Seasonality | No validation in reports
scanner_aj_intermarket.py | Intermarket analysis | No validation in reports
scanner_x_parabolic_sar.py | Parabolic SAR | No validation in reports
scanner_s_elliott_wave.py | Elliott Wave | No validation in reports
scanner_r_alligator.py | Alligator | No validation in reports

These 13 scanners have code written but none appear in the weekly research reports, suggesting they haven't been through the full Phase 1A → walk-forward → paper trading pipeline yet.

---

## Recommendations

### Immediate (lowest hanging fruit)
1. **Run hostile-fill validation on 4-Week Rule** (scanner_ae) — simple, well-documented, survives hostile fills on paper
2. **Refine STR-B (MACD Divergence)** with trend filter + RSI failure swing co-confirmation
3. **Explore inverse-RSI factor anomaly** — strongest signal across both assets, not yet in any live strategy

### Medium (requires new scanner code)
4. **40-60% Pullback with Triple Confluence** — new code needed, combines Dow/Fib/Murphy frameworks
5. **Flag/Pennant Half-Mast** — continuation pattern, clear rules, needs volume filter
6. **RSI Failure Swing** — different from simple RSI strategies already killed

### Meta
7. **Validate 13 untested scanners** — these have working code. Run Phase 1A backtests to see which survive before writing new scanners.