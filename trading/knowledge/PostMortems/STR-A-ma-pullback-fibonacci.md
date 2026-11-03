---
type: postmortem
source: postmortem
strategy_id: STR-A-ma-pullback-fibonacci
strategy_class: ma-pullback-fibonacci
signal_class: retail-ta
gate: G0
gate_subject: intake
status: deprecated
date: 2026-11-02
tags: [postmortem, feedback, generation, retail-ta]
confidence: high
topic: general
has_quotes: false
---
# STR-A MA-Pullback-Fibonacci — Post-Mortem

Deprecated at **G0/intake**, and it never reached any real gate. The root reason is a governance artifact, not a measured edge: STR-A was promoted to Active (2026-09-20) with **no backtest ever run and no completed paper trade**, and was simultaneously listed as KILLED in the regime selector — two registries that flatly disagreed, with the strategy carrying no evaluation whatsoever (its own file records "backtest: not started; paper trade log: not started"). The fill-model audit re-graded it "n/a — promoted with zero evidence." Its signal class (moving-average pullback + Fibonacci retracement) is retail-TA and is now hard-blocked at intake by the US-191 signal-class gate. For any variant to pass, it would first have to be re-specified as a systematic (non-retail-TA) mechanism and survive an actual G0 cost/leakage/fill evaluation before any promotion claim — there is no shortcut past the missing evidence that caused this failure.