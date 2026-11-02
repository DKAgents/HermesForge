---
type: user-story
epic: EPIC-017
priority: P1
status: backlog
created: 2026-11-02
owner: researcher
tags: [hypothesis, sourcing, research]
---

# US-205 — Preferred web sources: SSRN/arXiv over social

## Description
Prefer SSRN and arXiv q-fin (crypto funding, momentum, liquidity, listing effects) over social media for seed sourcing. Social/X ideas require a counterparty answer to enter.

## Acceptance Criteria
- The generator/scout crons query SSRN + arXiv q-fin as primary sources.
- Social/X-mined ideas without a `counterparty` answer are rejected at intake (tie to US-202).
- Sourcing provenance recorded per seed.

## Owner / RACI
- Owner (A): researcher · Responsible (R): researcher · Consulted (C): risk-guardian · Informed (I): orchestrator