---
type: postmortem
source: postmortem
strategy_id: STR-Q-liquidity-sweep
strategy_class: liquidity-sweep
signal_class: ict-smc
gate: G3
gate_subject: execution-realism
status: failed
date: 2026-11-02
tags: [postmortem, feedback, generation, ict-smc]
confidence: high
topic: general
has_quotes: false
---
# STR-Q Liquidity-Sweep — Post-Mortem

Died at **G3 (execution realism)**. The bar-level hostile-fill re-simulation (on the real production `hostile_fills_strq.py` rules — 3-bar confirmation lag, fill at triggering-bar open, worst-print stops, both-side taker fees) collapsed the paper-layer "+1,568 R" into a net **−8,447.07 R across 5,309 scored trades** (avg −1.59 R/trade, t = −41.2, 24.7% win rate). The root reason is that the sweep-detector's apparent edge was priced entirely off "fill at the exact reversal close" — i.e., buy the bottom of the sweep — which is unattainable: a real fill requires the price to trade *back through* the entry, which for a tight-stop sweep (0.1–0.3% risk) is already on the way to the stop, and the 3-bar lag lets the favorable reversal slip before a fill is even possible. The informational content of the stop-hunt/sweep signal is real but strictly smaller than the transaction cost of actually trading it — the strategy is not weakly-negative noise, it is strongly and statistically significant negative. For a variant to pass, the sweep signal would need predictive magnitude that survives a realistic trade-through fill: a net-positive R under hostile fills (not merely under frictionless or sweep-close fills), which no liquidity-sweep/stop-hunt ICT-SMC variant has yet demonstrated; this class is now hard-blocked at intake (US-191) pending any such pre-registered argument.