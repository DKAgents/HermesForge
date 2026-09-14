# Strategy Discovery Context — T1 Research Session

## Current State
After one month of paper trading, zero strategies survive hostile fill modeling:
- **STR-Q-liquidity-sweep** (5m intraday): Paper +1,305R / 52% WR → Hostile -104R / 42% WR (1,721 trades scored). Edge evaporates.
- **Swing strategies** (STR-VIXC, STR-B, STR-A): Only 7 hostile-scored closures. Paper -1.00R → Hostile -11.23R. Sample too small.
- **3,986 additional STR-Q trades** skipped (outside 5m bar cache window). Unscored.

## Hostile Fill Rules (What Kills the Edge)
Every strategy must survive these execution realities:
1. Fill at t+1 open (cannot fill on signal bar)
2. Taker fee 0.1% per side (0.2% round-trip)
3. Limit orders: must trade THROUGH level, not just touch
4. Stops: fill at WORST print on crossing bar (bar low for longs, bar high for shorts)
5. 75-min time stop on intraday (15 × 5m bars)

## What We Have In-House
- **Vault / second brain**: ~/HermesForge/vault/ — Obsidian notes, trading book summaries including Murphy's "Technical Analysis of the Financial Markets"
- **Existing scanners**: STR-Q (liquidity sweeps), STR-VIXC (VXX contango), STR-A (MA pullbacks), STR-B (MACD divergences)
- **Data**: 5m intraday bars (crypto OKX), daily bars (stocks + crypto), parquet cache

## What We Need
Generate **5-10 concrete, codable strategy specifications**. Each must include:
- Entry signal (exact conditions — e.g., "price sweeps below prior 5-bar low then reclaims")
- Entry method (market/limit, which bar)
- Stop placement (exact rule — e.g., "1 ATR below entry, minimum 0.5%")
- Target(s) (exact rule — e.g., "2:1 R multiple or prior swing high")
- Time stop (if intraday)
- Asset class (crypto, stocks, or both)
- Expected edge thesis (why should this work despite hostile fills?)

## What to Avoid
- Strategies with tight stops (<0.3% on crypto) — taker fees alone eat 0.2%
- Strategies relying on fills at exact signal-bar prices — t+1 gap kills these
- Mean reversion with wide stops — hostile worst-print rule punishes these
- Anything requiring sub-5m execution

## Reference
- Murphy: /root/HermesForge/technical-analysis-of-the-financial-mark-murphy/ — classic TA patterns
- Vault: /root/HermesForge/vault/ — Obsidian notes, strategy ideas, book summaries
- Existing trade journal: /root/HermesForge/scripts/paper_trading/trades.csv

## Constraints
- Paper trading only. 1% risk cap. No live execution.
- Strategies must be codable in Python with existing data feeds (5m/daily bars).
- Output: a markdown spec file per strategy in /root/HermesForge/04-Strategies/