#!/usr/bin/env python3
"""
research_wrapper.py — Cron wrapper for HermesForge Research Pipeline

Runs the full research pipeline and posts a summary to Discord.
Designed to run as a weekly cron job (Sundays at 12:00 UTC).

The script:
  1. Runs research_runner.py --save --json
  2. Parses the JSON output
  3. Posts a concise summary to Discord

Usage (from cron):
    cd /root/HermesForge && python3 scripts/research/research_wrapper.py
"""

import sys
import json
import pathlib
import subprocess
from datetime import datetime

REPO_ROOT = pathlib.Path(__file__).parent.parent.parent

def run_pipeline() -> dict:
    """Run the research pipeline and return the JSON results."""
    cmd = [
        sys.executable,
        str(REPO_ROOT / "scripts" / "research" / "research_runner.py"),
        "--save", "--json"
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=540, cwd=str(REPO_ROOT))
    if result.returncode != 0:
        print(f"Pipeline failed: {result.stderr}", file=sys.stderr)
        return {"error": result.stderr}
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return {"error": "Failed to parse JSON output", "stdout": result.stdout[:500]}


def build_discord_summary(results: dict) -> str:
    """Build a concise Discord-friendly summary from pipeline results."""
    if "error" in results:
        return f"❌ Research pipeline failed: {results['error'][:200]}"

    ts = results.get("timestamp", "unknown")
    runtime = results.get("runtime_seconds", 0)
    total = results.get("total_action_items", 0)

    # Factor screener
    sf = results.get("factor_screener", {})
    stock_factors = sf.get("stock", {})
    crypto_factors = sf.get("crypto", {})
    stock_cands = stock_factors.get("n_candidates", 0)
    crypto_cands = crypto_factors.get("n_candidates", 0)

    # Revival tester
    rt = results.get("revival_tester", {})
    revival_cands = rt.get("n_candidates", 0)

    # Decay monitor
    dm = results.get("decay_monitor", {})
    decay_flags = dm.get("n_decayed", 0)

    # Hypothesis generator
    hg = results.get("hypothesis_generator", {})
    stock_hyps = hg.get("stock", {})
    crypto_hyps = hg.get("crypto", {})
    stock_hyp_cands = stock_hyps.get("n_candidates", 0)
    crypto_hyp_cands = crypto_hyps.get("n_candidates", 0)

    lines = []
    lines.append("📊 **Weekly Research Pipeline Complete**")
    lines.append(f"*Runtime: {runtime:.0f}s | {ts[:10]}*")
    lines.append("")
    lines.append("**Factor Anomalies:**")
    lines.append(f"  Stocks: {stock_cands} candidate(s) | Crypto: {crypto_cands} candidate(s)")
    lines.append("")
    lines.append("**Killed Strategy Revival:**")
    if revival_cands > 0:
        for c in rt.get("candidates", []):
            lines.append(f"  ★ {c['strategy']} ({c['name']}): Mean R={c['mean_r']:.4f}, p={c['p_value']:.4f}")
    else:
        lines.append("  No revival candidates — all 12 killed strategies remain dead")
    lines.append("")
    lines.append("**Edge Decay Monitor:**")
    if decay_flags > 0:
        for d in dm.get("decayed", []):
            lines.append(f"  ⚠️ {d['strategy']} ({d['name']}): Sharpe dropped {d.get('decay_pct',0)*100:.0f}%")
    else:
        lines.append("  All monitored strategies stable — no decay detected")
    lines.append("")
    lines.append("**New Strategy Candidates:**")
    lines.append(f"  Stocks: {stock_hyp_cands} | Crypto: {crypto_hyp_cands}")
    if stock_hyp_cands > 0:
        for c in stock_hyps.get("candidates", [])[:3]:
            lines.append(f"  ★ {c['hypothesis']}: Sharpe {c['sharpe']:.3f}, p={c['p_value']:.4f}")
    if crypto_hyp_cands > 0:
        for c in crypto_hyps.get("candidates", [])[:3]:
            lines.append(f"  ★ {c['hypothesis']}: Sharpe {c['sharpe']:.3f}, p={c['p_value']:.4f}")
    lines.append("")
    if total > 0:
        lines.append(f"**{total} action item(s) require investigation.**")
        lines.append("Full report saved to vault/research/")
    else:
        lines.append("**No new edges found this week.** All strategies stable.")

    return "\n".join(lines)


if __name__ == "__main__":
    import os

    # Source environment for Discord credentials
    print("Running HermesForge Research Pipeline...", flush=True)
    results = run_pipeline()

    summary = build_discord_summary(results)
    print("\n" + "=" * 60)
    print(summary)
    print("=" * 60)

    # Output the summary for the cron agent to deliver
    print("\n---DISCORD_SUMMARY_START---")
    print(summary)
    print("---DISCORD_SUMMARY_END---")
