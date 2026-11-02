---
type: postmortem
source: postmortem
strategy_id: STR-funding-carry-directional
strategy_class: funding-carry
signal_class: systematic
gate: G3
gate_subject: execution-realism
status: failed
date: 2026-11-02
tags: [postmortem, feedback, generation, funding-carry]
confidence: high
---

# Funding Carry (Directional) — Post-Mortem

Died at **G3 (execution realism)**. On real Hyperliquid mark data the directional short/long funding-carries produced a tiny funding flow that was wiped out **20–39× over** by the directional hard stop whenever it fired: at λ = 0.25/0.50/1.00 the 2%-stop price-loss-to-funding ratios were **38.81× / 29.65× / 20.14×**, every λ failing G3 (real R −0.26 / −0.32 / −0.20). The root reason is structural: naked directional carry forces you to absorb the full directional price variance to harvest an interest flow (~11%/yr HL floor) that is an order of magnitude smaller — the funding yield is real but the *directional* form is a leveraged beta position in disguise, not a carry. For a variant to pass it must remove the directional exposure: the delta-neutral long-spot / short-perp construction is the only fix, and it is currently **blocked by the absence of a liquid Hyperliquid spot leg** — the only executable subset (BTC/ETH, ~+0.4–0.6 R net) still needs a real spot hedge or a beta-hedged overlay, and the λ-directional gate correctly rejects ~all naked entries regardless.