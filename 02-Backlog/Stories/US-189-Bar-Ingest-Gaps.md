---
type: user-story
epic: EPIC-016
priority: P1
status: backlog
created: 2026-11-02
tags: [data, bars, okx-proxy, bug]
---

# US-189 — Fix 1d bar ingestion gaps

## Problem

US-182's backtest found two ground-truth data-layer bugs (both root-caused, not papered over):

1. `bars_1d.db` is **empty** — `ingest_hl_bars.py` skips the 1d interval behind a false dependency ("already ingested deep by `fetch_crypto_data.py`", which does not exist in the tree).
2. `okx_proxy` passes `"1d"` to OKX, which rejects it (code 51000) — OKX requires `"1D"`. So the `load_bars("1d")` proxy fallback is broken.

## Fix

1. Remove the phantom dependency + enable 1d ingestion in `ingest_hl_bars.py` (and confirm the store seeds).
2. Normalize the OKX interval casing (`"1d"` → `"1D"`) in `okx_proxy` so the proxy fallback works.

## Acceptance

- `bars_1d.db` seeds with real 1d bars per coin (verify a positive row count + idempotent re-run).
- `load_bars("1d")` returns HL data directly and, on the pre-store gap, the OKX proxy works (no code 51000).