---
status: backtest_failed
source: web
edge_type: crypto_deleveraging_regime_breakout_asymmetry
composite_score: 64.0
confidence: medium
regime_fit: ['caution', 'neutral', 'risk_off']
created: 20260820
processed: 20260820
topic: research
has_quotes: false
tags: [crypto, onchain, deleveraging, positioning, breakout, regime, external]
---
# Edge Candidate: Crypto Post-Deleveraging Breakout Asymmetry

## Pipeline Result: BACKTEST FAILED (2026-08-20)

**Scanner:** `scanner_crypto_deleveraging_breakout.py` (STR-CDB-CRYPTO-DELEVERAGING-BREAKOUT)
**Phase 1A Results:**
- Total signals: 1,166 (210.1/year)
- Mean R: -0.032 (negative)
- Median R: -0.438 (median trade is a loss)
- Win rate: 36.1%
- p-value: 0.3337 (not significant)
- t-stat: -0.967
- Sub-periods positive: 0/3
- Classification: ❌ KILL (avg_r < KILL_AVG_R threshold)

**Analysis:**
The Bollinger-squeeze breakout strategy conditioned on a volatility-compression
regime gate does not produce a positive edge on the 35-asset Hyperliquid crypto
universe. The regime gate (median ATR% below 20th percentile of 180-day range
AND BTC ATR% below 20th percentile) is a proxy for leverage depletion — but
ATR compression captures low-volatility periods generally, not specifically
the "post-deleveraging, pre-flush" state described in the candidate.

Key issues:
1. The ATR-compression proxy detects ALL low-vol periods, not just post-
   deleveraging ones. Many low-vol crypto periods are accumulation/complacency,
   not the specific "leverage purged but no capitulation yet" state.
2. The Bollinger-squeeze breakout in low-vol crypto often produces false
   breakouts (the squeeze resolves in either direction without follow-through).
3. The chandelier trailing stop (2x ATR) may be too tight in crypto where
   2x ATR moves are common even in low-vol regimes.
4. True OI/funding data (the actual leverage signal) is not available
   historically — the candidate explicitly flagged this as a gap.

**What would change my view:** Access to historical aggregate OI data from
Hyperliquid would enable a proper leverage-depletion regime gate. The
hypothesis (post-deleveraging breakouts are directional) is sound but cannot
be tested without the actual OI data. The ATR proxy is insufficient.
# Edge Candidate: Crypto Post-Deleveraging Breakout Asymmetry

## Source
Web / on-chain research (Aug 2026) —
- **Galaxy Research, "State of Crypto Leverage Q2 2026" (Aug 17 2026):** Q2 was the first quarter since Q4 2022 in which onchain lending declined across *every* category (CeFi, DeFi, crypto-collateralized). Described as "orderly, measured deleveraging" — not a crash flush, but a clean regime shift. ETH OI declined more than BTC.
- **BlackRock (Aug 19 2026):** "Bitcoin has largely purged the froth that preceded the 50% drop from $126K." Positioning reached extreme levels at the Oct 2025 peak (futures OI >$90B, ~80% in offshore perps). BTC cycle low $58,642 (June 2026); now ~$63K.
- **CryptoSlate (Aug 16 2026):** "$48B Bitcoin leverage trap is about to trigger a massive forced exit the moment price boundaries break" — small positive funding on offshore perps exposes longs if price falls; large net-short among CME leveraged funds. Asymmetric setup.
- **Cointelegraph/BlackRock:** "Bitcoin's drawdown came WITHOUT a liquidation flush" — leverage is reduced but the capitulation cascade hasn't occurred. Rangebound $58K–$65K.
- **DeFi exploits Q2 record:** 99 hacks, $746M lost (Shattered.io, Aug 19 2026) — additional risk-off pressure within DeFi, TVL fragility.
- **BTC dominance 56.8%** (Aug 13 briefing): high dominance = risk-off within crypto.

## Signal
A **post-deleveraging, pre-flush positioning regime** in crypto. Leverage has been purged (OI halved from $90B→$48B, onchain lending down across all categories for the first time since Q4 2022) but price has NOT yet had its capitulation/breakout event — BTC is rangebound $58K–$65K with compressed volatility. Offshore perp funding is small-positive (longs still leveraged, exposed on a downside break) while CME funds are net-short (exposed on an upside break). This is a **trapped, low-leverage, compressed-volatility** state where the *next* directional break tends to be violent and **trend-following outperforms mean-reversion**, because the weak hands that mean-reversion profits from have already been removed.

The edge: when crypto leverage is depleted AND price volatility is compressed, switch crypto strategies from mean-reversion (which worked during the flush) to **breakout/trend-following**, and size up because the break is asymmetric.

## Hypothesis
After a broad-based leverage contraction (the Galaxy "every category down" signal), the remaining positioning is polarized (retail-long perps vs. fund-short CME). A volatility-compression breakout in this state resolves directionally rather than reverting, because there is no frothy leverage left to absorb the move on the mean-reverting side. Therefore a Bollinger-squeeze / ATR-contraction breakout strategy on the Hyperliquid crypto universe, *conditioned on a recent leverage-depletion regime*, delivers a materially higher win-rate and R than the same breakout strategy run unconditionally.

## Entry Rules
- **Regime gate (weekly check):** Crypto deleveraging regime is ACTIVE when:
  1. BTC futures OI proxy (or aggregate perp OI across the 35 Hyperliquid assets) is ≥ 30% below its 180-day high (leverage purged), AND
  2. BTC dominance ≥ 54% (risk-off within crypto), AND
  3. DeFi TVL trend flat/declining over prior 30 days
- **Breakout trigger (daily, within regime):** For each of the 35 crypto assets, enter long on a close > upper Bollinger Band (20, 2σ) after a squeeze (BB width ≤ 20th percentile of 120-day range); enter short on close < lower band after squeeze. ATR-based stop (1.5×ATR). 
- **Bias tilt:** Because offshore funding is small-positive (longs trapped) AND CME funds net-short, the *downside-break* leg may have higher expected R in the very near term — but the strategy is symmetric; let the breakout decide.

## Exit Rules
- Trail with 2×ATR chandelier exit, OR
- Exit on opposite-band touch, OR
- Regime gate turns OFF (leverage re-expands ≥ 20% from depletion low → mean-reversion strategies resume).
- Hard time-stop: 15 trading days if no >1R move develops.

## Score Breakdown
- Composite: 64.0
- Signal Strength: 14 (concurrent, multi-source: Galaxy + BlackRock + CryptoSlate all describe the same trapped-leverage state in the same week)
- Confidence: medium (15) — strong qualitative corroboration; medium because the OI/funding proxy from Hyperliquid needs validation and the "breakout vs mean-reversion" switch is regime-conditional
- Data Quality: 13 (Hyperliquid gives funding + perp data for 35 assets; OI proxy computable; BTC dominance/DeFi TVL need a cached free source — CoinGecko/DefiLlama public endpoints)
- Actionable: 12 (breakout scanner + regime gate is a clean extension of existing STR-F/STR-V breakout logic applied to crypto)
- Precedent: 10 (some_evidence — Q4 2022 post-FTX deleveraging produced a sharp trend-following regime in Q1 2023; analogous setup)

## Regime Fit
['caution', 'neutral', 'risk_off'] — the *crypto* sub-regime is risk-off/caution (deleveraging). The breakout strategy fires *within* this crypto risk-off state once volatility compresses. Suppress if crypto flips to outright 'risk_on' (leverage re-expands → mean-reversion retakes the edge). Distinct from the equity regime labels — this is a crypto-internal regime.

## Testability
✅ **Mostly testable with free data.** Hyperliquid provides funding rates and perp OHLC for 35 assets (engine already ingests LunarCrush/funding). BTC dominance + DeFi TVL available via DefiLlama/CoinGecko public endpoints (free, no key). The one gap: historical aggregate OI at the asset level — Hyperliquid exposes current OI; historical OI series may need the Hyperliquid public API historical endpoint or a cached daily snapshot started now. Backtest the breakout-on-squeeze strategy *conditioned* vs *unconditioned* on the regime gate over the 2159-day crypto history.

**Overlap with engine:** Engine has a funding-rate-extremes source and a crypto performance-dispersion source, and there are existing RWA/DeFi-TVL-divergence and BTC/ETH-ETF-rotation candidates. NONE frame the *aggregate leverage contraction as a regime gate that switches breakout vs mean-reversion*. This is a new regime-conditional strategy layer, not a duplicate TVL/flow signal.

## Recommended Pipeline Action
**PROMISING →** Two-step: (1) confirm the leverage-depletion regime gate is detectable from free data — start caching daily Hyperliquid aggregate OI + funding + BTC dominance + DeFi TVL now if not already cached. (2) Build `scanner_crypto_deleveraging_breakout.py`: Bollinger-squeeze breakout on 35 crypto assets, gated by the 3-condition leverage-depletion regime. Backtest conditioned vs. unconditioned win-rate/R over full crypto history. If the conditioned breakout shows ≥ 5pp higher win-rate and mean R > 0, proceed to walk-forward. Priority: high — the regime appears active *now* (Galaxy/BlackRock both flag it this week), so a live signal could be deployable within the cycle.
