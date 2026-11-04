---
type: user-story
epic: EPIC-017
priority: P1
status: backlog
created: 2026-11-02
owner: architect
tags: [gauntlet, reverse-engineering, builder, breaker, diagnostics]
---

# US-222 — Record-reverse-engineering builder + breaker harness

## Problem

The gauntlet can *test* any rule (G0→G7), but it cannot *reconstruct* a rule
from a dated trade record. The recurring question — "does THIS trader's actual
method have edge?" (the coach's record, my own history, a fund's filings) — is
currently unanswerable by measurement. A methodology from external research
(builder→breaker→harness, sealed time-split) maps nearly 1:1 onto our existing
gauntlet, but the **builder** half is missing.

## Build

1. **Builder** — reads a dated position/trade record (CSV/JSON: date, direction
   long/short/flat, price, size), **seals the recent half (time-seal, never a
   random split)**, and reconstructs the **smallest rule** from a small feature
   library (price-derived: SMA crosses / momentum / breakouts; + positioning:
   funding extreme / OI change) that best reproduces the record. Emits the rule
   as code + in-sample reproduction accuracy. Parsimony is the discipline: a
   bigger rule fits any record (overfit), so prefer the fewest features that hold
   OOS.
2. **Harness / breaker** — runs the reconstructed rule on the SEALED half (OOS
   reproduction = "did it learn the market, or just this record?"), then feeds it
   into the existing gauntlet (G0 cost-first, G3 fill realism, G4/G5 if it
   survives). **Charges fees — the source methodology runs gross of costs; we do
   not.** No model may report a number it did not compute.
3. Every run → trials ledger; pre-registration + counterparty-flag still apply (a
   reconstructed rule with no structural counterparty is flagged as diagnostic,
   never auto-promoted).

## Acceptance Criteria

- **Synthetic validation:** a record generated from a KNOWN rule (e.g. "long when
  close > SMA10m") → builder recovers ~that rule AND the breaker confirms it
  holds OOS; an overfit synthetic record (a rule that fits noise) → builder's
  rule FAILS OOS (breaker catches it).
- Works on a real dated record (the user's own CSV).
- Output feeds the gauntlet with fees charged.

## Owner / RACI
- Owner (A): architect · Responsible (R): coder · Consulted (C): risk-guardian, backtester · Informed (I): orchestrator