---
id: US-076
epic: EPIC-011
type: story
status: backlog
created: 2026-07-20
points: 2
tags: [hyperliquid, crypto, strategy-adaptation]
depends-on: US-069
---

# US-076: Crypto Strategy Adaptation

## Story
As the paper trading system, I need a clear decision on which of strategies A/B/D apply to which crypto pairs (BTC/ETH/SOL), and how strategy-specific concepts that assume stock-market structure (weekly bars, market-hours gaps) translate to 24/7 crypto markets.

## Acceptance Criteria
- [ ] Document decision in this story (or a linked ADR) for each strategy: applies to crypto as-is / applies with modification / does not apply
- [ ] Specifically resolve: Strategy A's weekly-gate logic assumes a stock-market weekly bar — define what "weekly" means for a 24/7 asset (e.g. Mon-Sun UTC close) or explicitly exclude Strategy A from crypto
- [ ] Specifically resolve: Strategy B's weekly trend-scaling matrix — same weekly-bar-definition question
- [ ] Strategy D's S/R role-reversal logic has no obvious stock-specific assumption — likely portable as-is, confirm
- [ ] Update the crypto scanner smoke test (US-069) results with the finalized strategy-per-pair mapping

## Definition of Done
- Strategy-to-crypto-pair mapping documented and committed
- Weekly-bar-definition question resolved (not left open)
