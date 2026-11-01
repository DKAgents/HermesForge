#!/usr/bin/env python3
"""
US-114 Walk-Forward Validation — 19 Strategy Scan
==================================================
Gate that prevents overfit strategies from contaminating paper trading.

For each strategy:
  1. Load Phase 1A CSV (individual trades with R multiples)
  2. Sort chronologically by entry date
  3. Split 60% in-sample (IS), 40% out-of-sample (OOS)
  4. Compute: trade count, win rate, avg R, profit factor, expectancy
  5. Flag significant OOS underperformance
  6. Bootstrap CI / t-test on OOS R multiples (H0: mean R <= 0)
  7. Verdict: PASS | FAIL | INSUFFICIENT | NO-DATA

Run: python3 ~/HermesForge/scripts/validation/walk_forward_us114.py
"""

import os
import sys
import pathlib
import warnings
import numpy as np
import pandas as pd
from scipy import stats as sp_stats

warnings.filterwarnings("ignore", category=FutureWarning)

# US-173 fill-convention import (same package dir).
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fill_convention import (  # noqa: E402
    FILL_CONVENTION,
    PHASE1A_VERSION,
    apply_next_open_entry,
    versioned_phase1a_name,
)

# --shim-legacy-close-entry flag: when True, permit scoring a legacy close-entry
# CSV by re-rating each trade through apply_next_open_entry. Default is False =
# REFUSE (fail-closed) — a legacy CSV lacking `fill_convention` must never be
# silently re-scored under a next-open model it was never tested on (§1.4 pt3).
SHIM_LEGACY_CLOSE_ENTRY = False

_MARKET_DATA_DIR = pathlib.Path.home() / ".hermes" / "market_data"

# ── Config ──────────────────────────────────────────────────────────────────
RESULTS_DIR = os.path.expanduser("~/HermesForge/scripts/validation/results")
OUTPUT_PATH = os.path.expanduser("~/HermesForge/code/forge-loop/AUDIT-backtester-US114.md")

TARGET_STRATS = [
    "STR-R", "STR-S", "STR-T", "STR-U", "STR-V", "STR-W",
    "STR-X", "STR-Y", "STR-Z", "STR-AA", "STR-AB", "STR-AC",
    "STR-AD", "STR-AE", "STR-AF", "STR-AG", "STR-AH", "STR-AI", "STR-AJ",
]

# Thresholds (from US-114 spec + US-109 lessons)
MIN_OOS_TRADES = 10
OOS_AVGR_DEGRADE = 0.1       # OOS avg R < IS avg R - 0.1 → flag
OOS_WINRATE_DEGRADE = 5.0    # OOS win rate < IS win rate - 5 pp → flag
OOS_PF_MIN = 1.0              # OOS profit factor < 1.0 → flag
P_THRESHOLD = 0.05            # p < 0.05 for OOS mean R > 0

BOOTSTRAP_ITERATIONS = 10000
BOOTSTRAP_SEED = 42

# ── Helpers ──────────────────────────────────────────────────────────────────

def _shim_legacy_close_entry(df: pd.DataFrame) -> pd.DataFrame:
    """Re-rate a legacy close-entry CSV through apply_next_open_entry (US-173).

    The backward-compatibility bridge of §1.4: given a pre-US-173 CSV whose
    entry_price is the signal-bar CLOSE, this loads each ticker's cached OHLC
    bars and re-rates entry to open[signal+1], charging the adverse drift.
    Rows whose ticker data are unavailable fall back to the original close-entry
    R but are stamped `lookahead_shim=False` so the residue is visible.
    """
    cache = {}
    out_rows = []

    for _, row in df.iterrows():
        sig = row.to_dict()
        direction = str(sig.get("direction", "long"))
        sym = sig.get("symbol") or sig.get("ticker")

        bars = None
        if sym and sym not in cache:
            p = _MARKET_DATA_DIR / f"{sym}.parquet"
            try:
                b = pd.read_parquet(p)
                if "Date" in b.columns:
                    b = b.set_index("Date")
                if not isinstance(b.index, pd.DatetimeIndex):
                    b.index = pd.to_datetime(b.index)
                cache[sym] = b
            except Exception:
                cache[sym] = None
        if sym in cache:
            bars = cache[sym]

        if bars is not None:
            sig = apply_next_open_entry(sig, bars, direction)
            sig.setdefault("lookahead_shim", True)
        else:
            sig["fill_convention"] = FILL_CONVENTION
            sig["lookahead_shim"] = False
            sig["entry_drift_r"] = float("nan")
        out_rows.append(sig)

    return pd.DataFrame(out_rows)


def load_trades(strategy_id):
    """Load Phase 1A CSV. Returns sorted DataFrame or None.

    US-173: prefers the versioned `-v4` (next-open) CSV. Any CSV lacking the
    `fill_convention` column is a legacy close-entry backtest and is REFUSED
    (fail-closed) unless `--shim-legacy-close-entry` is set, in which case it is
    re-rated through the fill_convention shim. Historic close-entry numbers are
    never silently re-scored under a next-open model (§1.4 pt3).
    """
    candidates = [
        versioned_phase1a_name(strategy_id),      # STR-X-stocks-phase1a-v4.csv
        f"{strategy_id}-stocks-phase1a.csv",      # legacy unversioned
    ]
    df = None
    fname_used = None
    for fname in candidates:
        fpath = os.path.join(RESULTS_DIR, fname)
        if os.path.isfile(fpath):
            try:
                df = pd.read_csv(fpath, parse_dates=["date"])
            except Exception as e:
                print(f"  WARN: {fpath} failed to parse: {e}")
                return None
            fname_used = fname
            break

    if df is None:
        return None

    if df.empty or len(df) < 2:  # header-only
        return None

    # Drop any rows with missing r_multiple or date
    df = df.dropna(subset=["r_multiple", "date"])
    if df.empty:
        return None

    # US-173 fill-convention gate (fail-closed).
    if "fill_convention" not in df.columns:
        if not SHIM_LEGACY_CLOSE_ENTRY:
            raise RuntimeError(
                f"REFUSING to score legacy close-entry CSV '{fname_used}' for "
                f"{strategy_id}: missing 'fill_convention' column. This is a "
                f"pre-US-173 close-entry backtest and must not be silently "
                f"re-scored under a next-open fill model it was never tested on "
                f"(§1.4 pt3). Re-run the scanner to emit '{PHASE1A_VERSION}' "
                f"(next-open), or pass --shim-legacy-close-entry to re-rate via "
                f"the fill_convention shim."
            )
        df = _shim_legacy_close_entry(df)

    # Sort chronologically by entry date
    df = df.sort_values("date").reset_index(drop=True)
    return df


def compute_metrics(trades):
    """Compute a dict of metrics from a Series of R multiples."""
    if trades.empty:
        return {
            "n_trades": 0,
            "win_rate": 0.0,
            "avg_r": 0.0,
            "profit_factor": 0.0,
            "expectancy": 0.0,
            "sum_r": 0.0,
        }

    r = trades["r_multiple"].values
    n = len(r)

    winners = r[r > 0]
    losers = r[r <= 0]
    n_wins = len(winners)
    n_losses = len(losers)

    win_rate = n_wins / n * 100.0 if n > 0 else 0.0
    avg_r = float(np.mean(r))
    sum_r = float(np.sum(r))

    gross_profit = float(np.sum(winners)) if n_wins > 0 else 0.0
    gross_loss = float(np.abs(np.sum(losers))) if n_losses > 0 else 0.0

    profit_factor = gross_profit / gross_loss if gross_loss > 1e-10 else (
        float("inf") if gross_profit > 0 else 0.0
    )

    avg_win_r = float(np.mean(winners)) if n_wins > 0 else 0.0
    avg_loss_r = float(np.mean(losers)) if n_losses > 0 else 0.0
    expectancy = (win_rate / 100.0 * avg_win_r) - (
        (1 - win_rate / 100.0) * abs(avg_loss_r)
    )

    return {
        "n_trades": n,
        "win_rate": win_rate,
        "avg_r": avg_r,
        "profit_factor": profit_factor,
        "expectancy": expectancy,
        "sum_r": sum_r,
    }


def bootstrap_test(r_values, n_iter=BOOTSTRAP_ITERATIONS, seed=BOOTSTRAP_SEED):
    """
    Bootstrap test: H0: mean R <= 0, Ha: mean R > 0.
    Returns bootstrap p-value and 95% CI of the mean.
    """
    rng = np.random.default_rng(seed)
    n = len(r_values)
    if n < MIN_OOS_TRADES:
        return 1.0, (-99.0, 99.0)  # inconclusive

    # Generate bootstrap distribution of the mean
    boot_means = np.zeros(n_iter)
    for i in range(n_iter):
        sample = rng.choice(r_values, size=n, replace=True)
        boot_means[i] = np.mean(sample)

    # Percentile 95% CI
    ci_low, ci_high = np.percentile(boot_means, [2.5, 97.5])

    # p-value: proportion of bootstrapped means <= 0
    p_value = np.mean(boot_means <= 0.0)

    return p_value, (ci_low, ci_high)


def t_test_oos(r_values):
    """One-sample t-test: H0: mean R = 0, Ha: mean R > 0 (one-sided)."""
    n = len(r_values)
    if n < MIN_OOS_TRADES:
        return 1.0, (-99.0, 99.0)

    t_stat, p_two = sp_stats.ttest_1samp(r_values, 0.0, alternative="two-sided")
    # For one-sided (mean > 0): if t_stat > 0, p_one = p_two/2; else p_one = 1 - p_two/2
    if t_stat > 0:
        p_one = p_two / 2.0
    else:
        p_one = 1.0 - p_two / 2.0

    ci = sp_stats.t.interval(
        0.95, df=n - 1, loc=np.mean(r_values), scale=sp_stats.sem(r_values)
    )

    return p_one, ci


def evaluate_oos(oos_r, is_metrics, oos_metrics):
    """
    Evaluate whether OOS passes validation.
    Returns (verdict: str, flags: list of str, p_value: float).
    """
    flags = []

    if not isinstance(oos_r, (list, np.ndarray)):
        oos_r = oos_r["r_multiple"].values if isinstance(oos_r, pd.DataFrame) else np.array([])

    n_oos = len(oos_r)
    if n_oos < MIN_OOS_TRADES:
        return "INSUFFICIENT", ["too few OOS trades"], 1.0

    # 1. OOS avg R vs IS avg R
    if oos_metrics["avg_r"] < is_metrics["avg_r"] - OOS_AVGR_DEGRADE:
        flags.append(
            f"OOS avg R ({oos_metrics['avg_r']:.3f}) < IS avg R ({is_metrics['avg_r']:.3f}) - {OOS_AVGR_DEGRADE}"
        )

    # 2. OOS win rate vs IS win rate
    if oos_metrics["win_rate"] < is_metrics["win_rate"] - OOS_WINRATE_DEGRADE:
        flags.append(
            f"OOS win rate ({oos_metrics['win_rate']:.1f}%) < IS win rate ({is_metrics['win_rate']:.1f}%) - {OOS_WINRATE_DEGRADE}pp"
        )

    # 3. OOS profit factor < 1.0
    if oos_metrics["profit_factor"] < OOS_PF_MIN:
        flags.append(
            f"OOS profit factor ({oos_metrics['profit_factor']:.3f}) < {OOS_PF_MIN}"
        )

    # 4. Statistical significance: bootstrap first (more robust), t-test as cross-check
    boot_p, boot_ci = bootstrap_test(oos_r)
    t_p, t_ci = t_test_oos(oos_r)
    p_value = min(boot_p, t_p)  # conservative: use the more significant result
    
    # For the report, use bootstrap p-value as primary
    report_p = boot_p

    if report_p >= P_THRESHOLD:
        flags.append(
            f"OOS mean R not statistically significant (bootstrap p={report_p:.4f}, "
            f"t-test p={t_p:.4f})"
        )

    # Verdict
    if not flags:
        return "PASS", [], report_p
    
    # Check if any failures are critical (unprofitable OOS)
    critical_failures = [
        f for f in flags if "profit factor" in f.lower() or "not statistically significant" in f.lower()
    ]

    if critical_failures:
        return "FAIL", flags, report_p
    else:
        # Degradation-only flags but still profitable and significant
        # Still call FAIL since degradation is the core concern
        return "FAIL", flags, report_p


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    results = []
    headers = [
        "Strategy",
        "IS Trades",
        "IS Win%",
        "IS Avg R",
        "IS PF",
        "IS Expect.",
        "OOS Trades",
        "OOS Win%",
        "OOS Avg R",
        "OOS PF",
        "OOS Expect.",
        "OOS p-val",
        "OOS 95% CI",
        "Verdict",
        "Notes",
    ]

    print("=" * 100)
    print("US-114 WALK-FORWARD VALIDATION — 19 Strategy Scan")
    print("=" * 100)
    print()

    for sid in TARGET_STRATS:
        print(f"\n{'─'*80}")
        print(f"  {sid} ... ", end="", flush=True)

        df = load_trades(sid)
        if df is None:
            print("NO-DATA (file missing or empty)")
            results.append(
                [sid, "—", "—", "—", "—", "—", "—", "—", "—", "—", "—", "—", "—", "NO-DATA", "No Phase 1A CSV found"]
            )
            continue

        n_total = len(df)
        split_idx = int(n_total * 0.6)

        is_df = df.iloc[:split_idx].copy()
        oos_df = df.iloc[split_idx:].copy()

        is_metrics = compute_metrics(is_df)
        oos_metrics = compute_metrics(oos_df)

        date_range_is = f"{is_df['date'].min().date()} to {is_df['date'].max().date()}"
        date_range_oos = f"{oos_df['date'].min().date()} to {oos_df['date'].max().date()}"

        print(f"\n    IS ({date_range_is}): {is_metrics['n_trades']} trades")
        print(f"      Win Rate: {is_metrics['win_rate']:.1f}%  |  Avg R: {is_metrics['avg_r']:.4f}  |  "
              f"PF: {is_metrics['profit_factor']:.3f}  |  Expect.: {is_metrics['expectancy']:.4f}")
        print(f"    OOS ({date_range_oos}): {oos_metrics['n_trades']} trades")
        print(f"      Win Rate: {oos_metrics['win_rate']:.1f}%  |  Avg R: {oos_metrics['avg_r']:.4f}  |  "
              f"PF: {oos_metrics['profit_factor']:.3f}  |  Expect.: {oos_metrics['expectancy']:.4f}")

        oos_r = oos_df["r_multiple"].values
        verdict, flags, p_value = evaluate_oos(oos_r, is_metrics, oos_metrics)

        # CI
        _, ci = t_test_oos(oos_r)
        ci_str = f"[{ci[0]:.4f}, {ci[1]:.4f}]" if ci[0] > -50 else "—"

        notes = []
        if flags:
            for f in flags:
                notes.append(f)
                print(f"    ⚠  {f}")

        # Build summary line
        is_trades_str = str(is_metrics["n_trades"])
        is_win_str = f"{is_metrics['win_rate']:.1f}%"
        is_avgr_str = f"{is_metrics['avg_r']:.4f}"
        is_pf_str = f"{is_metrics['profit_factor']:.3f}" if is_metrics["profit_factor"] != float('inf') else "∞"
        is_exp_str = f"{is_metrics['expectancy']:.4f}"
        oos_trades_str = str(oos_metrics["n_trades"])
        oos_win_str = f"{oos_metrics['win_rate']:.1f}%"
        oos_avgr_str = f"{oos_metrics['avg_r']:.4f}"
        oos_pf_str = f"{oos_metrics['profit_factor']:.3f}" if oos_metrics["profit_factor"] != float('inf') else "∞"
        oos_exp_str = f"{oos_metrics['expectancy']:.4f}"
        p_str = f"{p_value:.4f}"

        results.append([
            sid,
            is_trades_str,
            is_win_str,
            is_avgr_str,
            is_pf_str,
            is_exp_str,
            oos_trades_str,
            oos_win_str,
            oos_avgr_str,
            oos_pf_str,
            oos_exp_str,
            p_str,
            ci_str,
            verdict,
            "; ".join(notes) if notes else "—",
        ])

        symbol = "✓" if verdict == "PASS" else ("✗" if verdict == "FAIL" else "?")
        print(f"    >> VERDICT: {verdict} {symbol}")

    # ── Write Report ──────────────────────────────────────────────────────
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

    report_lines = []
    report_lines.append("# US-114 Walk-Forward Validation Report")
    report_lines.append(f"**Generated:** {pd.Timestamp.now(tz='America/Los_Angeles').strftime('%Y-%m-%d %H:%M %Z')}")
    report_lines.append(f"**Job:** 19-strategy scan | IS=60% | OOS=40% | Bootstrap + t-test")
    report_lines.append(f"**Fill convention:** {FILL_CONVENTION} (US-173)")
    report_lines.append("")
    report_lines.append("## Summary Table")
    report_lines.append("")
    report_lines.append("| Strategy | IS Trades | IS Win% | IS Avg R | IS PF | IS Expect. | OOS Trades | OOS Win% | OOS Avg R | OOS PF | OOS Expect. | OOS p-val | OOS 95% CI | VERDICT | Notes |")
    report_lines.append("|----------|----------|--------|---------|------|-----------|-----------|---------|----------|-------|------------|----------|-----------|---------|-------|")

    passes = 0
    fails = 0
    insuff = 0
    nodata = 0

    for row in results:
        safe_notes = row[14].replace("|", "/") if row[14] != "—" else "—"
        report_lines.append(
            f"| {row[0]} | {row[1]} | {row[2]} | {row[3]} | {row[4]} | {row[5]} | "
            f"{row[6]} | {row[7]} | {row[8]} | {row[9]} | {row[10]} | {row[11]} | {row[12]} | "
            f"{row[13]} | {safe_notes} |"
        )
        if row[13] == "PASS":
            passes += 1
        elif row[13] == "FAIL":
            fails += 1
        elif row[13] == "INSUFFICIENT":
            insuff += 1
        elif row[13] == "NO-DATA":
            nodata += 1

    report_lines.append("")
    report_lines.append(f"**Totals:** {passes} PASS | {fails} FAIL | {insuff} INSUFFICIENT | {nodata} NO-DATA")
    report_lines.append("")

    # ── Detail Section ────────────────────────────────────────────────────
    report_lines.append("## Detailed Per-Strategy Breakdown")
    report_lines.append("")

    for i, row in enumerate(results):
        sid = row[0]
        report_lines.append(f"### {sid}")
        if row[13] == "NO-DATA":
            report_lines.append(f"- **Verdict:** NO-DATA — no Phase 1A CSV found")
            report_lines.append("")
            continue

        report_lines.append(f"- **Verdict:** {row[13]}")
        report_lines.append(f"- **Trades:** {row[1]} IS → {row[6]} OOS")

        # Re-load for detailed stat printing
        df = load_trades(sid)
        if df is not None:
            n_total = len(df)
            split_idx = int(n_total * 0.6)
            is_df = df.iloc[:split_idx]
            oos_df = df.iloc[split_idx:]

            is_range = f"{is_df['date'].min().date()} to {is_df['date'].max().date()}"
            oos_range = f"{oos_df['date'].min().date()} to {oos_df['date'].max().date()}"
            report_lines.append(f"- **IS period:** {is_range}")
            report_lines.append(f"- **OOS period:** {oos_range}")

        report_lines.append(f"- **IS metrics:** Win Rate={row[2]}, Avg R={row[3]}, PF={row[4]}, Expectancy={row[5]}")
        report_lines.append(f"- **OOS metrics:** Win Rate={row[7]}, Avg R={row[8]}, PF={row[9]}, Expectancy={row[10]}")
        report_lines.append(f"- **OOS p-value (bootstrap):** {row[11]}")
        report_lines.append(f"- **OOS 95% CI:** {row[12]}")
        if row[14] != "—":
            report_lines.append(f"- **Flags:** {row[14]}")
        report_lines.append("")

    # ── Gate Decision ─────────────────────────────────────────────────────
    report_lines.append("## Gate Decision")
    report_lines.append("")
    report_lines.append("**Only PASS strategies clear the gate for paper trading.**")
    report_lines.append("FAIL strategies require redesign and re-validation before advancing to Phase 1B/2.")
    report_lines.append("INSUFFICIENT strategies need more data before a conclusion can be drawn.")
    report_lines.append("")
    report_lines.append("| Outcome | Count |")
    report_lines.append("|---------|-------|")
    report_lines.append(f"| PASS (clears gate) | {passes} |")
    report_lines.append(f"| FAIL (blocked) | {fails} |")
    report_lines.append(f"| INSUFFICIENT (need data) | {insuff} |")
    report_lines.append(f"| NO-DATA (not tested) | {nodata} |")
    report_lines.append(f"| **Total** | **{passes + fails + insuff + nodata}** |")

    if fails > 0:
        report_lines.append("")
        report_lines.append("### BLOCKED STRATEGIES — Immediate Attention Required")
        report_lines.append("")
        for row in results:
            if row[13] == "FAIL":
                report_lines.append(f"- **{row[0]}**: {row[14]}")
        report_lines.append("")
        report_lines.append("These strategies showed significant OOS degradation consistent with overfitting. "
                           "They must be re-optimized with walk-forward constraints (curfitted stop caps, "
                           "regime-aware parameters) before re-entering validation.")

    report_lines.append("")
    report_lines.append("---")
    report_lines.append("_Generated by HermesForge Backtester Agent — US-114 Walk-Forward Gate_")

    report_text = "\n".join(report_lines)

    with open(OUTPUT_PATH, "w") as f:
        f.write(report_text)

    print(f"\n{'='*80}")
    print(f"  Report written to: {OUTPUT_PATH}")
    print(f"  Results: {passes} PASS | {fails} FAIL | {insuff} INSUFFICIENT | {nodata} NO-DATA")
    print(f"{'='*80}")

    return passes, fails, insuff, nodata


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="US-114 walk-forward validation")
    ap.add_argument("--shim-legacy-close-entry", action="store_true",
                    help="Re-rate legacy close-entry CSVs (missing "
                         "fill_convention) via the fill_convention shim instead "
                         "of refusing them (US-173).")
    args = ap.parse_args()
    if args.shim_legacy_close_entry:
        SHIM_LEGACY_CLOSE_ENTRY = True
        print("[US-173] --shim-legacy-close-entry set: legacy CSVs will be "
              "re-rated to next-open via fill_convention.apply_next_open_entry.")
    main()