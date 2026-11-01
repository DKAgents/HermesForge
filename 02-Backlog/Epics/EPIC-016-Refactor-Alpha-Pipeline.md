---
type: epic
status: backlog
created: 2026-11-01
tags: [refactor, alpha, quant]
---

# EPIC-016 — Refactor the Alpha Pipeline

Driven by the deep-research diagnosis (committed evidence: `reports/backtester/` + the refactor synthesis). The pipeline failed for three compounding reasons, now each addressed:

1. **Look-ahead measurement** (fabricated edges) — FIXED: US-173 (next-open fill) + US-174 (mandatory G3 fill-realism gate).
2. **The retail TA / chart-pattern / ICT-SMC signal class has no raw alpha** — STR-Q was a literal coin-flip (24.2% win), and the whole class is empirically falsified / arbitraged-away. This epic REPLACES the signal class.
3. **Execution drag** — worst-print stops + trade-through entries turn −1 R nominal into −2.86 R actual. This epic fixes it.

## Stories

- **US-179** — Funding/basis carry (delta-neutral crypto) — the flagship new alpha, Tier-1, cheapest real edge.
- **US-180** — Execution-layer drag fix (wider stops, limit entries at the level, market-vs-limit exits).
- **US-181** — Vol/VRP with vol-of-vol timing.
- **US-182** — Cost-aware cross-sectional momentum.
- **US-183** — Harden the validation harness (deflated Sharpe, post-publication samples, no-trade zones, min-regime floors).

## Governing principles (binding)

- Optimize for **alpha decay + capacity**, not raw Sharpe.
- Every signal ships **no-trade zones + partial rebalancing** (cost-aware).
- Every promotion passes **US-174's mandatory G3 fill-realism gate** (realistic mean R > 0, pessimistic PF > 1.0, n ≥ 10, fail-closed).