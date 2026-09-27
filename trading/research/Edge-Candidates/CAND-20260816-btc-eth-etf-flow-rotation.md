---
status: rejected
source: web
edge_type: btc_eth_etf_flow_rotation
composite_score: 54.0
confidence: medium
regime_fit: ['neutral', 'caution']
created: 20260816
topic: research
has_quotes: false
tags: [crypto, etf-flows, rotation, external]
---
# Edge Candidate: BTC ETF Outflow / ETH ETF Inflow Rotation Signal

## Source
Web research — KuCoin News (Aug 13), Yellow.com (Aug 12), CryptoRank (Aug 14), CryptoPotato (Aug 15)

## Signal
- BTC ETF net outflows: $325M (week of Aug 10-15) and $61.1M on Aug 12 alone
- ETH ETF net inflows: $7.4M on Aug 12, with Ethereum outperforming BTC for first time in 2026
- BTC dominance: 56.8% (high, but ETH starting to gain)
- ETH price: ~$1,896 (struggling below $1,900 but ETF flows turning positive)
- BTC price: ~$63,558 (rangebound, 48% below ATH)
- ETH/BTC ratio starting to bottom after extended underperformance

## Hypothesis
When BTC ETFs show sustained net outflows while ETH ETFs show net inflows:
1. Institutional capital is rotating from BTC to ETH — a smart money signal
2. This typically precedes ETH outperformance by 5-15% over 2-4 weeks
3. The rotation often marks a regime shift from "BTC as safe haven" to "risk-on crypto" 
4. ETH at $1,896 with positive ETF inflows is a divergence — price lagging while capital flows in
5. The ETH weekly death cross (printed in July 2026) may be a false signal if ETF inflows sustain

This is a flow-based signal, not a sentiment signal. It captures what institutions are actually doing with capital, not what they're saying.

## Entry Rules
- **Strategy A (ETH/BTC Long):** Long ETH/BTC ratio when: (a) BTC ETF net outflows > $50M on any day, (b) ETH ETF net inflows > $5M on same day, (c) ETH/BTC ratio above 10-day MA
- **Strategy B (ETH Long):** Long ETH when ETH ETF inflows > $10M for 3 consecutive days AND ETH price above 20MA
- **Strategy C (BTC Short):** Short BTC when BTC ETF outflows > $100M for 3 consecutive days AND BTC below 50MA

## Exit Rules
- **Strategy A:** Exit when ETH/BTC ratio rises 8% or ETF flows reverse (BTC inflows, ETH outflows)
- **Strategy B:** Exit at 15% profit or when ETH ETF flows turn negative for 2 consecutive days
- **Strategy C:** Exit at 5% profit or when BTC ETF flows turn positive

## Score Breakdown
- Composite: 54.0
- Signal Strength: 9.0 ($325M outflow vs $7.4M inflow is notable but not extreme)
- Confidence: medium (15 pts) — ETF flow signals are increasingly tracked but still emerging
- Data Quality: 15 (daily ETF flow data from SoSoValue/Farside, free)
- Actionable: 15
- Precedent: 5 (novel — ETH ETFs are new, limited historical data for flow rotation)

## Regime Fit
['neutral', 'caution'] — rotation signals appear during regime transitions

## Testability
✅ Fully testable: ETF flow data from SoSoValue (free, daily), ETH/BTC prices from Hyperliquid or yfinance. Can backtest daily flow signals vs forward returns. Limited by ETH ETF history (launched mid-2025).

## Overlap with Engine
Engine does NOT scan ETF flows. This is entirely new data source. The engine's crypto scanners focus on funding rates, sentiment, and performance dispersion, not institutional flow data.

## Recommended Pipeline Action
PROMISING — proceed to backtest ETH/BTC ratio long strategy triggered by ETF flow divergence. The signal is novel and captures institutional positioning directly. Medium confidence due to limited ETH ETF history (~13 months), but the logic is sound and data is freely available.

## Pipeline Rejection (2026-08-23)
**Decision:** REJECT at Stage 1 (Read & Critique)

**Rationale:** The hypothesis requires daily ETF flow data (BTC ETF net outflows, ETH ETF net
inflows) from SoSoValue, Farside Investors, or similar sources. While the data is freely
available, it is not integrated into our backtest pipeline.

**Issues:**
- No ETF flow data feed exists in `fetch_data.py` or `fetch_crypto_data.py`
- OHLCV data alone (BTC-USD, ETH-USD) cannot test ETF flow divergence signals
- The candidate's three strategies (ETH/BTC long, ETH long, BTC short) all depend on flow thresholds
- ETH ETF history is only ~13 months (launched mid-2025), limiting statistical power even if data were available

**Recommendation:** This is the most promising of the three evaluated candidates. Build an
ETF flow data fetcher (`fetch_etf_flows.py`) using SoSoValue/Farside free APIs, then re-stage.
The hypothesis is well-formed with clear entry/exit rules and institutional logic. Priority:
MEDIUM — re-evaluate once the data pipeline is extended.
