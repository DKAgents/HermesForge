#!/usr/bin/env python3
"""
G2 Parameter Sensitivity Gate for Strategy Gauntlet (PROP-001).

Tests whether a strategy's profitability survives small parameter perturbations.
A strategy that only works at a narrow sweet spot is fragile — G2 catches
overfitting before it reaches live trading.

Gate logic:
    1. Discover the strategy's numeric parameters (via PARAMS dict or auto-detect)
    2. For each parameter, generate ±20% variations
    3. Re-run the backtest on the same dataset for each variation
    4. Compute net R (sum of r_multiple) for baseline and each variation
    5. Robustness score = fraction of variations where net R > 0
    6. Pass threshold: >= 0.8 (strategy survives 80%+ of parameter variations)

Integration with scanners:
    Scanners SHOULD declare a PARAMS dict at module level:
        PARAMS = {"ATR_PERIOD": 10, "ATR_MULT": 2.0, "EMA_PERIOD": 20}
    If absent, G2 auto-detects all-uppercase numeric module-level constants,
    filtering out known non-param names (STRATEGY_ID, STRATEGY_VERSION, etc.).
"""

from __future__ import annotations

import importlib
import importlib.util
import inspect
import os
import sys
import warnings
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

# ── Configuration ──────────────────────────────────────────────────────────

DEFAULT_DELTA_PCT = 0.20        # ±20% variation
PASS_THRESHOLD = 0.80            # must survive 80%+ of variations
SCANNERS_DIR = Path(__file__).resolve().parent.parent / "validation" / "scanners"

# Module-level constants that are NOT strategy parameters (auto-detect exclusions)
NON_PARAM_NAMES = frozenset({
    "STRATEGY_ID", "STRATEGY_NAME", "STRATEGY_VERSION",
    "CACHE_DIR", "DATA_DIR", "REPO_ROOT", "SUBPERIODS",
    "MIN_BARS", "MIN_ALIGNED",
    "__builtins__", "__cached__", "__doc__", "__file__", "__loader__",
    "__name__", "__package__", "__spec__",
    "pd", "np", "os", "sys", "Path", "pathlib", "datetime",
    "warnings", "importlib", "inspect",
})


# ── Scanner discovery ──────────────────────────────────────────────────────

# Cache: strategy_id -> (module, module_path)
_scanner_module_cache: Dict[str, Any] = {}


def _find_scanner_module(strategy_id: str) -> Tuple[Any, Path]:
    """
    Locate the scanner module for a strategy_id.

    Searches scanners/ directory for a .py file whose STRATEGY_ID constant
    matches. Falls back to filename-based matching.

    Returns (module, path). Raises FileNotFoundError if no scanner found.
    """
    if strategy_id in _scanner_module_cache:
        mod = _scanner_module_cache[strategy_id]
        path = Path(inspect.getfile(mod))
        return mod, path

    scanners_dir = SCANNERS_DIR
    if not scanners_dir.exists():
        raise FileNotFoundError(f"Scanners directory not found: {scanners_dir}")

    # Strategy-ID-to-module mapping: load each .py file, check STRATEGY_ID
    for py_file in sorted(scanners_dir.glob("*.py")):
        if py_file.name.startswith("_"):
            continue
        mod_name = py_file.stem
        try:
            spec = importlib.util.spec_from_file_location(mod_name, str(py_file))
            if spec is None or spec.loader is None:
                continue
            mod = importlib.util.module_from_spec(spec)
            sys.modules[mod_name] = mod
            spec.loader.exec_module(mod)
            sid = getattr(mod, "STRATEGY_ID", "")
            if sid and sid.lower() == strategy_id.lower():
                _scanner_module_cache[strategy_id] = mod
                return mod, py_file
        except Exception:
            continue

    raise FileNotFoundError(
        f"No scanner found for strategy_id='{strategy_id}' in {scanners_dir}"
    )


def list_strategies() -> List[str]:
    """Return all discoverable strategy IDs from the scanners directory."""
    strategy_ids = []
    scanners_dir = SCANNERS_DIR
    if not scanners_dir.exists():
        return strategy_ids
    for py_file in sorted(scanners_dir.glob("*.py")):
        if py_file.name.startswith("_"):
            continue
        try:
            spec = importlib.util.spec_from_file_location(
                py_file.stem, str(py_file)
            )
            if spec is None or spec.loader is None:
                continue
            mod = importlib.util.module_from_spec(spec)
            sys.modules[py_file.stem] = mod
            spec.loader.exec_module(mod)
            sid = getattr(mod, "STRATEGY_ID", None)
            if sid:
                strategy_ids.append(sid)
        except Exception:
            continue
    return sorted(strategy_ids)


# ── Parameter extraction ───────────────────────────────────────────────────

def extract_params(strategy_id: str) -> Dict[str, Any]:
    """
    Extract numeric parameters for a strategy.

    First looks for a module-level PARAMS dict. If absent, auto-detects all
    uppercase numeric constants (excluding known non-param names).

    Returns dict of param_name -> default_value (all float/int values).
    """
    mod, _ = _find_scanner_module(strategy_id)

    # Preferred: explicit PARAMS dict
    params = getattr(mod, "PARAMS", None)
    if params is not None and isinstance(params, dict):
        return {k: v for k, v in params.items()
                if isinstance(v, (int, float)) and not isinstance(v, bool)}

    # Fallback: auto-detect uppercase numeric constants
    auto_params = {}
    for name in dir(mod):
        if name in NON_PARAM_NAMES:
            continue
        if not name.isupper() or name.startswith("_"):
            continue
        val = getattr(mod, name)
        if isinstance(val, (int, float)) and not isinstance(val, bool):
            auto_params[name] = val

    return auto_params


# ── Parameter variation generation ─────────────────────────────────────────

def generate_variations(
    params: Dict[str, Any],
    delta_pct: float = DEFAULT_DELTA_PCT,
) -> List[Dict[str, Any]]:
    """
    Generate all ±delta_pct variations for each parameter.

    Each variation is a dict of {param_name: new_value}. Only the varied
    parameter differs from baseline; all others stay at default.

    For integer params, new values are rounded to nearest int (min 1).

    Returns a list of variation dicts, one per (param, direction) pair.
    """
    variations = []
    for name, default in sorted(params.items()):
        is_int = isinstance(default, int)

        # Low variation (-delta_pct)
        low_val = default * (1.0 - delta_pct)
        if is_int:
            low_val = max(1, int(round(low_val)))
        variations.append({name: low_val})

        # High variation (+delta_pct)
        high_val = default * (1.0 + delta_pct)
        if is_int:
            high_val = max(1, int(round(high_val)))
        variations.append({name: high_val})

    return variations


# ── Backtest execution with parameter overrides ────────────────────────────

def _run_backtest_with_params(
    module: Any,
    df: pd.DataFrame,
    ticker: str,
    param_overrides: Dict[str, Any],
    long_only: bool = False,
) -> List[Dict]:
    """
    Run a scanner's run_backtest with temporary parameter overrides.

    Sets module-level attributes to override values before calling run_backtest,
    then restores originals. This works because scan() and run_backtest()
    reference module globals at call time (not definition time).

    IMPORTANT: parameters used as Python function defaults (e.g.,
    `def _atr(df, period=14)`) are NOT affected by module-level overrides
    unless the caller passes them explicitly. Scanners should use module-level
    constants as explicit arguments: `_atr(df, ATR_PERIOD)`.
    """
    originals = {}
    for name, value in param_overrides.items():
        originals[name] = getattr(module, name, None)
        setattr(module, name, value)

    try:
        # Re-obtain run_backtest from the module (ensures fresh reference)
        run_bt = getattr(module, "run_backtest", None)
        if run_bt is None:
            raise AttributeError(
                f"Scanner module for {getattr(module, 'STRATEGY_ID', '?')} "
                f"has no run_backtest function"
            )
        # Call with explicit ticker and long_only
        trades = run_bt(df.copy(), ticker, long_only=long_only)
        return trades if trades else []
    finally:
        # Restore original values
        for name, original in originals.items():
            if original is None:
                try:
                    delattr(module, name)
                except (AttributeError, TypeError):
                    pass
            else:
                setattr(module, name, original)


def _net_r(trades: List[Dict]) -> float:
    """Sum of r_multiple across all trades."""
    total = 0.0
    for t in trades:
        r = t.get("r_multiple", 0)
        try:
            total += float(r)
        except (ValueError, TypeError):
            pass
    return total


# ── Main sensitivity test ──────────────────────────────────────────────────

def run_sensitivity_test(
    strategy_id: str,
    df: pd.DataFrame,
    ticker: str,
    delta_pct: float = DEFAULT_DELTA_PCT,
    long_only: bool = False,
    params: Optional[Dict[str, Any]] = None,
) -> Dict:
    """
    Run the full G2 parameter sensitivity test for a strategy on one ticker.

    Args:
        strategy_id: e.g. 'STR-AD-keltner'
        df: OHLCV DataFrame (must have 'open','high','low','close' columns)
        ticker: ticker symbol for context
        delta_pct: variation magnitude (default 0.20 = ±20%)
        long_only: pass through to run_backtest
        params: override extracted params (for testing)

    Returns dict with:
        strategy_id, params, baseline_net_r, variations (list of per-variation
        results), robustness_score, passes, threshold, explanation.
    """
    mod, mod_path = _find_scanner_module(strategy_id)

    # Extract parameters
    if params is not None:
        param_dict = {k: v for k, v in params.items()
                      if isinstance(v, (int, float)) and not isinstance(v, bool)}
    else:
        param_dict = extract_params(strategy_id)

    if not param_dict:
        return {
            "strategy_id": strategy_id,
            "params": {},
            "baseline_net_r": None,
            "variations": [],
            "robustness_score": None,
            "passes": None,
            "threshold": PASS_THRESHOLD,
            "explanation": f"{strategy_id}: no numeric parameters found for sensitivity testing",
            "skipped": True,
        }

    # Baseline: run with default parameters (no overrides)
    baseline_trades = _run_backtest_with_params(mod, df, ticker, {}, long_only)
    baseline_net_r = _net_r(baseline_trades)

    # Generate variations
    all_variations = generate_variations(param_dict, delta_pct)

    # Run each variation
    variation_results = []
    for var in all_variations:
        param_name = list(var.keys())[0]
        varied_value = var[param_name]
        default_value = param_dict[param_name]

        try:
            trades = _run_backtest_with_params(mod, df, ticker, var, long_only)
            net_r_val = _net_r(trades)
            positive = net_r_val > 0
            error = None
        except Exception as e:
            net_r_val = None
            positive = False
            error = str(e)

        variation_results.append({
            "param": param_name,
            "default": default_value,
            "varied": varied_value,
            "delta_pct": round((varied_value - default_value) / default_value * 100, 1),
            "net_r": net_r_val,
            "net_r_positive": positive,
            "error": error,
        })

    # Compute robustness score
    valid_variations = [v for v in variation_results if v["error"] is None]
    positive_count = 0
    if valid_variations:
        positive_count = sum(1 for v in valid_variations if v["net_r_positive"])
        robustness_score = positive_count / len(valid_variations)
    else:
        robustness_score = None

    passes = robustness_score is not None and robustness_score >= PASS_THRESHOLD

    # Build explanation
    if passes:
        explanation = (
            f"{strategy_id}: robustness_score={robustness_score:.2f} >= "
            f"{PASS_THRESHOLD} — strategy survives {positive_count}/{len(valid_variations)} "
            f"parameter variations"
        )
    elif robustness_score is not None:
        explanation = (
            f"{strategy_id}: robustness_score={robustness_score:.2f} < "
            f"{PASS_THRESHOLD} — strategy fails {len(valid_variations) - positive_count}/{len(valid_variations)} "
            f"parameter variations"
        )
    else:
        explanation = f"{strategy_id}: all parameter variations errored; cannot compute robustness"

    return {
        "strategy_id": strategy_id,
        "params": param_dict,
        "baseline_net_r": baseline_net_r,
        "baseline_trades": len(baseline_trades),
        "variations": variation_results,
        "robustness_score": robustness_score,
        "passes": passes,
        "threshold": PASS_THRESHOLD,
        "explanation": explanation,
    }


# ── G2 gate evaluation ─────────────────────────────────────────────────────

def evaluate_gate(
    strategy_id: str,
    df: pd.DataFrame,
    ticker: str = "TEST",
    delta_pct: float = DEFAULT_DELTA_PCT,
    long_only: bool = False,
    threshold: float = PASS_THRESHOLD,
) -> Dict:
    """
    Run the full G2 gate check and return a pass/fail decision.

    Convenience wrapper around run_sensitivity_test with threshold check.
    """
    result = run_sensitivity_test(
        strategy_id=strategy_id,
        df=df,
        ticker=ticker,
        delta_pct=delta_pct,
        long_only=long_only,
    )
    # Re-evaluate with custom threshold if different from default
    if threshold != PASS_THRESHOLD:
        score = result["robustness_score"]
        result["passes"] = score is not None and score >= threshold
        result["threshold"] = threshold
        if result["passes"]:
            result["explanation"] = (
                f"{strategy_id}: robustness_score={score:.2f} >= {threshold}"
            )
        elif score is not None:
            result["explanation"] = (
                f"{strategy_id}: robustness_score={score:.2f} < {threshold}"
            )
    return result


# ── Batch evaluation ───────────────────────────────────────────────────────

def batch_evaluate(
    strategy_ids: List[str],
    df: pd.DataFrame,
    ticker: str = "TEST",
    delta_pct: float = DEFAULT_DELTA_PCT,
    long_only: bool = False,
) -> List[Dict]:
    """Run G2 gate on multiple strategies against the same dataset."""
    results = []
    for sid in strategy_ids:
        try:
            result = evaluate_gate(
                strategy_id=sid,
                df=df,
                ticker=ticker,
                delta_pct=delta_pct,
                long_only=long_only,
            )
        except Exception as e:
            result = {
                "strategy_id": sid,
                "passes": False,
                "error": str(e),
                "skipped": True,
            }
        results.append(result)
    return results


# ── Utility: generate synthetic OHLCV for testing ──────────────────────────

def make_synthetic_ohlcv(
    n_bars: int = 500,
    trend_strength: float = 0.0005,
    volatility: float = 0.015,
    seed: int = 42,
) -> pd.DataFrame:
    """
    Generate synthetic OHLCV data for G2 testing.

    Produces a random walk with configurable trend and volatility.
    """
    rng = np.random.default_rng(seed)
    returns = rng.normal(trend_strength, volatility, n_bars)
    closes = 100.0 * np.exp(np.cumsum(returns))
    closes = np.maximum(closes, 0.01)

    high_factor = 1.0 + rng.uniform(0.002, 0.015, n_bars)
    low_factor = 1.0 - rng.uniform(0.002, 0.015, n_bars)

    df = pd.DataFrame({
        "open": np.roll(closes, 1),
        "high": closes * high_factor,
        "low": closes * low_factor,
        "close": closes,
        "volume": rng.integers(1000, 100000, n_bars),
    })
    df.iloc[0, df.columns.get_loc("open")] = closes[0]
    df.index = pd.date_range("2020-01-01", periods=n_bars, freq="D")

    return df


# ── CLI ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(
        description="G2 Parameter Sensitivity Gate"
    )
    ap.add_argument(
        "strategy_id", nargs="?", default=None,
        help="Strategy ID to test (e.g. STR-AD-keltner)"
    )
    ap.add_argument(
        "--list", action="store_true",
        help="List all discoverable strategy IDs"
    )
    ap.add_argument(
        "--delta", type=float, default=DEFAULT_DELTA_PCT,
        help=f"Variation magnitude (default: {DEFAULT_DELTA_PCT})"
    )
    ap.add_argument(
        "--threshold", type=float, default=PASS_THRESHOLD,
        help=f"Pass threshold (default: {PASS_THRESHOLD})"
    )
    ap.add_argument(
        "--long-only", action="store_true",
        help="Pass long_only=True to run_backtest"
    )
    ap.add_argument(
        "--synthetic-bars", type=int, default=500,
        help="Number of bars for synthetic test data"
    )
    ap.add_argument(
        "--all", action="store_true",
        help="Run G2 on all discoverable strategies"
    )
    args = ap.parse_args()

    if args.list:
        strategies = list_strategies()
        print(f"Discovered {len(strategies)} strategies:")
        for sid in strategies:
            print(f"  {sid}")
        sys.exit(0)

    # Default strategy for quick test
    strategy_id = args.strategy_id
    if strategy_id is None and not args.all:
        strategy_id = "STR-AD-keltner"
        print(f"No strategy_id provided, defaulting to {strategy_id}")

    # Generate synthetic test data
    df = make_synthetic_ohlcv(n_bars=args.synthetic_bars)

    if args.all:
        strategies = list_strategies()
        if not strategies:
            print("No strategies discovered.")
            sys.exit(1)
        print(f"Running G2 on {len(strategies)} strategies...\n")
        results = batch_evaluate(
            strategies, df, ticker="SYNTH",
            delta_pct=args.delta, long_only=args.long_only,
        )
        for r in results:
            status = "PASS" if r.get("passes") else ("SKIP" if r.get("skipped") else "FAIL")
            sid = r["strategy_id"]
            score = r.get("robustness_score")
            if score is not None:
                print(f"  [{status}] {sid}: robustness={score:.2f}")
            else:
                print(f"  [{status}] {sid}: {r.get('explanation', r.get('error', '?'))}")
    else:
        result = evaluate_gate(
            strategy_id=strategy_id,
            df=df,
            ticker="SYNTH",
            delta_pct=args.delta,
            long_only=args.long_only,
            threshold=args.threshold,
        )
        import json as _json
        print(_json.dumps(result, indent=2, default=str))