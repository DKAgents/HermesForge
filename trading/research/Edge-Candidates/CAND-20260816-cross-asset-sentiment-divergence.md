---
status: backtest_failed
source: web
edge_type: cross_asset_sentiment_divergence
composite_score: 63.0
confidence: medium
regime_fit: ['neutral', 'caution']
created: 20260816
topic: research
has_quotes: false
tags: [sentiment, crypto, divergence, external]
---
# Edge Candidate: Cross-Asset Sentiment Divergence (Crypto Fear 35 vs Equity Greed 62)

## Source
Web research — CryptoRank (Crypto F&G at 36-37, Aug 14-15), CNN Fear & Greed (Equity F&G at 62, Aug 11-13), CoinStats (BTC daily analysis Aug 16)

## Signal
- Crypto Fear & Greed Index: 35-37 (Fear territory, down from 40+ in prior weeks)
- Equity Fear & Greed Index: 62 (Greed)
- Divergence: 25-27 point spread (equities greedy, crypto fearful)
- BTC dominance: 56.8% (risk-off within crypto)
- BTC ETF outflows: $325M (Aug 12-13), ETH ETF inflows: $7.4M
- Retail crypto sentiment reads "extreme fear" near 40 per Saylor series reference
- BTC funding rate: 0.0014%/8h (~1.54% annualized) — very low, no long squeeze risk

## Hypothesis
The 25+ point sentiment divergence between equities (Greed) and crypto (Fear) represents a cross-asset positioning asymmetry. Historically:
1. When equity sentiment is greedy while crypto is in fear, crypto tends to mean-revert upward within 2-4 weeks as capital rotates from overheated equity markets to undervalued crypto
2. The low funding rate confirms no overcrowded long positioning — contrarian bullish setup
3. BTC at $63.5K is 48% below its ATH ($126K), creating an asymmetric risk/reward for long crypto positions
4. ETH ETF inflows while BTC ETFs see outflows suggests smart money is already rotating into ETH

This is NOT the same as the engine's BNB sentiment divergence (which is a single-token signal). This is a macro cross-asset sentiment regime signal.

## Entry Rules
- **Strategy A (BTC Long):** Long BTC when crypto F&G < 40 AND equity F&G > 55 AND BTC funding rate < 0.005%/8h. Enter on any day, scale in over 5 days.
- **Strategy B (ETH Rotation):** Long ETH/BTC ratio when BTC ETFs show net outflows AND ETH ETFs show net inflows on the same day. This captures the smart money rotation.
- **Strategy C (Crypto Basket Long):** Long top 5 crypto by 30d momentum when crypto F&G < 35. Exit when F&G > 55.

## Exit Rules
- **Strategy A:** Exit when crypto F&G > 55 or BTC drops below $58K (stop loss).
- **Strategy B:** Exit when ETH/BTC ratio rises 10% or ETF flows reverse.
- **Strategy C:** Exit when F&G > 55 or individual stop at -8%.

## Score Breakdown
- Composite: 63.0
- Signal Strength: 13.0 (27-point divergence is significant)
- Confidence: medium (15 pts) — sentiment divergence is documented but cross-asset version is less tested
- Data Quality: 15 (daily F&G from CNN/CoinMarketCap, ETF flows from public sources)
- Actionable: 15
- Precedent: 5 (novel — cross-asset sentiment divergence is not widely documented)

## Regime Fit
['neutral', 'caution'] — divergence appears when regimes are transitioning

## Testability
✅ Fully testable: Crypto F&G from alternative.me API (free), equity F&G from CNN, BTC/ETH prices from Hyperliquid or yfinance. ETF flows from SoSoValue/Farside (free).

## Overlap with Engine
Engine found BNB social sentiment divergence (score 48.6, low confidence). This is a BROADER macro signal — cross-asset sentiment regime, not single-token. Complementary but distinct.

## Recommended Pipeline Action
PROMISING — proceed to backtest crypto basket long strategy when F&G divergence > 20 points. The cross-asset angle is novel and testable. Medium confidence due to limited historical precedent for cross-asset sentiment divergence specifically.

## Pipeline Processing Log (2026-08-16, HermesForge Autonomous Pipeline)

**Scope note (data limitation):** The full cross-asset divergence requires
historical *equity* Fear & Greed (CNN), which is not historically cached in this
repo. The testable core — the candidate's own Strategy C ("Long top-N crypto by
30d momentum when crypto F&G < 35; exit when F&G > 55 or -8% stop") — was backtested
as a faithful proxy. The cross-asset divergence overlay remains a future
enhancement pending equity-F&G history.

**Scanner coded:** `scripts/validation/scanners/scanner_crypto_fg_contrarian.py`
- Batch/cross-sectional: on any day crypto F&G < 35 (Fear), ranks the crypto
  universe by 30-day return, enters long the top 5 not already held. Exits on
  F&G >= 55, -8% stop, +2R target (16%), or 21-bar time stop.

**Phase 1A backtest** (`run_phase1a.py --scanner ... --crypto --json`):
- total_signals: 2494 | signals_per_year: 470.0 | mean_r: **-0.019** | median_r: -1.047
- win_rate: 38.9% | sub_positive: 2/3 | p_value: **0.6184** | t_stat: -0.50
- ADR-004 classification: ❌ KILL (avg_r < 0.2); friction flag: true

**Verdict: BACKTEST_FAILED.** mean_r <= 0 (−0.019) with no statistical edge
(p=0.62). The crypto-F&G-contrarian gate alone does not add positive expectancy:
most trades hit the -8% stop before the 16% target (median R = −1.05). Buying
crypto in Fear purely on a 30d-momentum rank is not a standalone edge
frictionless, and would be worse after costs. Not advanced to walk-forward.

**Future work:** re-test the full cross-asset version (crypto F&G < 40 AND
equity F&G > 55 AND low funding) once historical equity Fear & Greed and
funding-rate series are cached — the divergence/asymmetry signal may carry
edge that the single-asset F&G gate does not.

**Survivorship caveat:** crypto universe is current Hyperliquid markets;
delisted coins (MATIC, FTM, etc.) were already filtered by the loader, which
can flatter cross-sectional momentum.

