#!/usr/bin/env python3
"""
position_sizing.py — HermesForge EPIC-010 (US-067)

Implements each strategy's own validated position sizing rules, plus
portfolio-level heat/concurrency enforcement (ADR-004 risk envelope).

KNOWN LIMITATION: Strategy B's sizing matrix depends on "weekly gates
passing" (3-gate weekly trend framework), but scanner_b_macd_divergence.py
is daily-only and does not currently compute this. Until a weekly-data
pipeline is built (tracked as a gap, not yet a numbered story), this
module defaults to the CONSERVATIVE case (all 3 weekly gates assumed
passing = smallest position size) rather than guessing or fabricating
weekly gate data. This is intentionally conservative, not optimistic.

Usage (unit test):
    python3 position_sizing.py --test
"""

import sys
import pathlib
from typing import Optional

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import trade_log

EXAMPLE_ACCOUNT_SIZE = 100_000
MAX_CONCURRENT_POSITIONS = 5
MAX_PORTFOLIO_HEAT_PCT = 5.0


# ---------------------------------------------------------------------------
# Per-strategy sizing functions
# ---------------------------------------------------------------------------

def size_strategy_b(confirmation_level: str, weekly_gates_passing: Optional[int] = None) -> float:
    """
    Strategy B (MACD Histogram Divergence) — Level x Weekly-gate matrix.
    Matrix (from STR-20260719-macd-histogram-divergence-weekly-assessment.md,
    Position Sizing Step 3):

                          All 3 gates   1 failing   2-3 failing
        Level 2 (1.0% base)   0.50%       0.75%        1.00%
        Level 1 (0.5% base)   0.25%       0.375%       0.50%

    weekly_gates_passing: number of the 3 weekly gates currently passing
    (0-3). If None (not yet computed -- see module docstring), defaults
    conservatively to 3 (all passing -> smallest size for the given level).
    """
    if weekly_gates_passing is None:
        weekly_gates_passing = 3  # conservative default -- see KNOWN LIMITATION above

    gates_failing = 3 - weekly_gates_passing

    if confirmation_level == "Level 2":
        if gates_failing == 0:
            return 0.50
        elif gates_failing == 1:
            return 0.75
        else:  # 2 or 3 failing
            return 1.00
    else:  # Level 1
        if gates_failing == 0:
            return 0.25
        elif gates_failing == 1:
            return 0.375
        else:  # 2 or 3 failing
            return 0.50


def size_strategy_a(*args, **kwargs) -> float:
    """Strategy A (MA Pullback + Fibonacci) — flat 1% per PS-001."""
    return 1.0


def size_strategy_d(*args, **kwargs) -> float:
    """Strategy D (S/R Role Reversal) — flat 1% per PS-001."""
    return 1.0


def size_strategy_i(*args, **kwargs) -> float:
    """Strategy I (Adaptive Trend) — flat 1% per PS-001."""
    return 1.0


def size_strategy_p(*args, **kwargs) -> float:
    """Strategy P (Cross-Sectional Factor) — flat 0.5% (WATCH status, reduced)."""
    return 0.5


def size_strategy_l(*args, **kwargs) -> float:
    """Strategy L (ATR Contraction) — flat 1% per PS-001."""
    return 1.0


def size_strategy_h(*args, **kwargs) -> float:
    """Strategy H (Hype/Momentum) — flat 0.5% (crypto, CR-001)."""
    return 0.5


def size_strategy_q(*args, **kwargs) -> float:
    """Strategy Q (Liquidity Sweep) — flat 1.0% (intraday, post-sweep confirmation)."""
    return 1.0


def size_strategy_r(*args, **kwargs) -> float:
    """Strategy R (Williams Alligator) — flat 1.0% (trend awakening)."""
    return 1.0


# US-113: Batch sizing functions for 18 new strategies
def size_strategy_s(*a, **k): return 1.0  # Elliott Wave
def size_strategy_t(*a, **k): return 1.0  # Head & Shoulders
def size_strategy_u(*a, **k): return 1.0  # Double Top/Bottom
def size_strategy_v(*a, **k): return 1.0  # Triangles
def size_strategy_w(*a, **k): return 1.0  # Flags & Pennants
def size_strategy_x(*a, **k): return 1.0  # Parabolic SAR
def size_strategy_y(*a, **k): return 1.0  # ADX/DMI
def size_strategy_z(*a, **k): return 1.0  # Stochastic
def size_strategy_aa(*a, **k): return 1.0  # Williams %R
def size_strategy_ab(*a, **k): return 1.0  # OBV Divergence
def size_strategy_ac(*a, **k): return 1.0  # CCI
def size_strategy_ad(*a, **k): return 1.0  # Keltner
def size_strategy_ae(*a, **k): return 1.0  # 4-Week Rule
def size_strategy_af(*a, **k): return 1.0  # Candlestick
def size_strategy_ag(*a, **k): return 1.0  # Wedge
def size_strategy_ah(*a, **k): return 1.0  # Island Reversal
def size_strategy_ai(*a, **k): return 1.0  # Seasonal
def size_strategy_aj(*a, **k): return 1.0  # Intermarket


SIZING_FUNCTIONS = {
    "STR-A-ma-pullback-fibonacci":       size_strategy_a,
    "STR-B-macd-histogram-divergence":   size_strategy_b,
    "STR-D-sr-role-reversal":            size_strategy_d,
    "STR-I-adaptive-trend":               size_strategy_i,
    "STR-P-crosssectional":               size_strategy_p,
    "STR-L-atr-contraction":              size_strategy_l,
    "STR-H-hype":                         size_strategy_h,
    "STR-Q-liquidity-sweep":              size_strategy_q,
    "STR-R-alligator":                    size_strategy_r,
    "STR-S-elliott-wave":                 size_strategy_s,
    "STR-T-head-shoulders":               size_strategy_t,
    "STR-U-double-top-bottom":            size_strategy_u,
    "STR-V-triangles":                    size_strategy_v,
    "STR-W-flags-pennants":               size_strategy_w,
    "STR-X-parabolic-sar":                size_strategy_x,
    "STR-Y-adx-dmi":                      size_strategy_y,
    "STR-Z-stochastic":                   size_strategy_z,
    "STR-AA-williams-r":                  size_strategy_aa,
    "STR-AB-obv-divergence":              size_strategy_ab,
    "STR-AC-cci":                         size_strategy_ac,
    "STR-AD-keltner":                     size_strategy_ad,
    "STR-AE-4week":                       size_strategy_ae,
    "STR-AF-candlestick":                 size_strategy_af,
    "STR-AG-wedge":                       size_strategy_ag,
    "STR-AH-island":                      size_strategy_ah,
    "STR-AI-seasonal":                    size_strategy_ai,
    "STR-AJ-intermarket":                 size_strategy_aj,
}


def get_risk_pct(strategy_id: str, signal_dict: dict) -> float:
    """Dispatch to the correct strategy's sizing function."""
    fn = SIZING_FUNCTIONS.get(strategy_id)
    if fn is None:
        # Default: 0.5% for crypto, 1% for stocks
        asset_class = signal_dict.get("asset_class", signal_dict.get("publish_channel", "stock"))
        if asset_class == "crypto":
            return 0.5
        return 1.0

    if strategy_id == "STR-B-macd-histogram-divergence":
        return fn(
            signal_dict.get("confirmation_level", "Level 1"),
            signal_dict.get("weekly_gates_passing"),
        )
    return fn()


# ---------------------------------------------------------------------------
# Portfolio heat enforcement
# ---------------------------------------------------------------------------

def check_portfolio_heat(new_risk_pct: float) -> tuple[bool, str]:
    """
    Returns (allowed, reason). Enforces ADR-004: max 5 concurrent positions,
    max 5% aggregate open risk ("heat").
    """
    open_trades = trade_log.get_open_trades()

    if len(open_trades) >= MAX_CONCURRENT_POSITIONS:
        return False, f"Max concurrent positions reached ({len(open_trades)}/{MAX_CONCURRENT_POSITIONS})"

    current_heat = sum(float(t.get("position_size_pct", 0) or 0) for t in open_trades)
    if current_heat + new_risk_pct > MAX_PORTFOLIO_HEAT_PCT:
        return False, (
            f"Adding {new_risk_pct}% risk would exceed max portfolio heat "
            f"({current_heat:.2f}% open + {new_risk_pct}% new > {MAX_PORTFOLIO_HEAT_PCT}%)"
        )

    return True, ""


# ---------------------------------------------------------------------------
# Unit tests
# ---------------------------------------------------------------------------

def _test():
    import tempfile

    # --- Sizing matrix tests (matches STR-B note's Step 3 table exactly) ---
    assert size_strategy_b("Level 2", weekly_gates_passing=3) == 0.50
    assert size_strategy_b("Level 2", weekly_gates_passing=2) == 0.75  # 1 failing
    assert size_strategy_b("Level 2", weekly_gates_passing=1) == 1.00  # 2 failing
    assert size_strategy_b("Level 2", weekly_gates_passing=0) == 1.00  # 3 failing
    assert size_strategy_b("Level 1", weekly_gates_passing=3) == 0.25
    assert size_strategy_b("Level 1", weekly_gates_passing=2) == 0.375
    assert size_strategy_b("Level 1", weekly_gates_passing=1) == 0.50
    assert size_strategy_b("Level 1", weekly_gates_passing=0) == 0.50
    assert size_strategy_b("Level 2", weekly_gates_passing=None) == 0.50  # conservative default
    print("✅ Strategy B sizing matrix matches STR-B note exactly")

    assert size_strategy_a() == 1.0
    assert size_strategy_d() == 1.0
    print("✅ Strategy A/D flat 1% verified")

    assert get_risk_pct("STR-A-ma-pullback-fibonacci", {}) == 1.0
    assert get_risk_pct("STR-B-macd-histogram-divergence",
                         {"confirmation_level": "Level 1", "weekly_gates_passing": 1}) == 0.50
    print("✅ get_risk_pct dispatch verified")

    # --- Portfolio heat tests ---
    orig_path = trade_log.LOG_PATH
    trade_log.LOG_PATH = pathlib.Path(tempfile.mktemp(suffix=".csv"))
    try:
        allowed, reason = check_portfolio_heat(1.0)
        assert allowed is True, "empty portfolio should allow any reasonable trade"

        # Fill to 5 concurrent positions
        for i in range(5):
            trade_log.open_trade({
                "strategy_id": "STR-A-ma-pullback-fibonacci",
                "ticker": f"TICK{i}",
                "entry_date": "2026-07-20",
                "entry_price": 100.0, "stop_price": 95.0, "target_price": 115.0,
                "position_size_pct": 1.0,
            })

        allowed, reason = check_portfolio_heat(1.0)
        assert allowed is False, "6th concurrent position should be rejected"
        assert "concurrent" in reason.lower()
        print("✅ Max-concurrent-positions rejection verified")

    finally:
        trade_log.LOG_PATH = orig_path

    # Heat-percentage rejection (separate from concurrency)
    trade_log.LOG_PATH = pathlib.Path(tempfile.mktemp(suffix=".csv"))
    try:
        trade_log.open_trade({
            "strategy_id": "STR-A-ma-pullback-fibonacci", "ticker": "AAA",
            "entry_date": "2026-07-20", "entry_price": 100.0, "stop_price": 95.0,
            "target_price": 115.0, "position_size_pct": 4.5,
        })
        allowed, reason = check_portfolio_heat(1.0)  # 4.5 + 1.0 > 5.0
        assert allowed is False, "exceeding 5% aggregate heat should be rejected"
        assert "heat" in reason.lower()
        print("✅ Max-portfolio-heat rejection verified")
    finally:
        trade_log.LOG_PATH = orig_path

    print("\n✅ All position_sizing.py unit tests passed")


if __name__ == "__main__":
    if "--test" in sys.argv:
        _test()
    else:
        print(__doc__)
