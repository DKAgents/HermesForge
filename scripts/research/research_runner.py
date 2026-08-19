#!/usr/bin/env python3
"""
research_runner.py — HermesForge Research Pipeline Orchestrator

Runs the full research pipeline:
  1. Factor Screener — scans for new factor anomalies
  2. Revival Tester — re-tests killed strategies for regime revival
  3. Decay Monitor — checks for edge erosion on live/watch strategies
  4. Hypothesis Generator — proposes new strategy ideas

Outputs a comprehensive markdown report and saves to vault.
Designed to run as a weekly cron job.

Usage:
    python3 research_runner.py                    # full pipeline, print report
    python3 research_runner.py --json              # JSON output
    python3 research_runner.py --save              # save to vault
    python3 research_runner.py --save --json       # save JSON to data/
"""

import sys
import json
import time
import argparse
import pathlib
from datetime import datetime

REPO_ROOT = pathlib.Path(__file__).parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts" / "research"))
sys.path.insert(0, str(REPO_ROOT / "scripts" / "validation"))
sys.path.insert(0, str(REPO_ROOT / "scripts" / "validation" / "scanners"))
sys.path.insert(0, str(REPO_ROOT / "scripts" / "paper_trading"))

from factor_screener import run_factor_screen, format_report as format_factor_report
from revival_tester import run_revival_tests, format_report as format_revival_report
from decay_monitor import run_decay_check, format_report as format_decay_report
from hypothesis_generator import generate_hypotheses, format_report as format_hypothesis_report


def run_full_pipeline(save: bool = False) -> dict:
    """
    Run the full research pipeline.
    Returns a dict with all results and a markdown report.
    """
    from fetch_data import load_all as load_all_stocks
    from fetch_crypto_data import load_all as load_all_crypto

    pipeline_start = time.time()
    today = datetime.utcnow()
    timestamp = today.isoformat()

    # Load data
    print("=" * 60, file=sys.stderr)
    print("HermesForge Research Pipeline", file=sys.stderr)
    print(f"Started: {today.strftime('%Y-%m-%d %H:%M %Z')}", file=sys.stderr)
    print("=" * 60, file=sys.stderr)

    print("\n[1/4] Loading data...", file=sys.stderr)
    stock_data = load_all_stocks()
    print(f"  Stocks: {len(stock_data)} tickers", file=sys.stderr)
    crypto_data = load_all_crypto()
    print(f"  Crypto: {len(crypto_data)} tickers", file=sys.stderr)

    # Module 1: Factor Screener
    print("\n[2/4] Factor Screener — scanning for new anomalies...", file=sys.stderr)
    t0 = time.time()
    stock_factor = run_factor_screen(stock_data, "stock")
    crypto_factor = run_factor_screen(crypto_data, "crypto")
    factor_time = time.time() - t0
    print(f"  Done in {factor_time:.1f}s", file=sys.stderr)
    print(f"  Stock candidates: {stock_factor['n_candidates']}", file=sys.stderr)
    print(f"  Crypto candidates: {crypto_factor['n_candidates']}", file=sys.stderr)

    # Module 2: Revival Tester
    print("\n[3/4] Revival Tester — re-testing killed strategies...", file=sys.stderr)
    t0 = time.time()
    revival = run_revival_tests(stock_data)
    revival_time = time.time() - t0
    print(f"  Done in {revival_time:.1f}s", file=sys.stderr)
    print(f"  Revival candidates: {revival['n_candidates']}", file=sys.stderr)

    # Module 3: Decay Monitor
    print("\n[4/4] Decay Monitor — checking edge erosion...", file=sys.stderr)
    t0 = time.time()
    decay = run_decay_check(stock_data, crypto_data)
    decay_time = time.time() - t0
    print(f"  Done in {decay_time:.1f}s", file=sys.stderr)
    print(f"  Decay flags: {decay['n_decayed']}", file=sys.stderr)

    # Module 4: Hypothesis Generator
    print("\n[5/5] Hypothesis Generator — proposing new strategies...", file=sys.stderr)
    t0 = time.time()
    stock_hyp = generate_hypotheses(stock_data, "stock")
    crypto_hyp = generate_hypotheses(crypto_data, "crypto")
    hyp_time = time.time() - t0
    print(f"  Done in {hyp_time:.1f}s", file=sys.stderr)
    print(f"  Stock candidates: {stock_hyp['n_candidates']}", file=sys.stderr)
    print(f"  Crypto candidates: {crypto_hyp['n_candidates']}", file=sys.stderr)

    total_time = time.time() - pipeline_start

    # Assemble report
    report_parts = []
    report_parts.append(f"# HermesForge Weekly Research Report")
    report_parts.append(f"**Date:** {today.strftime('%Y-%m-%d %H:%M %Z')}")
    report_parts.append(f"**Pipeline runtime:** {total_time:.1f}s")
    report_parts.append("")
    report_parts.append("---")
    report_parts.append("")

    # Summary section
    report_parts.append("## Executive Summary")
    report_parts.append("")
    total_candidates = (
        stock_factor["n_candidates"] + crypto_factor["n_candidates"] +
        revival["n_candidates"] + decay["n_decayed"] +
        stock_hyp["n_candidates"] + crypto_hyp["n_candidates"]
    )
    report_parts.append(f"- **Factor anomalies flagged:** {stock_factor['n_candidates']} stocks, {crypto_factor['n_candidates']} crypto")
    report_parts.append(f"- **Killed strategies revived:** {revival['n_candidates']}")
    report_parts.append(f"- **Edge decay detected:** {decay['n_decayed']}")
    report_parts.append(f"- **New strategy candidates:** {stock_hyp['n_candidates']} stocks, {crypto_hyp['n_candidates']} crypto")
    report_parts.append(f"- **Total action items:** {total_candidates}")
    report_parts.append("")
    if total_candidates == 0:
        report_parts.append("*No new edges found this week. All strategies stable, all killed strategies remain dead.*")
    else:
        report_parts.append(f"*{total_candidates} item(s) require further investigation. See details below.*")
    report_parts.append("")
    report_parts.append("---")
    report_parts.append("")

    # Factor screener section
    report_parts.append(format_factor_report(stock_factor, crypto_factor))
    report_parts.append("---")
    report_parts.append("")

    # Revival tester section
    report_parts.append(format_revival_report(revival))
    report_parts.append("---")
    report_parts.append("")

    # Decay monitor section
    report_parts.append(format_decay_report(decay))
    report_parts.append("---")
    report_parts.append("")

    # Hypothesis generator section
    report_parts.append(format_hypothesis_report(stock_hyp, crypto_hyp))
    report_parts.append("---")
    report_parts.append("")

    report = "\n".join(report_parts)

    results = {
        "timestamp": timestamp,
        "runtime_seconds": round(total_time, 1),
        "factor_screener": {"stock": stock_factor, "crypto": crypto_factor},
        "revival_tester": revival,
        "decay_monitor": decay,
        "hypothesis_generator": {"stock": stock_hyp, "crypto": crypto_hyp},
        "total_action_items": total_candidates,
        "report": report,
    }

    if save:
        # Save markdown to vault
        vault_dir = REPO_ROOT / "vault" / "research"
        vault_dir.mkdir(parents=True, exist_ok=True)
        report_file = vault_dir / f"research-{today.strftime('%Y-%m-%d')}.md"
        with open(report_file, "w") as f:
            f.write(report)
        print(f"\nReport saved to: {report_file}", file=sys.stderr)

        # Save JSON to data/
        data_dir = REPO_ROOT / "data"
        data_dir.mkdir(parents=True, exist_ok=True)
        json_file = data_dir / f"research-{today.strftime('%Y-%m-%d')}.json"
        # Save JSON without the report text (it's in the markdown)
        json_results = {k: v for k, v in results.items() if k != "report"}
        with open(json_file, "w") as f:
            json.dump(json_results, f, indent=2, default=str)
        print(f"JSON saved to: {json_file}", file=sys.stderr)

    print(f"\nPipeline complete in {total_time:.1f}s", file=sys.stderr)

    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="HermesForge Research Pipeline")
    parser.add_argument("--json", action="store_true", help="Output JSON summary")
    parser.add_argument("--save", action="store_true", help="Save report to vault and JSON to data/")
    args = parser.parse_args()

    results = run_full_pipeline(save=args.save)

    if args.json:
        json_results = {k: v for k, v in results.items() if k != "report"}
        print(json.dumps(json_results, indent=2, default=str))
    else:
        print(results["report"])
