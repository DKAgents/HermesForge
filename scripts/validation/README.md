# HermesForge — Phase 1A Validation Scripts

Signal scanners and analysis tools for Phase 1A strategy reality check.
See ADR-004 for all locked decisions and thresholds.

## Quick Start

### 1. Fetch market data (first time, ~5-10 min)
```bash
cd ~/HermesForge
python3 scripts/validation/fetch_data.py
```
Data cached to `~/.hermes/market_data/` as parquet files.
Re-run with no args to refresh stale files (>7 days old).

### 2. Run all four scanners
```bash
python3 scripts/validation/run_phase1a.py
```

### 3. Run a single strategy
```bash
python3 scripts/validation/run_phase1a.py --strategy a   # MA Pullback
python3 scripts/validation/run_phase1a.py --strategy b   # MACD Divergence
python3 scripts/validation/run_phase1a.py --strategy c   # Breakout + Volume
python3 scripts/validation/run_phase1a.py --strategy d   # S/R Reversal
```

### 4. Fetch + run in one step
```bash
python3 scripts/validation/run_phase1a.py --fetch
```

## Output

Results saved to `scripts/validation/results/`:
- `STR-A-ma-pullback-fibonacci-phase1a.csv`
- `STR-B-macd-histogram-divergence-phase1a.csv`
- `STR-C-breakout-volume-phase1a.csv`
- `STR-D-sr-role-reversal-phase1a.csv`
- `phase1a-summary.md` — kill/pass/watch decisions per ADR-004

## Thresholds (ADR-004)

| Classification | Criteria |
|---|---|
| ❌ KILL | < 12 signals/year OR avg R < 0.2 |
| ⚠️ WATCH | Between kill and pass |
| ✅ PASS | ≥ 25 signals/year AND avg R ≥ 0.6 AND positive in ≥ 2 sub-periods |
| ⚠️ Friction flag | avg R < 0.5 (verify edge survives costs in Phase 1B) |

All Phase 1A results are frictionless and survivorship-biased.
Acceptable for reality check — not for final decision-making.

## Universe

Top 100 liquid US stocks — see `universe.py`.
Survivorship bias: top 100 today ≠ top 100 in 2019. Acknowledged limitation.

## Data

- Source: yfinance daily OHLCV
- Pull start: Oct 2018 (indicator warm-up period)
- Valid signal start: Apr 2019 (after 90-day warm-up)
- Sub-periods:
  - Period 1 (Bull): Apr 2019 – Dec 2021
  - Period 2 (Bear): Jan 2022 – Dec 2023
  - Period 3 (Current): Jan 2024 – present

## File Structure

```
scripts/validation/
├── universe.py           # Universe definition (100 tickers)
├── fetch_data.py         # yfinance downloader + cache manager
├── run_phase1a.py        # Master runner + summary/classification
├── README.md             # This file
├── scanners/
│   ├── __init__.py
│   ├── scanner_a_ma_pullback.py
│   ├── scanner_b_macd_divergence.py
│   ├── scanner_c_breakout_volume.py
│   └── scanner_d_sr_reversal.py
└── results/
    ├── STR-A-*.csv
    ├── STR-B-*.csv
    ├── STR-C-*.csv
    ├── STR-D-*.csv
    └── phase1a-summary.md
```
