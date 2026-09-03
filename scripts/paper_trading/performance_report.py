#!/usr/bin/env python3
"""
performance_report.py — HermesForge EPIC-010 (US-071)

Reads trades.csv and produces an evidence-based paper trading performance
summary: open positions/heat, recently closed trades, and running totals
by strategy and asset class. No editorializing on small sample sizes --
states counts plainly per the user's evidence-based analysis preference.

Usage:
    python3 performance_report.py [--since-hours N]
"""

import sys
import argparse
import pathlib
import datetime

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import trade_log


def _rows() -> list[dict]:
    return trade_log._read_all_rows()


def _dedupe_rows(rows: list[dict]) -> list[dict]:
    """Deduplicate by signal_id — keep the LAST entry for each.
    
    Known issue: _write_all_rows() had a bug that created duplicate rows
    with the same signal_id. This ensures PNL calculations don't double-count.
    The last row in iteration order (most recently written) is kept.
    """
    seen = {}  # signal_id → row
    for r in rows:
        sig = r.get("signal_id", "")
        if not sig:
            continue
        # Always keep the most recently encountered row for this signal_id
        seen[sig] = r
    return list(seen.values())


def _build_pnl_section(closed_rows: list[dict], label: str) -> list[str]:
    """Build a PNL section for a subset of closed trades."""
    lines = []
    if not closed_rows:
        lines.append(f"**{label}:** No closed trades in period.")
        return lines
    
    r_vals = [float(r.get("r_multiple", 0) or 0) for r in closed_rows]
    total_r = sum(r_vals)
    wins = [v for v in r_vals if v > 0]
    wr = len(wins) / len(r_vals) * 100
    avg_r = total_r / len(r_vals)
    
    # Max drawdown (running peak-to-trough)
    peak = 0.0
    cum = 0.0
    max_dd = 0.0
    for v in r_vals:
        cum += v
        if cum > peak:
            peak = cum
        dd = peak - cum
        if dd > max_dd:
            max_dd = dd
    
    lines.append(f"**{label}:** {len(closed_rows)} trades, {wr:.0f}% win rate, {total_r:+.2f}R total, avg {avg_r:+.3f}R, max DD {max_dd:.2f}R")
    return lines


def build_report(since_hours: int = 24) -> str:
    rows = _dedupe_rows(_rows())
    open_rows = [r for r in rows if r["status"] == "open"]
    closed_rows = [r for r in rows if r["status"] == "closed"]

    cutoff = datetime.datetime.utcnow() - datetime.timedelta(hours=since_hours)
    recent_closed = []
    for r in closed_rows:
        try:
            exit_dt = datetime.datetime.fromisoformat(r["exit_date"])
        except (ValueError, TypeError):
            continue
        if exit_dt >= cutoff:
            recent_closed.append(r)

    # PNL lookback windows: 1 week and 1 month (for trend analysis)
    now = datetime.datetime.utcnow()
    week_cutoff = now - datetime.timedelta(days=7)
    month_cutoff = now - datetime.timedelta(days=30)
    week_closed = []
    month_closed = []
    for r in closed_rows:
        try:
            exit_dt = datetime.datetime.fromisoformat(r["exit_date"])
        except (ValueError, TypeError):
            continue
        if exit_dt >= week_cutoff:
            week_closed.append(r)
        if exit_dt >= month_cutoff:
            month_closed.append(r)

    lines = ["📈 **Paper Trading Performance Report**\n"]

    # --- Open positions ---
    total_heat = sum(float(r.get("position_size_pct", 0) or 0) for r in open_rows)
    lines.append(f"**Open Positions:** {len(open_rows)} (aggregate heat: {total_heat:.2f}%)")
    if open_rows:
        by_strategy = {}
        for r in open_rows:
            by_strategy.setdefault(r["strategy_id"], []).append(r)
        for sid, trades in by_strategy.items():
            lines.append(f"  • {sid}: {len(trades)} open ({', '.join(t['ticker'] for t in trades)})")
    lines.append("")

    # --- Recently closed ---
    lines.append(f"**Closed (last {since_hours}h):** {len(recent_closed)}")
    if recent_closed:
        wins = [r for r in recent_closed if float(r.get("r_multiple", 0) or 0) > 0]
        win_rate = len(wins) / len(recent_closed) * 100
        avg_r = sum(float(r.get("r_multiple", 0) or 0) for r in recent_closed) / len(recent_closed)
        lines.append(f"  Win rate: {win_rate:.0f}% ({len(wins)}/{len(recent_closed)}) | Avg R: {avg_r:+.2f}")

        best = max(recent_closed, key=lambda r: float(r.get("r_multiple", 0) or 0))
        worst = min(recent_closed, key=lambda r: float(r.get("r_multiple", 0) or 0))
        lines.append(f"  Best: {best['ticker']} ({best['strategy_id']}) {float(best['r_multiple']):+.2f}R")
        lines.append(f"  Worst: {worst['ticker']} ({worst['strategy_id']}) {float(worst['r_multiple']):+.2f}R")
    lines.append("")

    # --- PNL trend (1-week + 1-month lookback) ---
    lines.append("**PNL Trend (lookback):**")
    lines.extend(_build_pnl_section(week_closed, "Last 7 days"))
    lines.extend(_build_pnl_section(month_closed, "Last 30 days"))
    lines.append("")

    # --- Running totals since inception ---
    lines.append("**Running Totals (since inception):**")
    by_strategy_all = {}
    if not closed_rows:
        lines.append("  No closed trades yet.")
    else:
        # Overall summary
        all_r = [float(r.get("r_multiple", 0) or 0) for r in closed_rows]
        total_r = sum(all_r)
        wins = [r for r in all_r if r > 0]
        wr = len(wins) / len(all_r) * 100
        avg_r = total_r / len(all_r)
        # Max drawdown (running peak-to-trough on cumulative R)
        peak = 0.0
        cum = 0.0
        max_dd = 0.0
        for r in all_r:
            cum += r
            if cum > peak:
                peak = cum
            dd = peak - cum
            if dd > max_dd:
                max_dd = dd
        lines.append(f"  Total: {len(closed_rows)} trades, {wr:.0f}% win, {total_r:+.2f}R realized, avg {avg_r:+.3f}R, max DD {max_dd:.2f}R")

        # By strategy
        lines.append("")
        lines.append("**By Strategy:**")
        by_strategy_all = {}
        for r in closed_rows:
            by_strategy_all.setdefault(r["strategy_id"], []).append(r)
        for sid, trades in sorted(by_strategy_all.items()):
            r_vals = [float(t.get("r_multiple", 0) or 0) for t in trades]
            t_wins = [v for v in r_vals if v > 0]
            t_wr = len(t_wins) / len(r_vals) * 100
            t_avg = sum(r_vals) / len(r_vals)
            t_total = sum(r_vals)
            lines.append(f"  • {sid}: {len(trades)} trades, {t_wr:.0f}% win, {t_total:+.2f}R, avg {t_avg:+.3f}R")

        # By asset class
        lines.append("")
        lines.append("**By Asset Class:**")
        by_class = {}
        for r in closed_rows:
            by_class.setdefault(r.get("asset_class", "unknown"), []).append(r)
        for ac, trades in sorted(by_class.items()):
            r_vals = [float(t.get("r_multiple", 0) or 0) for t in trades]
            t_wins = [v for v in r_vals if v > 0]
            t_wr = len(t_wins) / len(r_vals) * 100
            t_total = sum(r_vals)
            lines.append(f"  • {ac}: {len(trades)} trades, {t_wr:.0f}% win, {t_total:+.2f}R")

    # --- Strategy correlation (need 5+ closed trades per strategy) ---
    if closed_rows and len(by_strategy_all) >= 2:
        lines.append("")
        lines.append("**Strategy Correlation (closed trades, overlap periods):**")
        # Check if any strategies tend to draw down at the same time
        import datetime as dt
        strategy_drawdowns = {}
        for sid, trades in by_strategy_all.items():
            if len(trades) < 3:
                continue
            # Compute worst drawdown period for this strategy
            r_seq = [(t.get("exit_date", ""), float(t.get("r_multiple", 0) or 0)) for t in trades]
            r_seq.sort(key=lambda x: x[0])
            peak, cum, worst_dd, worst_start, worst_end = 0, 0, 0, "", ""
            for d, r in r_seq:
                cum += r
                if cum > peak:
                    peak = cum
                dd = peak - cum
                if dd > worst_dd:
                    worst_dd = dd
                    worst_start = d
                    worst_end = d
            strategy_drawdowns[sid] = {"worst_dd": worst_dd, "dd_start": worst_start[:10], "dd_end": worst_end[:10]}

        # Check for overlapping drawdown periods
        overlap_found = False
        sids = list(strategy_drawdowns.keys())
        for i in range(len(sids)):
            for j in range(i + 1, len(sids)):
                a, b = strategy_drawdowns[sids[i]], strategy_drawdowns[sids[j]]
                # Simple overlap: same month
                a_month = a["dd_start"][:7]
                b_month = b["dd_start"][:7]
                if a_month and b_month and a_month == b_month:
                    overlap_found = True
                    lines.append(f"  ⚠️ {sids[i]} and {sids[j]} both hit worst drawdown in {a_month}")
        if not overlap_found:
            lines.append("  No overlapping drawdown periods detected between strategies.")
        lines.append(f"  _{len(strategy_drawdowns)} strategies with 3+ closed trades analyzed._")

    if len(closed_rows) < 10:
        lines.append("")
        lines.append(f"_Note: only {len(closed_rows)} closed trades total -- sample size too small for reliable conclusions._")

    return "\n".join(lines)


def post_to_discord(report_text: str, channel_id: str, dry_run: bool = False) -> dict:
    """Post the performance report to a Discord channel via bot REST API."""
    import subprocess, json, os

    token = os.environ.get("DISCORD_BOT_TOKEN", "")
    if not token:
        return {"status": "error", "message": "DISCORD_BOT_TOKEN not set"}

    # Split into chunks if > 2000 chars (Discord limit)
    chunks = []
    current = ""
    for line in report_text.split("\n"):
        if len(current) + len(line) + 1 > 1900:
            if current:
                chunks.append(current)
            current = line
        else:
            current += "\n" + line if current else line
    if current:
        chunks.append(current)

    if dry_run:
        for i, chunk in enumerate(chunks):
            print(f"  [dry-run chunk {i+1}/{len(chunks)}] {chunk[:80]}...")
        return {"status": "dry_run", "chunks": len(chunks)}

    results = []
    for chunk in chunks:
        payload = json.dumps({"content": chunk}, ensure_ascii=False)
        with open("/tmp/perf_report_chunk.json", "w") as f:
            f.write(payload)
        result = subprocess.run(
            ["curl", "-s", "-X", "POST",
             "-H", f"Authorization: Bot {token}",
             "-H", "Content-Type: application/json",
             "--data-binary", "@/tmp/perf_report_chunk.json",
             f"https://discord.com/api/v10/channels/{channel_id}/messages"],
            capture_output=True, text=True, timeout=15
        )
        resp = json.loads(result.stdout)
        if "id" in resp:
            results.append({"status": "ok", "id": resp["id"]})
        else:
            results.append({"status": "error", "response": resp})
        import time
        time.sleep(1)

    return {"status": "ok" if all(r["status"] == "ok" for r in results) else "partial", "results": results}


def main():
    ap = argparse.ArgumentParser(description="HermesForge paper trading performance report")
    ap.add_argument("--since-hours", type=int, default=24)
    ap.add_argument("--post", metavar="CHANNEL_ID", help="Post report to Discord channel")
    ap.add_argument("--dry-run", action="store_true", help="Show what would be posted without posting")
    args = ap.parse_args()

    report = build_report(since_hours=args.since_hours)

    if args.post:
        result = post_to_discord(report, args.post, dry_run=args.dry_run)
        if result["status"] == "ok":
            print(f"Posted to Discord ({len(result['results'])} messages)")
        elif result["status"] == "dry_run":
            print(f"Dry run: {result['chunks']} chunks would be posted")
        else:
            print(f"Post result: {result}")
    else:
        print(report)


if __name__ == "__main__":
    main()
