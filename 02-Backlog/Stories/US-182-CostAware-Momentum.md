---
type: user-story
epic: EPIC-016
priority: P1
status: backlog
created: 2026-11-01
tags: [alpha, momentum, cross-sectional]
---

# US-182 — Cost-aware cross-sectional momentum

## Problem

Cross-sectional momentum grosses ~0.64%/mo but pays ~63 bps/mo to trade it; naive construction is net-unprofitable. Transaction-cost-aware construction (partial rebalancing toward target weights) raises net Sharpe up to 2.5×. In crypto it is low-beta directional (a Bitcoin-regime-overlay), not market-neutral.

## Fix

Build a cross-sectional momentum strategy with: (a) transaction-cost-aware construction (partial rebalancing), (b) a market-regime overlay (e.g. BTC 200-DMA), (c) inverse-vol / gross-exposure caps. Accept it as low-beta, conditionally directional.

## Acceptance

- A cost-aware construction (partial rebalance toward target weights) + regime overlay + vol caps.
- A backtest showing net edge that survives the G3 gate.