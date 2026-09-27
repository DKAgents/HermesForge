---
topic: research
confidence: high
has_quotes: false
tags: []
source: unknown
created: 2026-08-14
---
# Edge Candidates

Staging directory for the autonomous strategy pipeline.

## Flow
1. **External Edge Discovery** (cron `e214a9d8f348`, Tue/Thu/Sun 16:00 UTC) — searches web/X/vault, critiques findings, writes promising edges here as candidate files
2. **Autonomous Strategy Pipeline** (cron `2d8dff498d1f`, Tue/Thu/Sun 17:00 UTC) — picks up staged candidates, writes scanner code, runs backtest, runs walk-forward validation, deploys to paper trading

## Candidate File Status
- `staged` — waiting to be processed by the pipeline
- `processing` — pipeline is currently working on it
- `processed` — fully validated and deployed to paper trading
- `backtest_failed` — preliminary backtest showed no edge
- `validation_failed` — walk-forward validation showed no OOS edge
- `watch` — marginal validation results, deployed with WATCH status

## Naming Convention
`CAND-[YYYYMMDD]-[short-name].md`
