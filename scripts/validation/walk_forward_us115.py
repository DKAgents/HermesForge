#!/usr/bin/env python3
"""
walk_forward_us115.py — HermesForge US-115 Walk-Forward Validation (v3)

For each of the 10 structure-based scanners:
  1. Load Phase 1A v3 CSV
  2. Sort chronologically by entry date
  3. Split 60% IS / 40% OOS
  4. Compute: trade count, win rate, avg R, profit factor
  5. Bootstrap p-value (H0: mean OOS R <= 0)
  6. Compare vs v2 (fixed 3R) baseline

Run: python3 ~/HermesForge/scripts/validation/walk_forward_us115.py
"""

import os
import sys
import warnings
import numpy as np
import pandas as pd
from scipy import stats as sp_stats

warnings.filterwarnings("ignore", category=FutureWarning)

RESULTS_DIR = os.path.expanduser("~/HermesForge/scripts/validation/results")
OUTPUT_PATH = os.path.expanduser("~/HermesForge/04-ForgeLoop/AUDIT-backtester-US115-v3.md")

# v3 scanners (market_structure-based)
V3_STRATS = ["STR-X", "STR-Z", "STR-AA", "STR-AC", "STR-AD", "STR-AE", "STR-AF", "STR-Y", "STR-R", "STR-B"]

# v2 baseline CSV files (fixed 3R approach)
V2_BASELINE_CSVS = {
    "STR-X": "STR-X-stocks-phase1a.csv",
    "STR-Z": "STR-Z-stocks-phase1a.csv",
    "STR-AA": "STR-AA-stocks-phase1a.csv",
    "STR-AC": "STR-AC-stocks-phase1a.csv",
    "STR-AD": "STR-AD-stocks-phase1a.csv",
    "STR-AE": "STR-AE-stocks-phase1a.csv",
    "STR-AF": "STR-AF-stocks-phase1a.csv",
    "STR-Y": "STR-Y-stocks-phase1a.csv",
    "STR-R": "STR-R-stocks-phase1a-v2.csv",
    "STR-B": "STR-B-macd-histogram-divergence-phase1a.csv",
}

MIN_OOS_TRADES = 10
P_THRESHOLD = 0.05
BOOTSTRAP_ITERATIONS = 10000
BOOTSTRAP_SEED = 42


def load_trades_v3(strategy_id):
    """Load Phase 1A v3 CSV. Returns sorted DataFrame or None."""
    fname = f"{strategy_id}-stocks-phase1a-v3.csv"
    fpath = os.path.join(RESULTS_DIR, fname)
    if not os.path.isfile(fpath):
        return None
    try:
        df = pd.read_csv(fpath, parse_dates=["date"])
    except Exception as e:
        print(f"  WARN: {fpath} failed to parse: {e}")
        return None
    if df.empty or len(df) < 2:
        return None
    df = df.dropna(subset=["r_multiple", "date"])
    if df.empty:
        return None
    df = df.sort_values("date").reset_index(drop=True)
    return df


def load_baseline_v2(strategy_id):
    """Load v2 baseline CSV. Returns DataFrame or None."""
    fname = V2_BASELINE_CSVS.get(strategy_id)
    if not fname:
        return None
    fpath = os.path.join(RESULTS_DIR, fname)
    if not os.path.isfile(fpath):
        return None
    try:
        df = pd.read_csv(fpath)
    except Exception:
        return None
    if df.empty or len(df) < 2:
        return None
    # Handle different column naming conventions
    r_col = "r_multiple"
    if r_col not in df.columns:
        # Try alternative names
        for alt in ["R_multiple", "r_mult"]:
            if alt in df.columns:
                df = df.rename(columns={alt: r_col})
                break
    df = df.dropna(subset=[r_col])
    if df.empty:
        return None
    return df


def compute_metrics(r_values):
    """Compute metrics from an array of R multiples."""
    if len(r_values) == 0:
        return {"n_trades": 0, "win_rate": 0.0, "avg_r": 0.0, "profit_factor": 0.0, "sum_r": 0.0}
    n = len(r_values)
    winners = r_values[r_values > 0]
    losers = r_values[r_values <= 0]
    n_wins = len(winners)
    n_losses = len(losers)
    win_rate = n_wins / n * 100.0 if n > 0 else 0.0
    avg_r = float(np.mean(r_values))
    sum_r = float(np.sum(r_values))
    gross_profit = float(np.sum(winners)) if n_wins > 0 else 0.0
    gross_loss = float(np.abs(np.sum(losers))) if n_losses > 0 else 0.0
    profit_factor = gross_profit / gross_loss if gross_loss > 1e-10 else (float("inf") if gross_profit > 0 else 0.0)
    return {"n_trades": n, "win_rate": win_rate, "avg_r": avg_r, "profit_factor": profit_factor, "sum_r": sum_r}


def bootstrap_test(r_values, n_iter=BOOTSTRAP_ITERATIONS, seed=BOOTSTRAP_SEED):
    """Bootstrap test: H0: mean R <= 0. Returns (p_value, 95% CI)."""
    rng = np.random.default_rng(seed)
    n = len(r_values)
    if n < MIN_OOS_TRADES:
        return 1.0, (-99.0, 99.0)
    boot_means = np.zeros(n_iter)
    for i in range(n_iter):
        sample = rng.choice(r_values, size=n, replace=True)
        boot_means[i] = np.mean(sample)
    ci_low, ci_high = np.percentile(boot_means, [2.5, 97.5])
    p_value = np.mean(boot_means <= 0.0)
    return p_value, (ci_low, ci_high)


def t_test_oos(r_values):
    """One-sample t-test: H0: mean R = 0, Ha: mean R > 0 (one-sided)."""
    n = len(r_values)
    if n < MIN_OOS_TRADES:
        return 1.0, (-99.0, 99.0)
    t_stat, p_two = sp_stats.ttest_1samp(r_values, 0.0, alternative="two-sided")
    if t_stat > 0:
        p_one = p_two / 2.0
    else:
        p_one = 1.0 - p_two / 2.0
    ci = sp_stats.t.interval(0.95, df=n - 1, loc=np.mean(r_values), scale=sp_stats.sem(r_values))
    return p_one, ci


def main():
    results = []

    print("=" * 100)
    print("US-115 WALK-FORWARD VALIDATION (v3) — 10 Structure-Based Scanners")
    print("=" * 100)
    print()

    passes = 0
    fails = 0
    insuff = 0
    nodata = 0

    for sid in V3_STRATS:
        print(f"\n{'─'*80}")
        print(f"  {sid} ... ", end="", flush=True)

        df = load_trades_v3(sid)
        if df is None:
            print("NO-DATA (v3 CSV missing or empty)")
            results.append({
                "sid": sid,
                "verdict": "NO-DATA",
                "v2_trades": 0, "v2_avg_r": 0, "v2_pf": 0,
                "v3_trades": 0, "v3_avg_r": 0, "v3_pf": 0,
                "is_trades": 0, "is_avg_r": 0, "is_pf": 0,
                "oos_trades": 0, "oos_avg_r": 0, "oos_pf": 0, "oos_pval": 1.0,
                "notes": "No v3 CSV found",
            })
            nodata += 1
            continue

        n_total = len(df)
        split_idx = int(n_total * 0.6)

        is_df = df.iloc[:split_idx].copy()
        oos_df = df.iloc[split_idx:].copy()

        is_r = is_df["r_multiple"].values
        oos_r = oos_df["r_multiple"].values

        is_metrics = compute_metrics(is_r)
        oos_metrics = compute_metrics(oos_r)

        # Bootstrap + t-test
        boot_p, boot_ci = bootstrap_test(oos_r)
        t_p, t_ci = t_test_oos(oos_r)
        report_p = boot_p  # use bootstrap as primary

        # Evaluate
        flags = []
        n_oos = len(oos_r)
        if n_oos < MIN_OOS_TRADES:
            verdict = "INSUFFICIENT"
            flags.append(f"Only {n_oos} OOS trades (min {MIN_OOS_TRADES})")
        elif oos_metrics["avg_r"] <= 0 or oos_metrics["profit_factor"] < 1.0:
            verdict = "FAIL"
            flags.append(f"OOS avg R={oos_metrics['avg_r']:.4f}, PF={oos_metrics['profit_factor']:.3f}")
            if report_p >= P_THRESHOLD:
                flags.append(f"OOS not significant (p={report_p:.4f})")
        elif report_p >= P_THRESHOLD:
            verdict = "FAIL"
            flags.append(f"OOS not statistically significant (p={report_p:.4f})")
        else:
            verdict = "PASS"

        # Check trade count for low-signal flag
        if n_total < 50:
            flags.append(f"LOW TRADE COUNT ({n_total}) — min_rr filter may be too aggressive")

        # Load v2 baseline
        v2_df = load_baseline_v2(sid)
        if v2_df is not None:
            v2_r = v2_df["r_multiple"].values
            v2_metrics = compute_metrics(v2_r)
        else:
            v2_metrics = {"n_trades": 0, "avg_r": 0.0, "profit_factor": 0.0}

        date_range_is = f"{is_df['date'].min().date()} to {is_df['date'].max().date()}"
        date_range_oos = f"{oos_df['date'].min().date()} to {oos_df['date'].max().date()}"

        print(f"\n    IS ({date_range_is}): {is_metrics['n_trades']} trades")
        print(f"      Win Rate: {is_metrics['win_rate']:.1f}%  |  Avg R: {is_metrics['avg_r']:.4f}  |  PF: {is_metrics['profit_factor']:.3f}")
        print(f"    OOS ({date_range_oos}): {oos_metrics['n_trades']} trades")
        print(f"      Win Rate: {oos_metrics['win_rate']:.1f}%  |  Avg R: {oos_metrics['avg_r']:.4f}  |  PF: {oos_metrics['profit_factor']:.3f}")
        print(f"    Bootstrap p: {report_p:.4f}  |  t-test p: {t_p:.4f}")

        if v2_metrics["n_trades"] > 0:
            trade_delta = ((n_total - v2_metrics["n_trades"]) / v2_metrics["n_trades"]) * 100
            r_delta = ((is_metrics["avg_r"] - v2_metrics["avg_r"]) / v2_metrics["avg_r"]) * 100 if v2_metrics["avg_r"] != 0 else 0
            print(f"    v2 baseline: {v2_metrics['n_trades']} trades, avg R={v2_metrics['avg_r']:.4f}, PF={v2_metrics['profit_factor']:.3f}")
            print(f"    v3 vs v2: trades {trade_delta:+.1f}% | avg R {r_delta:+.1f}%")

        for f in flags:
            print(f"    ⚠  {f}")

        symbol = "\u2713" if verdict == "PASS" else ("\u2717" if verdict == "FAIL" else "?")
        print(f"    >> VERDICT: {verdict} {symbol}")

        if verdict == "PASS":
            passes += 1
        elif verdict == "FAIL":
            fails += 1
        elif verdict == "INSUFFICIENT":
            insuff += 1
        elif verdict == "NO-DATA":
            nodata += 1

        results.append({
            "sid": sid,
            "verdict": verdict,
            "v2_trades": v2_metrics["n_trades"],
            "v2_avg_r": v2_metrics["avg_r"],
            "v2_pf": v2_metrics["profit_factor"],
            "v3_trades": n_total,
            "v3_avg_r": is_metrics["avg_r"],
            "v3_pf": is_metrics["profit_factor"],
            "is_trades": is_metrics["n_trades"],
            "is_avg_r": is_metrics["avg_r"],
            "is_pf": is_metrics["profit_factor"],
            "oos_trades": oos_metrics["n_trades"],
            "oos_avg_r": oos_metrics["avg_r"],
            "oos_pf": oos_metrics["profit_factor"],
            "oos_pval": report_p,
            "oos_ci": f"[{boot_ci[0]:.4f}, {boot_ci[1]:.4f}]",
            "notes": "; ".join(flags) if flags else "",
        })

    # ── Write Report ──────────────────────────────────────────────────────
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

    report_lines = []
    report_lines.append("# US-115 v3 Structure-Based Validation — Walk-Forward Report")
    report_lines.append("")
    report_lines.append(f"**Generated:** {pd.Timestamp.now(tz='America/Los_Angeles').strftime('%Y-%m-%d %H:%M %Z')}")
    report_lines.append("**Backtester:** T3 (deepseek-v4-flash)")
    report_lines.append("**Scope:** 10 scanners re-validated with market_structure module (pullback entry, structure stop, natural target, min 1.5R, 20-bar cooldown)")
    report_lines.append("**Universe:** 529 stocks | **Split:** IS=60% | OOS=40%")
    report_lines.append("")
    report_lines.append("---")
    report_lines.append("")
    report_lines.append("## Summary: v2 (Fixed 3R) vs v3 (Structure-Based)")
    report_lines.append("")
    report_lines.append("| Strategy | v2 Trades | v2 Avg R | v2 PF | v3 Trades | v3 Avg R | v3 PF | OOS Trades | OOS Avg R | OOS PF | OOS p-val | OOS 95% CI | VERDICT |")
    report_lines.append("|----------|----------|----------|-------|-----------|----------|-------|------------|-----------|--------|-----------|------------|---------|")

    for r in results:
        v2_t = r["v2_trades"]
        v2_r = f"{r['v2_avg_r']:.4f}" if r["v2_trades"] > 0 else "—"
        v2_p = f"{r['v2_pf']:.3f}" if r["v2_trades"] > 0 else "—"
        report_lines.append(
            f"| {r['sid']} | {v2_t} | {v2_r} | {v2_p} | "
            f"{r['v3_trades']} | {r['is_avg_r']:.4f} | {r['is_pf']:.3f} | "
            f"{r['oos_trades']} | {r['oos_avg_r']:.4f} | {r['oos_pf']:.3f} | "
            f"{r['oos_pval']:.4f} | {r['oos_ci']} | **{r['verdict']}** |"
        )

    report_lines.append("")
    report_lines.append(f"**Totals:** {passes} PASS | {fails} FAIL | {insuff} INSUFFICIENT | {nodata} NO-DATA")
    report_lines.append("")

    # ── PASS CRITERIA EVALUATION ──────────────────────────────────────────
    report_lines.append("### Pass Criteria Applied")
    report_lines.append("")
    report_lines.append("1. **OOS avg R > 0 and OOS PF > 1.0** (profitable out-of-sample)")
    report_lines.append("2. **OOS p-value < 0.05** (bootstrap, statistically significant)")
    report_lines.append("3. **Trade count > 10** (sufficient sample for inference)")
    report_lines.append("")
    report_lines.append("Additional flags:")
    report_lines.append("- Trade count < 50: possible aggressive min_rr filter or tight pullback window")
    report_lines.append("- Trade count dropped > 50% vs v2: structural impact of pullback/cooldown")
    report_lines.append("")

    # ── DETAILED PER-STRATEGY ─────────────────────────────────────────────
    report_lines.append("## Detailed Per-Strategy Breakdown")
    report_lines.append("")

    for r in results:
        sid = r["sid"]
        report_lines.append(f"### {sid}")
        report_lines.append(f"- **Verdict:** {r['verdict']}")
        report_lines.append(f"- **v2 baseline:** {r['v2_trades']} trades, Avg R={r['v2_avg_r']:.4f}, PF={r['v2_pf']:.3f}")
        report_lines.append(f"- **v3 IS:** {r['is_trades']} trades, Avg R={r['is_avg_r']:.4f}, PF={r['is_pf']:.3f}")
        report_lines.append(f"- **v3 OOS:** {r['oos_trades']} trades, Avg R={r['oos_avg_r']:.4f}, PF={r['oos_pf']:.3f}")
        report_lines.append(f"- **OOS p-value (bootstrap):** {r['oos_pval']:.4f}")
        report_lines.append(f"- **OOS 95% CI:** {r['oos_ci']}")

        if r["v2_trades"] > 0:
            trade_delta = ((r["v3_trades"] - r["v2_trades"]) / r["v2_trades"]) * 100
            r_delta = ((r["is_avg_r"] - r["v2_avg_r"]) / r["v2_avg_r"]) * 100 if r["v2_avg_r"] != 0 else 0
            report_lines.append(f"- **Δ v2→v3:** trades {trade_delta:+.1f}%, IS avg R {r_delta:+.1f}%")
            if trade_delta < -50:
                report_lines.append(f"  - ⚠ Trade count dropped >50%. Review pullback window and min_rr filter.")
            if r_delta > 0:
                report_lines.append(f"  - Avg R improved with structure-based targets (+{r_delta:.0f}%).")
            else:
                report_lines.append(f"  - Avg R declined with structure-based targets ({r_delta:.0f}%).")

        if r["notes"]:
            report_lines.append(f"- **Flags:** {r['notes']}")

        # Specific recommendation based on verdict
        if r["verdict"] == "PASS":
            report_lines.append(f"- **Recommendation:** Return to LIVE — structure-based approach validated.")
        elif r["verdict"] == "FAIL":
            report_lines.append(f"- **Recommendation:** BLOCKED. Review structure parameters or revert to v2 fixed 3R.")
        elif r["verdict"] == "INSUFFICIENT":
            report_lines.append(f"- **Recommendation:** Need more trade data. Flag for risk guardian review — do not auto-kill.")
        report_lines.append("")

    # ── GATE DECISION ─────────────────────────────────────────────────────
    report_lines.append("## Gate Decision: Scanners Cleared for Return to LIVE")
    report_lines.append("")

    passed_strats = [r for r in results if r["verdict"] == "PASS"]
    failed_strats = [r for r in results if r["verdict"] in ("FAIL",)]
    insuff_strats = [r for r in results if r["verdict"] == "INSUFFICIENT"]
    nodata_strats = [r for r in results if r["verdict"] == "NO-DATA"]

    if passed_strats:
        report_lines.append("### PASS (Return to LIVE)")
        report_lines.append("")
        report_lines.append("| Strategy | OOS Avg R | OOS PF | OOS Trades | OOS p | Key Improvement |")
        report_lines.append("|----------|-----------|--------|------------|-------|-----------------|")
        for r in passed_strats:
            report_lines.append(
                f"| {r['sid']} | {r['oos_avg_r']:.4f} | {r['oos_pf']:.3f} | {r['oos_trades']} | "
                f"{r['oos_pval']:.4f} | Structure-based targets |"
            )
        report_lines.append("")

    if failed_strats:
        report_lines.append("### FAIL (Blocked — Return to Review)")
        report_lines.append("")
        for r in failed_strats:
            report_lines.append(f"- **{r['sid']}**: {r['notes']}")
        report_lines.append("")

    if insuff_strats:
        report_lines.append("### INSUFFICIENT DATA (Risk Guardian Review Required)")
        report_lines.append("")
        report_lines.append("These scanners have fewer than 50 trades, which may indicate:")
        report_lines.append("- The `min_rr=1.5` filter is too aggressive and rejecting valid setups")
        report_lines.append("- The pullback window (`max_wait_bars=5`) is too short for this indicator's signals")
        report_lines.append("- The 20-bar cooldown is suppressing overlapping but independent signals")
        report_lines.append("")
        report_lines.append("**Do not auto-kill. Flag for risk guardian to review parameters.**")
        report_lines.append("")
        for r in insuff_strats:
            report_lines.append(f"- **{r['sid']}**: {r['votes']} trades OOS, avg R={r['oos_avg_r']:.4f}, PF={r['oos_pf']:.3f}")
        report_lines.append("")

    if nodata_strats:
        report_lines.append("### NO-DATA")
        report_lines.append("")
        for r in nodata_strats:
            report_lines.append(f"- **{r['sid']}**: {r['notes']}")
        report_lines.append("")

    # ── KEY FINDINGS ──────────────────────────────────────────────────────
    report_lines.append("## Key Findings")
    report_lines.append("")

    # Summarize the structure-based approach vs fixed 3R
    avg_r_v2 = np.mean([r["v2_avg_r"] for r in results if r["v2_trades"] > 0])
    avg_r_v3 = np.mean([r["is_avg_r"] for r in results if r["v3_trades"] > 0])
    avg_r_oos = np.mean([r["oos_avg_r"] for r in results if r["oos_trades"] > 0])

    total_trades_v2 = sum(r["v2_trades"] for r in results if r["v2_trades"] > 0)
    total_trades_v3 = sum(r["v3_trades"] for r in results if r["v3_trades"] > 0)
    trade_reduction = ((total_trades_v3 - total_trades_v2) / total_trades_v2 * 100) if total_trades_v2 > 0 else 0

    report_lines.append(f"**Across all 10 scanners (averages):**")
    report_lines.append(f"- **v2 (fixed 3R):** {total_trades_v2} total trades, avg R={avg_r_v2:.4f}")
    report_lines.append(f"- **v3 (structure-based):** {total_trades_v3} total trades, IS avg R={avg_r_v3:.4f}, OOS avg R={avg_r_oos:.4f}")
    report_lines.append(f"- **Trade count Δ:** {trade_reduction:+.1f}% (expected: pullback entries + min_rr filter + cooldown)")
    report_lines.append("")

    if avg_r_v3 > avg_r_v2:
        report_lines.append(f"**Avg R improved +{(avg_r_v3 - avg_r_v2)/avg_r_v2*100:.0f}%** in v3 → structure-based targets produce better R:R than fixed 3R.")
    else:
        report_lines.append(f"**Avg R declined {(avg_r_v2 - avg_r_v3)/avg_r_v2*100:.0f}%** in v3 → structure-based targets underperformed fixed 3R.")

    # Did the edge survive?
    report_lines.append("")
    report_lines.append("**Critical question: Did the edge survive the transition?**")
    report_lines.append("")
    report_lines.append("From 'enter on strength, target 3R' to 'enter on pullback, target natural resistance':")
    
    pass_count = len(passed_strats)
    fail_count = len(failed_strats)
    if pass_count > fail_count:
        report_lines.append(f"- {pass_count}/{10} scanners PASSED — the structure-based approach preserved or improved the edge for most.")
        report_lines.append(f"- {fail_count}/{10} scanners FAILED — the edge did not survive for these.")
    else:
        report_lines.append(f"- Only {pass_count}/{10} scanners PASSED — the structure-based approach needs further refinement.")
        report_lines.append(f"- {fail_count}/{10} scanners FAILED.")    
    report_lines.append("")

    report_lines.append("---")
    report_lines.append("_Generated by HermesForge Backtester Agent — US-115 Walk-Forward Gate_")

    report_text = "\n".join(report_lines)

    with open(OUTPUT_PATH, "w") as f:
        f.write(report_text)

    print(f"\n{'='*80}")
    print(f"  Report written to: {OUTPUT_PATH}")
    print(f"  Results: {passes} PASS | {fails} FAIL | {insuff} INSUFFICIENT | {nodata} NO-DATA")
    print(f"{'='*80}")

    return passes, fails, insuff, nodata


if __name__ == "__main__":
    main()