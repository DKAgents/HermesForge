"""preregister_us211_us212.py — US-211 + US-212 pre-registration (EPIC-017 Phase 4).

Pre-registers the two Phase-4 research hypotheses with FULL US-202 frontmatter
(incl. the load-bearing `counterparty`), then runs before any backtest. Uses the
canonical register() intake path (validate_frontmatter + signal-class gate +
duplicate check). Write-once to data/gauntlet/hypotheses.jsonl.

  HYP-14  = US-211  BTC-residualized cross-sectional momentum (the raw xsmom
                     re-run with the beta stripped before ranking).
  HYP-15  = US-212  funding-extreme unwind at SWING horizon (4-48h) —
                     positioning-conditioned re-spec of the seed-pool HYP-01.

Read-only research driver; registers hypotheses, runs NO backtest.
"""

from __future__ import annotations

import pathlib
import sys

_THIS_DIR = pathlib.Path(__file__).resolve().parent
if str(_THIS_DIR) not in sys.path:
    sys.path.insert(0, str(_THIS_DIR))

import hypothesis_register as hr  # noqa: E402


HYP_14 = {
    "hypothesis_id": "HYP-14",
    "source": "human",
    "venue": "hyperliquid",
    "instruments": ["universe:hl-perps"],
    "horizon": "7d",
    "entry_logic": (
        "Rank the 31-name Hyperliquid perp universe on BTC-RESIDUALIZED "
        "30-day momentum: regress each coin's daily returns on BTC daily "
        "returns (rolling 60d beta, estimated on data through t-1 to avoid "
        "look-ahead), build a residual-return series, rank on the residualized "
        "cumulative return. Long the top quintile. Strips the BTC-beta before "
        "ranking so the book is idiosyncratic alpha, not directional beta."
    ),
    "exit_logic": (
        "Weekly rebalance; partial-rebalance (kappa=0.5) with a no-trade band "
        "(0.25); BTC 200-DMA overlay scales gross to 0.5 when down. Exit on "
        "rank decay below the median. No leverage (gross exposure cap 1.0)."
    ),
    "expected_gross_edge_bps": 30,
    "cost_hurdle_bps": 45,
    "data_dependencies": ["hl:candleSnapshot"],
    "counterparty": (
        "Alt-coin momentum under-reaction that is idiosyncratic to the coin "
        "AFTER stripping the systematic BTC move: late trend-followers and "
        "delayed indexers who chase the residual drift rather than the BTC "
        "beta, paying the spread to catch up after the move. They accept the "
        "loss because they are chasing, not arbitraging, the cross-section."
    ),
    "execution_mode": "taker",
    "falsification_criteria": (
        "Residualizing BTC FAILS to clear the overfit controls that sank the "
        "raw version: CPCV 10th-pct split PF < 1.0, OR PBO >= 0.30, OR DSR <= "
        "0.95, OR the edge remains concentrated in < 2 BTC-beta clusters "
        "(i.e. the residual still carries systematic beta)."
    ),
    "primitives": ["momentum_30d", "btc_residual", "regime"],
    "description": (
        "US-211: BTC-residualized cross-sectional momentum. Regress per-coin "
        "returns on BTC, rank on residuals to strip beta before ranking."
    ),
    "tier": "T1",
    "timeframe": "1d",
}

HYP_15 = {
    "hypothesis_id": "HYP-15",
    "source": "human",
    "venue": "hyperliquid",
    "instruments": ["universe:hl-perps"],
    "horizon": "4-48h",
    "entry_logic": (
        "Fade crowded positioning when the hourly perp funding rate exceeds "
        "its trailing 95th percentile (funding extreme) AND open interest is "
        "still rising (OI-delta quadrant), using the HL funding percentile, "
        "the OKX funding SPREAD, and the OI-delta quadrant (positioning-"
        "conditioned, not the naked directional carry that structural "
        "analysis rejected)."
    ),
    "exit_logic": (
        "Exit on funding mean-reversion below the 80th percentile, or a hard "
        "stop at 1x structure-wide ATR against the entry."
    ),
    "expected_gross_edge_bps": 15,
    "cost_hurdle_bps": 45,
    "data_dependencies": [
        "hl:fundingHistory", "hl:assetCtxs.openInterest", "okx:funding-rate",
    ],
    "counterparty": (
        "Late retail longs crowding a high-funding regime — they accept "
        "negative funding carry because they are momentum-chasing, not "
        "carry-aware, so the unwind pays them to hold and price corrects "
        "against them."
    ),
    "execution_mode": "taker",
    "falsification_criteria": (
        "Sharpe < 0.5 over 200+ trades, OR the HONEST funding-only edge "
        "(funding_pnl - execution_cost, with the basis-proxy contribution "
        "stripped) disappears when funding falls below the 80th percentile."
    ),
    "primitives": ["funding_percentile", "oi_delta", "funding_spread"],
    "description": (
        "US-212: funding-extreme unwind at SWING horizon (4-48h). Positioning-"
        "conditioned re-spec of seed-pool HYP-01: funding > 95th %ile + OI "
        "rising + OKX funding spread + OI-delta quadrant."
    ),
    "tier": "T3",
    "timeframe": "1h-6h",
}


def main() -> int:
    for entry in (HYP_14, HYP_15):
        hid = entry["hypothesis_id"]
        try:
            rec = hr.register(entry)
            print(f"registered {hid}  status={rec['status']} "
                  f"registered_at={rec['registered_at']}")
        except ValueError as e:
            print(f"REJECTED {hid}: {e}")
    return 0


if __name__ == "__main__":
    sys.exit(main())