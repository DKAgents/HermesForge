---
type: user-story
epic: EPIC-017
priority: P1
status: backlog
created: 2026-11-07
owner: publisher
tags: [carry, funding, report, paper-trading, discord]
---

# US-230 — Add funding-carry status to the daily paper-trading report

## Problem

The delta-neutral funding carry (STR-FNDCARRY, US-229) is now paper-forward and
accumulating maker-only PnL. But the daily performance report (`performance_
report.py` → `#paper-trading` 1537225420120793088) has no visibility into it —
the carry ledger grows invisibly. The user wants the carry's paper-forward status
surfaced in the existing daily post.

## Fix

Add a compact "Funding Carry (STR-FNDCARRY)" section to `build_report()` in
`scripts/paper_trading/performance_report.py`:
- Read the carry's closed episodes (`funding_carry_paper.jsonl`) + open positions
  (`funding_carry_paper_state.json`) via the carry module (import
  `read_ledger`/`load_state`, do NOT re-parse the files separately).
- Report: open carry positions (coin + entry) and the closed-episode PnL with the
  funding-vs-basis split EXPLICIT (headline `net_funding` = funding-only; `basis_pnl`
  flagged separately — never folded into the headline, per US-179).
- Trade IDs `STR-FNDCARRY-<COIN>-MMDDS` shown.
- If there are no carry positions/episodes yet, emit a single quiet line
  ("STR-FNDCARRY: no episodes yet — accumulating") rather than omitting the section.

## Hard constraints (binding)

- Do NOT alter the existing report sections/order (fill-realistic headline, gauntlet
  secondary, strategy/asset-class breakdowns) — this is an ADDITIVE section.
- Funding-vs-basis split preserved (headline = funding-only).
- Path-scoped commit only; never `git add -A` / `git add .`.
- No `send_message` from a cron context; the report already posts via the existing
  `post_to_discord` path + crosspost — keep that mechanism intact.

## Acceptance Criteria

- Daily report includes a funding-carry section with open positions + closed PnL
  (funding-only headline + flagged basis).
- Quiet "accumulating" line when empty.
- Existing report sections untouched; post + crosspost path unchanged.

## Owner / RACI
- Owner (A): publisher · Responsible (R): publisher · Consulted (C): coder · Informed (I): orchestrator