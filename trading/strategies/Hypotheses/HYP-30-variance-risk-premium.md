---
hypothesis_id: HYP-30
source: internal (structural risk-premia class — the VRP, second documented-persistent edge)
venue: deribit (options)
instruments: BTC + ETH ATM straddles (European-style, no early exercise)
horizon: straddle entry -> expiry (weekly to ~30d DTE)
signal: SELL ATM straddles to collect the variance risk premium (VRP = implied − realized)
timing_gate: vol-of-vol — enter in low/decaying vol regimes, EXIT/avoid vol-spike regimes (per skill "VRP with vol-of-vol timing")
data_dependencies:
  - options: Deribit History API (history.deribit.com, no token) — expired BTC/ETH option trades (2016+/2019+)
  - realized vol: Deribit get_historical_volatility + our own BTC/ETH spot (oracle/mark)
  - vol index: Deribit DVOL (get_volatility_index_data)
cost_hurdle_bps: realistic option bid-ask spread (wider than perp) + margin cost + adverse fill; maker where possible
counterparty: option buyers (hedgers + speculators) paying a premium for tail/convexity insurance
topic: structural (carry/risk-premia)
confidence: low-medium (strong prior — VRP is documented-persistent — but short-vol tail risk is the honest unknown)
has_quotes: false
tags: []
---
# HYP-30 — Variance Risk Premium (sell ATM vol) on BTC/ETH

## Motivation

The second documented-persistent structural edge after carry: the VRP. Option
buyers systematically overpay for tail protection (implied vol > realized vol
in expectation), so SELLING that insurance collects a premium. It is structurally
diversifying against the funding carry (vol-selling earns in calm/decaying vol,
carry earns in trending) — the two together are the start of an uncorrelated
risk-premia portfolio.

## Pre-registered operationalization (fixed)

- Signal: sell an ATM straddle on BTC/ETH, hold to expiry (weekly→~30d DTE).
- Edge: VRP = (premium collected at entry, in vol terms) minus (realized vol over
  the hold). Net-positive if implied systematically exceeds realized.
- Timing gate (vol-of-vol): enter only in low/decaying vol (DVOL below its own
  trailing band / not spiking); avoid/exit when vol is spiking — the short-vol
  tail lives exactly in vol-spike regimes.
- Cost: realistic option bid-ask spread + margin + adverse fill; report maker vs
  taker leg.
- Risk (the honest unknown): report the short-straddle TAIL explicitly — max
  drawdown, the vol-spike episodes, and whether the premium survives them. This
  is the load-bearing question, not the mean.

## Prior (recorded)

The VRP has a strong structural prior (it is the canonical risk-premium, the same
family as the carry that just validated). BUT short vol is short a hard tail: a
vol spike (the literal scenario crypto is prone to) can give back a year of
premium in days. The honest test is whether the premium, side-netted against the
tail + spreads, stays positive and survives vanilla robustness — not whether the
mean is positive, which is near-certain.

## Falsification / promotion

- Promote only if net premium (after spread + tail + margin) is positive AND
  robust (G4/G5) with the vol-of-vol gate honored. A premium that only survives
  by ignoring the tail, or that needs to sell at-the-spike, is not a tradeable VRP.

## Note

This is the second structural premia candidate, deliberately paired with the
carry for diversification. Data is FREE + DEEP (Deribit History API, no token).
The honest unknown is the tail, not the mean.