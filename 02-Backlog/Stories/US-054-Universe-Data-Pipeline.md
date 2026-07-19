---
id: US-054
epic: EPIC-007
type: story
status: in-progress
created: 2026-07-20
points: 3
tags: [validation, data, infrastructure, phase1a]
---

# US-054: Universe + Data Pipeline

## Story
As a strategy validator, I need a defined stock universe and reliable OHLCV data pipeline so that all Phase 1A scanners operate on consistent, clean data.

## Acceptance Criteria
- [ ] Universe defined: top 100 S&P 500 stocks by average dollar volume, computed from yfinance data
- [ ] Universe list saved as `scripts/validation/universe.py` (returns a list of tickers)
- [ ] Data fetcher pulls daily OHLCV via yfinance from Oct 2018 to present for all universe tickers
- [ ] Data cached locally to `~/.hermes/market_data/` as parquet files (one per ticker)
- [ ] Warm-up handling: first valid signal date set to Apr 1 2019 (90-day indicator warm-up)
- [ ] Data quality checks: flag tickers with >5% missing bars; remove from universe for that period
- [ ] Sub-period labels applied: Period 1 (Apr 2019–Dec 2021), Period 2 (Jan 2022–Dec 2023), Period 3 (Jan 2024–present)
- [ ] Script runs end-to-end without errors; prints universe size and date range confirmed

## Technical Notes
- Use `yfinance`, `pandas`, `pyarrow` for parquet
- Universe computation: download SPY constituents or use a hardcoded top-100 list by market cap as proxy (yfinance does not expose constituent lists directly — use a known liquid list)
- Cache invalidation: re-fetch if cached file is >7 days old
- Known limitation: survivorship bias (top 100 today ≠ top 100 in 2019) — document in output, acceptable for Phase 1A

## Definition of Done
- `scripts/validation/universe.py` returns 100 tickers
- `scripts/validation/fetch_data.py` downloads and caches all tickers
- Cache populated at `~/.hermes/market_data/`
- README in `scripts/validation/` documents the pipeline
- Committed to main
