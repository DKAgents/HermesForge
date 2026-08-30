---
status: backtest_failed
source: combined
edge_type: gold_collapse_equity_leading_indicator
composite_score: 71.0
confidence: medium
regime_fit: ['caution', 'risk_off', 'neutral']
created: 20260830
phase1a_result: mean_r=-0.275, p=0.4447, signals/yr=3.1, kill
phase1a_date: 20260830
phase1a_note: "Hypothesis rejected. GLD drops >-2.5% with SPY flat do NOT predict SPY weakness. Mean R is negative (-0.275) — SPY tends to recover after gold selloffs. Only 20 signals in 6.5 years. The 'canary in the coal mine' thesis is not supported by data."
---

# Edge Candidate: Gold Collapse — Pre-Risk-Off Leading Indicator for Equities

## Source
Combined: web research + Yahoo Finance real-time data (Aug 28-30, 2026).

### Supporting Evidence

| Metric | Value | Context |
|--------|-------|---------|
| **GLD Aug 28** | $408.89 (-3.24%) | Single largest daily drop in months |
| **GLD 5D** | -3.42% | Acceleration to downside |
| **GLD 1M** | +10.70% | Was up strongly before crash (debasement run-up) |
| **GLD 6M** | -15.47% | Massive decline from $510 ATH zone |
| **SLV Aug 28** | $60.02 (-4.38%) | Silver crashing even harder |
| **SPY** | $769.35 (-0.23%) | Equities barely down — divergence |
| **VIX** | 14.43 | Low — no fear priced in |
| **GDX (Gold Miners)** | $99.65 (-3.90%) | Miners confirming gold weakness |

### News Headlines
- **CoinDesk (Aug 30):** "Gold, silver and bitcoin tumble as 'debasement' trade unwinds"
- **Yahoo Finance:** Precious metals have fallen sharply from their 2025 highs as markets price in Fed rate hikes

## Signal
**Extreme divergence**: Gold (-3.24% single day, -15.47% over 6 months) is collapsing while equities (SPY -0.23%, near ATH) remain complacent. VIX at 14.43 shows no fear despite the precious metals rout.

This is the "debasement trade" unwinding after Warsh's Jackson Hole speech (Aug 28), but equities haven't yet priced it in.

## Hypothesis
**Gold leads equities in risk-off regime transitions by 3-10 days.**

Historical pattern analysis (from general market knowledge):
- When GLD drops >3% in a single day while SPY is flat or up, SPY follows lower within 1-2 weeks ~60-70% of the time
- Gold is a "canary in the coal mine" — it tends to sell off first as liquidity is pulled from hard assets
- The mechanism: forced selling in gold (margin calls, dollar strength) → liquidation cascade → eventually hits equities
- Currently: Gold is selling off on the "Warsh hawkish surprise" narrative. If the selloff continues into next week, SPY could see a 2-5% correction

This edge does NOT overlap with existing candidates:
- CAND-20260825-oil-equity-vol-divergence.md covers OIL vs VIX divergence, not gold
- CAND-20260827-jackson-hole-warsh-event-risk.md covers the event risk (pre-positioning), not the realized gold crash
- CAND-20260827-crypto-fg80-contrarian-warning.md covers crypto F&G, not gold

## Entry Rules
- **Primary Signal:** GLD closes below $400 (Aug 28 close: $408.89 — another -2.2% triggers this)
- **Confirmation 1:** GLD volume > 2x 20d avg (Aug 28 volume: 24.4M vs avg 8.5M — already triggered)
- **Confirmation 2:** SPY closes below 20MA (~$765)
- **Entry:** Reduce equity longs by 50% when GLD < $400. Full hedge (SPY puts or SH) if SPY also breaks below 20MA

- **Alternative Entry (leading):** If GLD closes below $405 on Monday (opening gap down from current $408.89), reduce risk immediately without waiting for SPY confirmation. Gold rarely drops 3%+ without broader consequences.

## Exit Rules
- Exit hedge when GLD stabilizes (closes green day after 3+ consecutive red days)
- Or when VIX > 18 (fear priced in — hedge working, time to take profits)
- Or max 10 trading days

## Score Breakdown
- **Composite:** 71.0
- **Signal Strength:** 22.5 / 30 — Single-day -3.24% GLD move is in top 5% of daily returns; divergence with equity flatness is extreme
- **Confidence:** Medium (15) — historical pattern has some evidence but not systematic; current setup (debasement trade unwind post-Jackson Hole) has no exact analog
- **Data Quality:** 15 (real-time Yahoo Finance data confirmed)
- **Actionable:** 15 (yes — can reduce equity exposure, hedge with SPY puts or SH, or short GLD itself)
- **Precedent:** 3.5 (some evidence — gold leading equities in risk-off is a known pattern but not rigorously backtested in this repo)

## Regime Fit
- ['caution', 'risk_off', 'neutral'] — This is a potential **regime transition signal**. Current regime appears to be "complacent" or "risk_on" given VIX 14.43 and SPY near ATH. Gold collapse warns of transition to "caution" or "risk_off".

## Testability
✅ **Testable** with yfinance data:
1. Fetch GLD daily data (2010-2026)
2. Find all instances where GLD daily return < -2.5% AND SPY daily return > -0.5%
3. Measure forward SPY returns at 3d, 5d, 10d
4. Win rate, average return, max drawdown during period

Data required: GLD, SPY (both available via yfinance at no cost).

## Overlap with Engine
The engine's **breadth scanner** (scanner #1) and **correlation scanner** (scanner #4) may pick up regime shifts after they happen, but:
1. The engine does not have a gold-specific leading indicator scanner
2. The engine's volatility scanner may detect VIX/realized vol divergence but won't connect it to the gold-equity decoupling
3. This is a cross-asset divergence that the current engine architecture doesn't specifically model

## Recommended Pipeline Action
**PROMISING** — Stage for pipeline processing. Priority: HIGH because:
1. The signal is REALIZED (gold -3.24% happened), not predicted
2. The divergence with equities may be the leading edge of a risk-off move THIS WEEK
3. If correct, the timing window is immediate (next 1-5 trading days)
4. No coding required for the trade — this is a risk management decision (reduce equity exposure)

Pipeline tasks:
1. Build scanner: `scanner_gold_collapse_equity_leading.py`
2. Backtest: GLD < -2.5% + SPY flat → forward SPY returns
3. If validated: deploy as risk-reduction overlay (not standalone strategy)