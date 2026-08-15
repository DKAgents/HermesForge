---
title: "US-107: Institutional Stop-Loss Sweep Detection & Entry Timing"
epic: "EPIC-015-Liquidity-Sweeps"
status: "in-progress"
priority: "high"
created: 2026-08-26
assigned_to: "agent"
---

# US-107: Institutional Stop-Loss Sweep Detection & Entry Timing

## Problem Statement

Our MAE/MFE analysis revealed that **73.7% of stops get hit** before the real trade move happens, with an MFE/realized ratio of 8.62x. This pattern is consistent with institutional stop-loss sweeps: price penetrates a key liquidity level, triggers resting stop orders (providing liquidity for institutions), then reverses in the intended trade direction.

None of our 18 scanners accounted for this phenomenon. All strategies entered on signal trigger without checking whether a liquidity sweep had occurred or was pending.

## Solution

Built a complete intraday liquidity sweep detection system:

### 1. Intraday Data Infrastructure
- **`fetch_intraday_crypto.py`**: Hyperliquid API for 1m/5m/15m/1h crypto candles (free, unlimited history)
- **`fetch_intraday_stocks.py`**: yfinance for 5m/15m stock bars (free, 60 days history). Alpaca upgrade path included for 7+ years of 1m data.

### 2. Sweep Detection Engine (`detect_liquidity_sweeps.py`)
Detects sweeps at 8 liquidity level types:
- Prior Day High/Low (PDH/PDL)
- Session High/Low
- Equal Highs/Lows (liquidity pools)
- Swing Highs/Lows
- Round Numbers

Each sweep scored 0-100 based on: penetration depth (ATR), wick quality, volume surge, level strength, and confirmation status.

### 3. STR-Q Strategy Scanner (`scanner_q_liquidity_sweep.py`)
New strategy that enters AFTER sweep confirmation. Entry on sweep candle close, stop behind sweep wick, 3R target, 15-bar time stop.

### 4. Sweep Timing Filter (`sweep_timing_filter.py`)
Three modes for existing strategies:
- **Boost** (default): Tags signals with sweep context, +15 quality if sweep-aligned
- **Require**: Blocks signals unless a confirmed sweep is detected
- **Delay**: Holds signal until sweep confirmation

### 5. Integration
- Wired into `capture_signals.py`: Every signal from STR-A/B/D/I now tagged with sweep context
- Wired into `full_research_pipeline.py`: Module 8 runs sweep detection on crypto + stock universe

## Phase 1A Backtest Results

### Crypto (5m, 8 symbols, 500 bars)
- **237 signals, 51.1% WR, +0.843 avg R, +199.8 sum R**
- Best level: equal_lows (67.7% WR, +1.648R)
- Worst level: round_number (34.0% WR, +0.198R)
- Bullish: 50.9% WR, Bearish: 51.2% WR (balanced)

### Stocks (5m, 8 symbols, 500 bars)
- **313 signals, 54.6% WR, +0.864 avg R, +270.5 sum R**
- Best level: PDH (75.0% WR, +1.572R), round_number (68.2% WR, +1.547R)
- Session low: 70.0% WR, +1.122R
- Bearish slightly better than bullish (57.4% vs 51.9%)

### Comparison to Existing Strategies
| Strategy | Avg R | Win Rate |
|---|---|---|
| STR-B (MACD Div) | +0.227 | ~30% |
| STR-Q Crypto | **+0.843** | **51.1%** |
| STR-Q Stocks | **+0.864** | **54.6%** |

STR-Q shows ~3.7x better average R than our best existing strategy.

## Key Findings

1. **Equal lows are the strongest signal** (crypto: 67.7% WR). Multiple matching swing points = concentrated stop orders = higher-quality sweep.
2. **Round numbers work for stocks** (68.2% WR, +1.547R) but NOT for crypto (34.0% WR, +0.198R). Crypto has fewer round-number stops.
3. **PDH/PDL sweeps are high-quality for stocks** (75% WR) but rare (8 trades). Worth monitoring.
4. **Quality score 50-60 bucket performs best** (60.8% WR, +1.120R). The 70-80 bucket underperforms — likely overfitting to specific patterns.
5. **Bearish sweeps slightly outperform bullish** in stocks (57.4% vs 51.9% WR).

## Data Source Limitations

- **Crypto (Hyperliquid)**: Unlimited 1m/5m/15m history. Best fidelity.
- **Stocks (yfinance)**: 60 days of 5m, 7 days of 1m. Limited backtesting window.
- **Upgrade path**: Alpaca free tier would give 7+ years of 1m stock data. Requires free signup at alpaca.markets.

## Acceptance Criteria

- [x] Intraday data fetchers for crypto and stocks
- [x] Sweep detection engine with 8 liquidity level types
- [x] STR-Q Phase 1A backtest completed (crypto + stocks)
- [x] Sweep timing filter with 3 modes (boost/require/delay)
- [x] Wired into capture_signals.py (signal tagging)
- [x] Wired into full_research_pipeline.py (Module 8)
- [ ] STR-Q walk-forward validation (Phase 1B)
- [ ] STR-Q added to live signal capture (separate intraday cron)
- [ ] Historical trade backfill with sweep context
- [ ] Alpaca integration for extended stock backtesting

## Files Created/Modified

| File | Status | Description |
|---|---|---|
| `scripts/data/fetch_intraday_crypto.py` | NEW | Hyperliquid 1m/5m/15m candles |
| `scripts/data/fetch_intraday_stocks.py` | NEW | yfinance 5m/15m + Alpaca upgrade path |
| `scripts/data/detect_liquidity_sweeps.py` | NEW | Core sweep detection engine (27KB) |
| `scripts/data/sweep_timing_filter.py` | NEW | Filter for existing strategies |
| `scripts/validation/scanners/scanner_q_liquidity_sweep.py` | NEW | STR-Q Phase 1A scanner |
| `scripts/paper_trading/capture_signals.py` | MODIFIED | Sweep context tagging added |
| `scripts/research/full_research_pipeline.py` | MODIFIED | Module 8: sweep detection |
| `scripts/validation/results/STR-Q-crypto-phase1a.csv` | NEW | Backtest results |
| `scripts/validation/results/STR-Q-stocks-phase1a.csv` | NEW | Backtest results |

## Dependencies

- Hyperliquid API (free, no key) — already wired for daily data
- yfinance (free, no key) — already wired for daily data
- No new dependencies required
