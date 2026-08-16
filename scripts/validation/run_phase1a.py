"""
run_phase1a.py — HermesForge Phase 1A Master Runner (US-055/US-056)

Runs all four strategy scanners across the universe, saves results CSVs,
and prints a summary with kill/pass/watch classifications per ADR-004.

Usage:
    python3 scripts/validation/run_phase1a.py [--fetch] [--strategy STR_ID]

Options:
    --fetch       Re-fetch market data before scanning (slow, ~10min)
    --strategy    Run only one strategy (a/b/c/d)
"""

import sys
import json
import argparse
import pathlib
import datetime
import importlib.util
import pandas as pd

try:
    from scipy import stats as _scipy_stats
except Exception:  # pragma: no cover
    _scipy_stats = None

# Paths
REPO_ROOT = pathlib.Path(__file__).parent.parent.parent
RESULTS_DIR = REPO_ROOT / "scripts" / "validation" / "results"
sys.path.insert(0, str(REPO_ROOT / "scripts" / "validation"))

from fetch_data import load_all, fetch_all
from universe import get_universe
from scanners.scanner_a_ma_pullback import scan as scan_a
from scanners.scanner_b_macd_divergence import scan as scan_b
from scanners.scanner_c_breakout_volume import scan as scan_c
from scanners.scanner_d_sr_reversal import scan as scan_d
from scanners.scanner_e_rsi_mean_reversion import scan as scan_e
from scanners.scanner_g_relative_strength import scan as scan_g
from scanners.scanner_f_bollinger_squeeze import scan as scan_f
from scanners.scanner_h_first_pullback_trend_swing import scan as scan_h
from scanners.scanner_i_adaptive_trend import scan as scan_i
from scanners.scanner_j_eufearia_cci import scan as scan_j

STRATEGY_MAP = {
    "a": ("STR-A-ma-pullback-fibonacci",        scan_a),
    "b": ("STR-B-macd-histogram-divergence",    scan_b),
    "c": ("STR-C-breakout-volume",              scan_c),
    "d": ("STR-D-sr-role-reversal",             scan_d),
    "e": ("STR-E-rsi-mean-reversion",           scan_e),
    "g": ("STR-G-relative-strength-rotation",   scan_g),
    "f": ("STR-F-bollinger-squeeze-breakout",   scan_f),
    "h": ("STR-20260726-first-pullback-trend-swing", scan_h),
    "i": ("STR-20260728-adaptive-trend",       scan_i),
    "j": ("STR-20260726-eufearia-cci-reversal", scan_j),
}

# ADR-004 thresholds
KILL_SIGNALS_PER_YEAR  = 12
KILL_AVG_R             = 0.2
WATCH_SIGNALS_PER_YEAR = 25
PASS_AVG_R             = 0.6
FRICTION_FLAG_R        = 0.5
SUBPERIODS             = ["period1_bull", "period2_bear", "period3_current"]


def run_scanner(strategy_key: str, data: dict[str, pd.DataFrame]) -> pd.DataFrame:
    strategy_id, scan_fn = STRATEGY_MAP[strategy_key]
    print(f"\n{'='*60}")
    print(f"Scanning {strategy_id}...")
    all_signals = []
    for ticker, df in data.items():
        try:
            signals = scan_fn(df, ticker)
            all_signals.extend(signals)
        except Exception as e:
            print(f"  ERROR on {ticker}: {e}")
    if not all_signals:
        print(f"  No signals found.")
        return pd.DataFrame()
    results = pd.DataFrame(all_signals)
    results["strategy_id"] = strategy_id
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = RESULTS_DIR / f"{strategy_id}-phase1a.csv"
    results.to_csv(out_path, index=False)
    print(f"  Saved {len(results)} signals → {out_path.name}")
    return results


def classify(signals_per_year: float, avg_r: float, sub_positive: int) -> str:
    if signals_per_year < KILL_SIGNALS_PER_YEAR or avg_r < KILL_AVG_R:
        return "❌ KILL"
    if signals_per_year >= WATCH_SIGNALS_PER_YEAR and avg_r >= PASS_AVG_R and sub_positive >= 2:
        return "✅ PASS"
    return "⚠️  WATCH"


def summarize(results: pd.DataFrame, strategy_id: str) -> dict:
    if results.empty:
        return {
            "strategy": strategy_id, "total_signals": 0,
            "signals_per_year": 0.0, "avg_r": 0.0, "median_r": 0.0,
            "win_rate": 0.0, "sub_positive": 0, "classification": "❌ KILL",
            "friction_flag": False, "p_value": 1.0, "t_stat": 0.0,
            "mean_r": 0.0,
        }
    # Date range
    results["date"] = pd.to_datetime(results["date"])
    years = max((results["date"].max() - results["date"].min()).days / 365.25, 0.1)
    signals_per_year = len(results) / years
    avg_r_val    = float(results["r_multiple"].mean())       # type: ignore[arg-type]
    median_r_val = float(results["r_multiple"].median())     # type: ignore[arg-type]
    win_rate_val = float((results["r_multiple"] > 0).mean()) # type: ignore[arg-type]

    # Sub-period analysis
    sub_positive = 0
    for sp in SUBPERIODS:
        sub = results[results["subperiod"] == sp]
        if len(sub) >= 3 and float(sub["r_multiple"].mean()) > 0:  # type: ignore[arg-type]
            sub_positive += 1

    classification = classify(signals_per_year, avg_r_val, sub_positive)
    friction_flag = avg_r_val < FRICTION_FLAG_R

    # Statistical significance — one-sample t-test, H0: mean R = 0
    r_vals = results["r_multiple"].dropna().astype(float).values
    p_value = 1.0
    t_stat = 0.0
    if len(r_vals) >= 3:
        try:
            if _scipy_stats is not None:
                t_stat, p_value = _scipy_stats.ttest_1samp(r_vals, 0.0)
                if p_value is None or r_vals.std(ddof=1) == 0:
                    t_stat, p_value = (0.0, 1.0) if avg_r_val == 0 else (float('inf'), 0.0)
                t_stat = float(t_stat)
                p_value = float(p_value)
            else:
                from statistics import NormalDist
                std_r = float(r_vals.std(ddof=1))
                t_stat = (avg_r_val / (std_r / (len(r_vals) ** 0.5))) if std_r > 0 else 0.0
                p_value = 2 * (1 - NormalDist(0, 1).cdf(abs(t_stat))) if abs(t_stat) < 100 else 0.0
        except Exception:
            p_value, t_stat = 1.0, 0.0

    return {
        "strategy": strategy_id,
        "total_signals": len(results),
        "signals_per_year": round(signals_per_year, 1),
        "avg_r": round(avg_r_val, 3),
        "mean_r": round(avg_r_val, 3),
        "median_r": round(median_r_val, 3),
        "win_rate": round(win_rate_val, 3),
        "sub_positive": sub_positive,
        "classification": classification,
        "friction_flag": friction_flag,
        "p_value": round(p_value, 4),
        "t_stat": round(t_stat, 3),
    }


def print_summary(summaries: list[dict]):
    print(f"\n{'='*60}")
    print("PHASE 1A RESULTS SUMMARY")
    print(f"{'='*60}")
    print(f"{'Strategy':<40} {'Sig/Yr':>7} {'AvgR':>7} {'WinR':>7} {'SubPos':>7} {'Friction':>9} {'Status'}")
    print("-" * 100)
    for s in summaries:
        friction = "⚠️ FLAG" if s["friction_flag"] else "ok"
        print(
            f"{s['strategy']:<40} {s['signals_per_year']:>7.1f} {s['avg_r']:>7.3f} "
            f"{s['win_rate']:>7.1%} {s['sub_positive']:>7}/3 {friction:>9}  {s['classification']}"
        )
    print(f"\nKill criteria (ADR-004): <{KILL_SIGNALS_PER_YEAR} sig/yr OR avg R < {KILL_AVG_R}")
    print(f"Pass criteria:           >={WATCH_SIGNALS_PER_YEAR} sig/yr AND avg R >= {PASS_AVG_R} AND positive in >=2 sub-periods")
    print(f"Watch band:              Everything in between")
    print(f"Friction flag:           avg R < {FRICTION_FLAG_R} (check after adding costs in Phase 1B)")


def write_report(summaries: list[dict]):
    lines = [
        "# Phase 1A Results Summary",
        f"Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "",
        "## Classification Criteria (ADR-004)",
        f"- **Kill**: < {KILL_SIGNALS_PER_YEAR} signals/year OR avg R < {KILL_AVG_R} (frictionless)",
        f"- **Watch**: between kill and pass thresholds",
        f"- **Pass**: >= {WATCH_SIGNALS_PER_YEAR} signals/year AND avg R >= {PASS_AVG_R} AND positive in >= 2 of 3 sub-periods",
        f"- **Friction flag**: avg R < {FRICTION_FLAG_R} — check after adding costs in Phase 1B",
        "",
        "## Results",
        "",
        "| Strategy | Sig/Yr | Avg R | Median R | Win Rate | Sub-Periods+ | Friction | Status |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for s in summaries:
        friction = "⚠️" if s["friction_flag"] else "✓"
        lines.append(
            f"| {s['strategy']} | {s['signals_per_year']} | {s['avg_r']} | {s['median_r']} | "
            f"{s['win_rate']:.1%} | {s['sub_positive']}/3 | {friction} | {s['classification']} |"
        )
    lines += [
        "",
        "## Decisions",
        "",
    ]
    for s in summaries:
        decision = s['classification']
        lines.append(f"### {s['strategy']}")
        lines.append(f"**Decision:** {decision}")
        if "KILL" in decision:
            lines.append("- Signals too rare or edge too weak. Drop or major revision before Phase 1B.")
        elif "WATCH" in decision:
            lines.append("- Marginal results. Advance to Phase 1B with caution flag. Review operationalization.")
        else:
            lines.append("- Sufficient frequency and edge. Advance to Phase 1B for perturbation testing.")
        if s["friction_flag"]:
            lines.append("- ⚠️ Friction flag: avg R below 0.5 — verify edge survives commission + slippage in Phase 1B.")
        lines.append("")

    out_path = RESULTS_DIR / "phase1a-summary.md"
    out_path.write_text("\n".join(lines))
    print(f"\nReport saved → {out_path}")


def _load_scanner_module(scanner_path: str):
    """Dynamically import a scanner module from a file path.

    Returns (module, scan_fn_name). Detects whether the module exposes a
    `scan` function (per-ticker: scan(df, ticker)) or a `scan_all` / `scan`
    batch function (scan(data_dict)).
    """
    p = pathlib.Path(scanner_path).expanduser().resolve()
    if not p.exists():
        raise FileNotFoundError(f"Scanner file not found: {p}")
    mod_name = p.stem
    # Ensure scanners dir is importable so intra-scanner imports resolve
    scanners_dir = REPO_ROOT / "scripts" / "validation" / "scanners"
    for d in [str(REPO_ROOT / "scripts" / "validation"), str(scanners_dir)]:
        if d not in sys.path:
            sys.path.insert(0, d)
    spec = importlib.util.spec_from_file_location(mod_name, str(p))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    if hasattr(module, "scan"):
        return module, "scan"
    raise AttributeError(f"Scanner {p.name} exposes no `scan` function")


def run_external_scanner(scanner_path: str, data: dict, strategy_id: str) -> pd.DataFrame:
    """Run a scanner file across the universe and return a results DataFrame."""
    module, scan_fn_name = _load_scanner_module(scanner_path)
    scan_fn = getattr(module, scan_fn_name)
    import inspect
    sig = inspect.signature(scan_fn)
    batch_mode = len(sig.parameters) == 1  # scan(data_dict)

    print(f"\n{'='*60}")
    print(f"Scanning {strategy_id} (file: {pathlib.Path(scanner_path).name})...")
    all_signals = []
    if batch_mode:
        try:
            sigs = scan_fn(data)
            if sigs:
                all_signals.extend(sigs)
        except Exception as e:
            print(f"  ERROR (batch): {e}")
    else:
        for ticker, df in data.items():
            try:
                signals = scan_fn(df, ticker)
                if signals:
                    all_signals.extend(signals)
            except Exception as e:
                print(f"  ERROR on {ticker}: {e}")
    if not all_signals:
        print("  No signals found.")
        return pd.DataFrame()
    results = pd.DataFrame(all_signals)
    results["strategy_id"] = strategy_id
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = RESULTS_DIR / f"{strategy_id}-phase1a.csv"
    results.to_csv(out_path, index=False)
    print(f"  Saved {len(results)} signals -> {out_path.name}")
    return results


def main():
    parser = argparse.ArgumentParser(description="Run HermesForge Phase 1A signal scanners")
    parser.add_argument("--fetch", action="store_true", help="Fetch/refresh market data first")
    parser.add_argument("--strategy", choices=["a","b","c","d","e","g","f","h","i","j"], help="Run only one built-in strategy")
    parser.add_argument("--scanner", type=str, default=None,
                        help="Path to a scanner .py file to run (must expose scan(df, ticker) or scan(data_dict))")
    parser.add_argument("--strategy-id", type=str, default=None,
                        help="Override strategy_id label for --scanner runs")
    parser.add_argument("--crypto", action="store_true",
                        help="Load crypto universe (instead of stocks) for --scanner runs")
    parser.add_argument("--json", action="store_true", help="Emit JSON summary to stdout")
    args = parser.parse_args()

    # ── External scanner mode ────────────────────────────────────────────
    if args.scanner:
        if args.fetch:
            print("Fetching market data...")
            fetch_all()
        print("Loading cached data...")
        if args.crypto:
            sys.path.insert(0, str(REPO_ROOT / "scripts" / "paper_trading"))
            from fetch_crypto_data import load_all as load_all_crypto
            data = load_all_crypto()
            label = "crypto"
        else:
            data = load_all()
            label = "stock"
        if not data:
            print(f"ERROR: No cached {label} data found. Run the relevant fetcher first.")
            sys.exit(1)
        print(f"Loaded {len(data)} {label} tickers.")

        strategy_id = args.strategy_id or pathlib.Path(args.scanner).stem
        results = run_external_scanner(args.scanner, data, strategy_id)
        summary = summarize(results, strategy_id)
        if args.json:
            print(json.dumps(summary, default=str, indent=2))
        else:
            print_summary([summary])
        return

    # ── Built-in strategy mode ────────────────────────────────────────────
    if args.fetch:
        print("Fetching market data...")
        fetch_all()

    print("Loading cached data...")
    data = load_all()
    if not data:
        print("ERROR: No cached data found. Run with --fetch first.")
        sys.exit(1)
    print(f"Loaded {len(data)} tickers.")

    keys = [args.strategy] if args.strategy else list(STRATEGY_MAP.keys())
    summaries = []
    for key in keys:
        results = run_scanner(key, data)
        strategy_id = STRATEGY_MAP[key][0]
        summary = summarize(results, strategy_id)
        summaries.append(summary)

    if args.json:
        print(json.dumps(summaries, default=str, indent=2))
    else:
        print_summary(summaries)
        if len(summaries) == len(STRATEGY_MAP):
            write_report(summaries)


if __name__ == "__main__":
    main()
