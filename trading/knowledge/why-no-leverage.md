---
type: reference
topic: leverage
tags: [leverage, risk, expectancy, friction, gauntlet]
created: 2026-11-02
source: human Q+A
confidence: high
has_quotes: false
---
# Why no leverage (reference)

## Core principle

Leverage is a **linear multiplier on both P&L and risk**. It cannot change the
sign of net expectancy — a strategy that is net-negative after costs stays
net-negative, it just burns the account L-times faster. The edge/friction ratio
(and therefore Sharpe / risk-adjusted quality) is **invariant to leverage**.

## Why it doesn't rescue retail TA

- Chart-pattern / retail-TA gross edge (0.08–0.22 R) sits *below* realistic
  friction (0.1–0.3 R taker + slippage + funding) → net-negative.
- Taker fees and perp funding are charged on **notional**; leverage raises
  notional per unit of capital, so the friction hit *on capital* widens, not
  closes.
- Empirical (US-185, NL ledger): directional funding carry printed **+$3,680
  funding vs −$61,546 price risk** (38.8×). Leverage amplifies the *steamroller*
  side, not the income side.

## When leverage IS legitimate

Only to scale the **absolute size** of an edge that is *already* positive
net-of-cost (a capital-constrained, not edge-constrained, situation). It
amplifies a real edge; it never manufactures one. Nothing in the current
pipeline has a positive net edge to amplify.

## Constraint

Leverage stays **OFF** (EPIC-017 binding rule + HermesForge core rule). No
exceptions without explicit human approval — and even then it cannot rescue a
negative-EV strategy.