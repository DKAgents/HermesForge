---
type: user-story
epic: EPIC-016
priority: P1
status: backlog
created: 2026-11-01
tags: [data, options, iv, volatility]
---

# US-187 — Options IV surface

## Problem

The vol / variance-risk-premium direction (US-181) cannot be built without an options implied-volatility surface, which we do not ingest (US-120 already flags "IV rank data source" as a missing dependency).

## Fix

Ingest an options IV feed into a persistent store:
- Crypto: Deribit BTC/ETH options implied volatility (public `get_volatility_index_data` / options chain) — or an equivalent.
- Equities: IV for the traded stock universe (yfinance options chains, which the existing options recommender already uses).

## Acceptance

- An IV surface store + ingestion cron (no_agent, resolve_python.sh), idempotent.
- The vol/VRP strategy (US-181) can consume vol-of-vol level for its timing gate.