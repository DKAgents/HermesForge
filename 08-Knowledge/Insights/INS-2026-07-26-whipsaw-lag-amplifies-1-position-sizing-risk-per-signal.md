---
type: insight
date: 2026-07-26
actionability: 3
connection_type: adds_condition
domains: [edge-conditions, indicators, rules]
sources: ["N039-double-crossover-method-10-and-50-day-combination-for-stocks", "E020-double-crossover-reduces-whipsaws-vs-single-average", "EN028-10-and-50-day-moving-average-crossover"]
seed_id: diversification_position_limit
tags: [insight, discovery, knowledge-evolution]
topic: knowledge
confidence: high
has_quotes: false
source: unknown
---
# Whipsaw Lag Amplifies 1% Position Sizing Risk Per Signal

## Discovery Summary

E020-double-crossover-reduces-whipsaws-vs-single-average explicitly establishes that the 10/50 double crossover (documented in both N039 and EN028) lags the market more than a single MA, producing later entries and exits. If a HermesForge 1% position sizing rule is applied per signal, the known lag means the trader is systematically entering after a portion of the move is already consumed — compressing the reward side of the risk/reward ratio on every trade. Murphy's implied 10-15% per-market capital limit (not present in the retrieved notes) would cap total market exposure, but the 1% per-signal rule interacts with lag by ensuring each lagged entry risks only 1% of capital on a potentially reduced move. The two rules do not conflict outright but the lag condition means the effective risk/reward of each 1% bet is structurally worse than it would be with a faster signal.

## Trading Implication

When using the 10/50 crossover, a trader applying 1% position sizing should explicitly widen profit targets or tighten stops to account for the confirmed entry lag (per E020-Murphy quote), rather than using the same reward parameters as a faster single-MA system; failure to adjust means the 1% risk is taken on a structurally inferior entry point every time.

## Supporting Notes

- [[N039-double-crossover-method-10-and-50-day-combination-for-stocks]]
- [[E020-double-crossover-reduces-whipsaws-vs-single-average]]
- [[EN028-10-and-50-day-moving-average-crossover]]

## Connection Type

**adds_condition** — Actionability score: 3/5

## Related
- [[RG035-combining-technical-factors-with-money-management-for-stop-p]] — See RG035-combining-technical-factors-with-money-management-for-stop-p for stop placement rules that offset lag-compressed reward

- [[POSITION_SIZING]] — See POSITION_SIZING for the standard 1% rule that this lag compromises

- [[R226-equity-curve-management-increase-commitments-after-drawdowns]] — See equity curve management rule for timing of size increases after drawdowns

- [[RG034-handling-winning-streaks-and-position-sizing]] — See RG034-handling-winning-streaks-and-position-sizing for why increasing size after wins is especially dangerous with lagging systems.

- [[C239-money-management-as-survival-mechanism]] — See C239-money-management-as-survival-mechanism for why this lag amplification threatens survival.

## Related Notes
- [[R226-equity-curve-management-increase-commitments-after-drawdowns|Equity Curve Management: Increase Commitments After Drawdowns]]
