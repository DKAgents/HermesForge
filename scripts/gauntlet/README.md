# Strategy Gauntlet — Execution Simulator (G3)

Execution realism module for the HermesForge Strategy Gauntlet (PROP-001).  
Replays fills against L2 orderbook state to measure what a strategy actually captures after slippage, fees, and funding.

## Quick start

```python
from execution_sim import (
    FillMode, Direction,
    simulate_trade, batch_simulate, check_mode_ordering,
    make_book, make_snapshot,
)

# Build a synthetic L2 book (centered at 100, 5 levels, 50K depth each)
book = make_book(100.0, spread_bps=2.0, levels=5, depth_per_level=50_000)
snap = make_snapshot(100.0)
snap2 = make_snapshot(101.0)

result = simulate_trade(
    entry_price=100.0,
    exit_price=101.0,
    size_usd=10_000,
    direction=Direction.LONG,
    entry_mode=FillMode.OPTIMISTIC,
    exit_mode=FillMode.REALISTIC,
    l2_snapshots=[snap, snap2],
    funding_rates=[1.0],          # 1 bps 8h funding rate
    holding_period_hours=8.0,
)

print(f"Net PnL: {result['net_pnl_bps']:.1f} bps")
print(f"  Gross:  {result['gross_pnl_bps']:.1f} bps")
print(f"  Fees:   {result['fees_bps']:.1f} bps")
print(f"  Slippage: {result['slippage_bps']:.1f} bps")
print(f"  Funding:  {result['funding_bps']:.1f} bps")
```

## Three fill modes

| Mode | Behavior |
|---|---|
| `OPTIMISTIC` | Always fills at target (mid) price |
| `REALISTIC` | Queue-aware: limit orders fill only when price trades through; market orders at VWAP |
| `PESSIMISTIC` | Taker at best bid/ask + one tick adverse selection |

## Key functions

### `simulate_trade(...)`
Simulate one round-trip trade. Returns `dict` with `gross_pnl_bps`, `fees_bps`, `slippage_bps`, `funding_bps`, `net_pnl_bps`, `fill_prices`.

### `batch_simulate(trades, mode)`
Run a list of trades through one fill mode. Returns aggregate stats:
- `mean_net_r` — mean net PnL in R-units
- `pf` — profit factor
- `win_rate` — fraction of trades with positive net PnL
- `n_trades`, `net_pnls_bps`

### `check_mode_ordering(trades)`
Run all three modes and verify `OPTIMISTIC >= REALISTIC >= PESSIMISTIC`.

### `compute_slippage_bps(size_usd, book, direction)`
Compute expected slippage in bps for executing *size_usd* against a book. Monotonic in size.

### Fee & funding
- Fees: 4.5 bps taker fee per leg (9 bps round-trip)
- Funding: Hyperliquid formula — hourly = 1/8 of 8h premium + 0.01%/8h interest, premium clamped to ±0.05%, hard cap 4%/hr

## L2 book format

```python
book = {
    "bids": [[price, size_usd], ...],  # descending by price
    "asks": [[price, size_usd], ...],  # ascending by price
}

snapshot = {
    "book": book,
    "mid": 100.0,  # optional
}
```

## Running tests

```bash
cd scripts/gauntlet
python3 tests/test_execution_sim.py
```

12 tests covering: mid fills, limit fills, queue position, VWAP, fees, funding, slippage monotonicity, mode ordering, zero-size, long/short signs, batch aggregation, empty trades.