---
status: backtest_failed
source: combined
edge_type: btc_dominance_cycle_inflection
composite_score: 56.0
confidence: low
regime_fit: ['neutral', 'risk_on', 'caution']
created: 20260830
phase1a_result: mean_r=-0.493, p=0.0000, signals/yr=56.5, kill
phase1a_date: 20260830
phase1a_note: "Hypothesis (H2) rejected. BTC dominance extremes (proxied by BTC/ETH ratio > 90th percentile + BTC rally > 15% in 30d) do NOT predict BTC weakness. Mean R is strongly negative (-0.493, p=0.0) — the momentum continues. 106 signals suggest this is a robust anti-signal: when BTC is dominant, shorting it loses money. Trend continuation, not reversal. H1 (alt rotation) may still be worth testing separately."
topic: research
has_quotes: false
tags: []
---
# Edge Candidate: BTC Dominance 59.5% — Cycle Inflection Point

## Source
Combined: CoinMarketCap, Yahoo Finance, CoinDesk (Aug 28-30, 2026).

### Supporting Evidence

| Metric | Value | Context |
|--------|-------|---------|
| **BTC Dominance** | 59.5% | Near cycle highs — highest since late 2022 |
| **BTC 1M** | +21.75% | Strong short-term rally |
| **BTC YTD** | -9.95% | Still negative for 2026 |
| **BTC 1Y** | -27.58% | Down from 2025 ATH above $126K |
| **ETH** | $2,479 (+1.17%) | Underperforming BTC |
| **ETH Dominance** | 11.2% | Multi-year low |
| **Altcoin Season Index** | 31/100 | Extremely low — strongly NOT alt season |
| **F&G (Crypto)** | 76/100 (Greed) | Elevated — not extreme fear |
| **Total Crypto Market Cap** | $2.64T | Modest recovery |
| **BTC 52wk Range** | $57,747 - $126,198 | Current $78,797 is in middle-upper range |
| **ETH/BTC Ratio** | ~0.031 | ETH massively underperforming |

### News Headlines
- **CryptoQuant:** "Michael Saylor should halt Strategy's bitcoin buys" — cash cushion thinned from 7 years to 14 months coverage
- **CoinDesk:** "Bitcoin OGs aren't selling as aggressively as they did above $100,000" — long-term holders holding
- **10x Research:** "Bitcoin could fall to $55,000 before finding a bottom"
- **CoinDesk (Aug 30):** "Gold, silver and bitcoin tumble as 'debasement' trade unwinds"

## Signal
**BTC Dominance is at 59.5%** — a level historically associated with major cycle turning points:

1. **Late 2020 (~60%):** BTC.D peaked → began declining → massive alt season (DeFi summer, NFT boom) for 18 months
2. **Early 2021 (~55%):** BTC.D peaked at ~55% before dropping to 40% through Nov 2021 cycle top
3. **Late 2022 (~42%):** BTC.D bottomed at 42% in bear market → BTC.D climbing as capital fled alts for BTC
4. **Jun 2023 (~52%):** BTC.D plateaued then continued climbing through 2024-25

The current 59.5% is a structurally extreme level. The question is: **is this a cycle top signal or a new normalization?**

Two competing hypotheses:

**H1: Peak Dominance = Imminent Alt Season (Bullish for ETH/SOL)**
- BTC dominance historically tops near 60% before a multi-month rotation into alts
- The mechanism: BTC leads the rally, establishes the trend, then capital rotates to alts (higher beta)
- If total cap expands from $2.64T during alt season, ETH could 2-3x from here
- Entry: Buy ETH, wait for BTC.D to drop below 58%

**H2: Peak Dominance = Cycle Top (Bearish for Everything)**
- In bear markets, BTC.D also rises (capital flees alts and consolidates in BTC)
- F&G at 76 (Greed) suggests euphoria, not the start of a risk-on rotation
- The "debasement trade unwinding" (gold crashing, BTC selling post-Jackson Hole) suggests risk appetite is fading
- If total cap contracts from $2.64T, BTC.D staying at 59.5% means both BTC and alts fall, but alts fall harder
- Entry: Short alts (ETH, SOL), long BTC relative to total portfolio

## Hypothesis
**BTC Dominance > 58% combined with F&G > 70 (Greed) has historically signaled a near-term market top, not an alt season beginning.**

The evidence:
- F&G at 76 while BTC.D is at 59.5% is unusual in both directions (greed + BTC dominance)
- The debasement trade (gold + BTC) is unwinding simultaneously — suggesting the "BTC as digital gold" narrative is fading
- CryptoQuant's warning about Strategy's BTC buys suggests institutional flows are stretched
- 10x Research calling for $55K BTC suggests even bullish institutions see downside

## Entry Rules
- **Primary Signal:** BTC.D closes above 60% for 2 consecutive days — activate caution mode
- **Confirmation:** F&G stays above 70 while BTC.D stays above 58%
- **Entry (H2):** Reduce total crypto exposure by 50%. Do not add to ETH or alt positions until BTC.D drops below 55%
- **Exit (H2 — Bearish):** Close remaining positions if BTC drops below $70K (major support zone)

- **Contrarian Entry (H1 — Bullish):** Buy ETH when BTC.D drops below 57% with 2 consecutive days of decline. Target: ETH/BTC ratio returns to 0.05+

## Exit Rules
- For H2 (bearish): Re-enter when BTC.D drops below 55% AND total cap shows expansion (indicating new capital entering, not just rotation)
- For H1 (bullish): Exit alt positions when BTC.D drops below 50% (overshoot) or F&G > 90 (euphoria)

## Score Breakdown
- **Composite:** 56.0
- **Signal Strength:** 15.0 / 30 — BTC.D at 59.5% is extreme but there's no consensus on whether it's bullish or bearish
- **Confidence:** Low (5) — two competing hypotheses with near-opposite implications; the regime context (debasement trade unwinding, gold crashing) weakly favors H2 (caution/bearish) but not decisively
- **Data Quality:** 15 (real-time CoinMarketCap data confirmed)
- **Actionable:** 15 (yes — can reduce crypto exposure, shift to cash)
- **Precedent:** 8 (some evidence — historical BTC.D peaks have been both tops and rotation beginnings depending on broader macro context)

## Regime Fit
- ['neutral', 'risk_on', 'caution'] — This edge spans multiple potential regimes:
  - If H1 (alt season begins) → risk_on
  - If H2 (top in) → caution/risk_off

## Testability
⚠️ **Partially testable** with yfinance + existing data:
1. BTC.D data available from CoinMarketCap (not on yfinance natively but can be calculated from BTC-USD and total market cap)
2. Test H1: All instances where BTC.D was > 58% with F&G > 70 → forward ETH/BTC ratio over 1m, 3m
3. Test H2: Same setup → forward BTC total return over 1m, 3m
4. The sample size is limited (BTC.D > 58% has occurred only 4-5 times since 2017)

Data required: BTC-USD, ETH-USD, total crypto market cap (free from CoinMarketCap), F&G index (free from alternative.me)

## Overlap with Engine
The engine's **sector rotation scanner** (#3) compares alts to BTC but doesn't model BTC.D directly. The **Fear & Greed scanner** (#10) tracks sentiment but doesn't combine it with dominance. This edge is a **combination** that neither scanner alone captures.

## Recommended Pipeline Action
**SPECULATIVE** — Stage for pipeline as low-priority research project.

Given the competing hypotheses:
1. Do NOT deploy as a production strategy until further research
2. Build research scanner: `scanner_btc_dominance_inflection.py`
3. Phase 1A test: single-variable (just BTC.D > 58%)
4. Phase 1B test: two-variable (BTC.D > 58% + F&G > 70)
5. If one hypothesis strongly outperforms, deploy accordingly

Priority: LOW — this is a structural observation, not an immediate trading setup. The setup is not urgent because BTC.D changes slowly (over weeks/months, not days).

## Risk Note
This is the LOWEST confidence candidate of this batch. The two competing hypotheses have opposite implications and roughly equal historical support. Do NOT trade this based on conviction — wait for the hypothesis test results.