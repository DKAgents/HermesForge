#!/usr/bin/env python3
"""
performance_report.py — HermesForge EPIC-010 (US-071)

Reads trades.csv and produces an evidence-based paper trading performance
summary: open positions/heat, recently closed trades, and running totals
by strategy and asset class. No editorializing on small sample sizes --
states counts plainly per the user's evidence-based analysis preference.

Usage:
    python3 performance_report.py [--since-hours N] [--since-date YYYY-MM-DD]
"""

import sys
import argparse
import pathlib
import datetime

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import trade_log

# ── Gauntlet go-live: first date trades were captured with cost-adjusted fills ──
GAUNTLET_CUTOVER = datetime.date(2026, 9, 14)


def _rows() -> list[dict]:
    return trade_log._read_all_rows()


def _get_r(trade: dict) -> float:
    """Return cost-adjusted R when available, otherwise raw r_multiple."""
    val = trade.get("gauntlet_r", None)
    if val is None or val == "" or val == '':
        val = trade.get("r_multiple", 0)
    try:
        return float(val)
    except (ValueError, TypeError):
        return 0.0


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
    
    r_vals = [_get_r(r) for r in closed_rows]
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


def _hostile_strq_r_str() -> str:
    """Read cumulative hostile STR-Q R from the hostile fill jsonl file,
    filtered to post-gauntlet entries only (>= 2026-09-14).
    Returns a formatted string with sum, record count, and date range.
    Returns 'Pessimistic R: unavailable' on error."""
    try:
        import json, pathlib
        jsonl = pathlib.Path(__file__).parent / "hostile_fill_report_strq.jsonl"
        if not jsonl.exists():
            return "Pessimistic R: unavailable"
        total = 0.0
        count = 0
        mindate = ""
        maxdate = ""
        with open(jsonl) as f:
            for line in f:
                r = json.loads(line)
                hr = r.get("hostile_r")
                if hr is None:
                    continue
                d = (r.get("entry_date") or "")[:10]
                # Only include post-gauntlet entries
                if d < "2026-09-14":
                    continue
                total += float(hr)
                count += 1
                if d:
                    if not mindate or d < mindate:
                        mindate = d
                    if not maxdate or d > maxdate:
                        maxdate = d
        if count == 0:
            return "Pessimistic R: unavailable"
        return (f"Pessimistic R (worst-case L2 order-book fills): {total:+.0f}R"
                f" on {count} rows, {mindate} to {maxdate}")
    except Exception:
        return "Pessimistic R: unavailable"


def _simulate_portfolio_managed(closed_rows: list) -> dict:
    """Replay closed trades chronologically through the portfolio risk guard.
    Returns stats on which trades would be accepted vs rejected under
    the current production limits (8 pos, 7% heat, 3 sector, 5 asset class).

    Returns:
        {accepted_count, rejected_count, accepted_r, rejected_r, accepted_by_strategy, rejected_by_strategy,
         rejected_reasons: {reason: count}, peak_heat, peak_positions, bottleneck_strategies}
    """
    try:
        from portfolio_risk_guard import MAX_CONCURRENT_POSITIONS, MAX_PORTFOLIO_HEAT_PCT, MAX_SAME_SECTOR, MAX_SAME_ASSET_CLASS, _get_sector
    except ImportError:
        return {"error": "portfolio_risk_guard not importable"}

    # Sort chronologically by entry date
    sorted_trades = sorted(closed_rows, key=lambda r: r.get("entry_date", ""))

    # State tracking — simulate portfolio state as trades are opened/closed
    open_positions = []  # list of (exit_date, position_size_pct, ticker, asset_class, sector)
    accepted = []
    rejected = []
    rejected_reasons = {}
    peak_heat = 0.0
    peak_positions = 0

    for row in sorted_trades:
        # First, process any positions that closed before this entry date
        entry_date = row.get("entry_date", "")
        open_positions = [p for p in open_positions if p[0] >= entry_date]

        # Current portfolio state
        current_positions = len(open_positions)
        current_heat = sum(float(p[1]) for p in open_positions)
        risk_pct = float(row.get("position_size_pct", 0) or 0)

        # Sector tracking
        ticker = row.get("ticker", "")
        asset_class = row.get("asset_class", "stock")
        new_sector = _get_sector(ticker, asset_class)

        sector_counts = {}
        asset_class_counts = {}
        for p in open_positions:
            s = p[4]
            sector_counts[s] = sector_counts.get(s, 0) + 1
            ac = p[3]
            asset_class_counts[ac] = asset_class_counts.get(ac, 0) + 1

        # Check gates
        reason = None
        if current_positions >= MAX_CONCURRENT_POSITIONS:
            reason = f"max positions ({current_positions}/{MAX_CONCURRENT_POSITIONS})"
        elif current_heat + risk_pct > MAX_PORTFOLIO_HEAT_PCT:
            reason = f"heat limit ({current_heat:.1f}% + {risk_pct:.1f}% > {MAX_PORTFOLIO_HEAT_PCT}%)"
        elif sector_counts.get(new_sector, 0) >= MAX_SAME_SECTOR:
            reason = f"sector limit: {new_sector} ({sector_counts.get(new_sector, 0)}/{MAX_SAME_SECTOR})"
        elif asset_class_counts.get(asset_class, 0) >= MAX_SAME_ASSET_CLASS:
            reason = f"asset class limit: {asset_class} ({asset_class_counts.get(asset_class, 0)}/{MAX_SAME_ASSET_CLASS})"

        if reason:
            rejected.append(row)
            rejected_reasons[reason] = rejected_reasons.get(reason, 0) + 1
        else:
            accepted.append(row)
            exit_date = row.get("exit_date", "2099-12-31")
            # Add to simulated open positions
            open_positions.append((exit_date, risk_pct, ticker, asset_class, new_sector))
            current_heat += risk_pct
            current_positions += 1

        if current_heat > peak_heat:
            peak_heat = current_heat
        if current_positions > peak_positions:
            peak_positions = current_positions

    # Calculate R values
    accepted_r = sum(_get_r(r) for r in accepted)
    rejected_r = sum(_get_r(r) for r in rejected)

    # By strategy
    accepted_by_strategy = {}
    rejected_by_strategy = {}
    for r in accepted:
        sid = r.get("strategy_id", "unknown")
        accepted_by_strategy[sid] = accepted_by_strategy.get(sid, 0) + 1
    for r in rejected:
        sid = r.get("strategy_id", "unknown")
        rejected_by_strategy[sid] = rejected_by_strategy.get(sid, 0) + 1

    # Bottleneck: which strategies get rejected most?
    bottleneck = sorted(rejected_by_strategy.items(), key=lambda x: -x[1])[:5]

    return {
        "accepted_count": len(accepted),
        "rejected_count": len(rejected),
        "accepted_r": accepted_r,
        "rejected_r": rejected_r,
        "accepted_by_strategy": accepted_by_strategy,
        "rejected_by_strategy": rejected_by_strategy,
        "rejected_reasons": rejected_reasons,
        "peak_heat": round(peak_heat, 2),
        "peak_positions": peak_positions,
        "bottleneck": bottleneck,
        "limits": {
            "max_positions": MAX_CONCURRENT_POSITIONS,
            "max_heat_pct": MAX_PORTFOLIO_HEAT_PCT,
            "max_same_sector": MAX_SAME_SECTOR,
            "max_same_asset_class": MAX_SAME_ASSET_CLASS,
        }
    }


def build_report(since_hours: int = 24, since_date: datetime.date = None) -> str:
    rows = _dedupe_rows(_rows())
    open_rows = [r for r in rows if r["status"] == "open"]
    
    # Filter closed rows by gauntlet cutover if specified
    if since_date is None:
        since_date = GAUNTLET_CUTOVER
    closed_rows = []
    skipped_pre_gauntlet = 0
    for r in rows:
        if r["status"] != "closed":
            continue
        try:
            exit_dt = datetime.datetime.fromisoformat(r["exit_date"]).date()
        except (ValueError, TypeError):
            # Try entry_date as fallback
            try:
                entry = r.get("entry_date", "")
                if " " in entry:
                    entry = entry.split(" ")[0]
                exit_dt = datetime.date.fromisoformat(entry)
            except (ValueError, TypeError):
                exit_dt = None
        if exit_dt is None or exit_dt < since_date:
            skipped_pre_gauntlet += 1
            continue
        closed_rows.append(r)

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
        wins = [r for r in recent_closed if _get_r(r) > 0]
        win_rate = len(wins) / len(recent_closed) * 100
        avg_r = sum(_get_r(r) for r in recent_closed) / len(recent_closed)
        lines.append(f"  Win rate: {win_rate:.0f}% ({len(wins)}/{len(recent_closed)}) | Avg R: {avg_r:+.2f}")

        best = max(recent_closed, key=lambda r: _get_r(r))
        worst = min(recent_closed, key=lambda r: _get_r(r))
        lines.append(f"  Best: {best['ticker']} ({best['strategy_id']}) {float(best['r_multiple']):+.2f}R (gauntlet: {_get_r(best):+.2f}R)")
        lines.append(f"  Worst: {worst['ticker']} ({worst['strategy_id']}) {float(worst['r_multiple']):+.2f}R (gauntlet: {_get_r(worst):+.2f}R)")
    lines.append("")

    # --- PNL trend (1-week + 1-month lookback) ---
    lines.append("**PNL Trend (lookback):**")
    lines.extend(_build_pnl_section(week_closed, "Last 7 days"))
    lines.extend(_build_pnl_section(month_closed, "Last 30 days"))
    lines.append("")

    # --- Running totals since gauntlet go-live ---
    cutover_str = since_date.isoformat()
    lines.append(f"**Running Totals (since {cutover_str} — gauntlet go-live):**")
    if skipped_pre_gauntlet:
        lines.append(f"  _(+{skipped_pre_gauntlet} pre-gauntlet trades excluded)_")
    lines.append("")
    lines.append("**Optimistic R** _(cost-adjusted fills — mid-price minus typical slippage + venue costs, ~12 bps crypto / ~2 bps stocks):_")
    by_strategy_all = {}
    if not closed_rows:
        lines.append("  No closed trades yet.")
    else:
        # Overall summary
        all_r = [_get_r(r) for r in closed_rows]
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
        lines.append("")
        lines.append(f"  **{_hostile_strq_r_str()}** _(worst-case L2 order-book fill — simulates market order absorption against actual order book depth)_")

        # By strategy
        lines.append("")
        lines.append("**By Strategy:**")
        by_strategy_all = {}
        for r in closed_rows:
            by_strategy_all.setdefault(r["strategy_id"], []).append(r)
        for sid, trades in sorted(by_strategy_all.items()):
            r_vals = [_get_r(t) for t in trades]
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
            r_vals = [_get_r(t) for t in trades]
            t_wins = [v for v in r_vals if v > 0]
            t_wr = len(t_wins) / len(r_vals) * 100
            t_total = sum(r_vals)
            lines.append(f"  • {ac}: {len(trades)} trades, {t_wr:.0f}% win, {t_total:+.2f}R")

    # --- Portfolio-Managed Simulation ---
    if closed_rows and len(closed_rows) >= 10:
        lines.append("")
        lines.append("**📊 Portfolio-Managed View** _(simulated: same trades, gated by portfolio risk limits):_")
        sim = _simulate_portfolio_managed(closed_rows)
        if "error" in sim:
            lines.append(f"  Simulation unavailable: {sim['error']}")
        else:
            limits = sim["limits"]
            lines.append(f"  Limits: {limits['max_positions']} concurrent positions, {limits['max_heat_pct']}% max heat, "
                        f"{limits['max_same_sector']} per sector, {limits['max_same_asset_class']} per asset class")
            lines.append("")
            ac_r = sim["accepted_r"]
            rej_r = sim["rejected_r"]
            ac_count = sim["accepted_count"]
            rej_count = sim["rejected_count"]
            total_count = ac_count + rej_count
            lines.append(f"  Accepted: {ac_count}/{total_count} trades ({ac_count/total_count*100:.0f}%), {ac_r:+.2f}R")
            lines.append(f"  Rejected: {rej_count}/{total_count} trades ({rej_count/total_count*100:.0f}%), {rej_r:+.2f}R")
            lines.append(f"  Peak heat: {sim['peak_heat']}%  |  Peak positions: {sim['peak_positions']}")
            lines.append("")
            # Rejection reasons
            if sim["rejected_reasons"]:
                lines.append("  **Rejection reasons:**")
                for reason, count in sorted(sim["rejected_reasons"].items(), key=lambda x: -x[1]):
                    lines.append(f"    • {reason}: {count} trades")
            # Bottleneck strategies
            if sim["bottleneck"]:
                lines.append("  **Most rejected strategies:**")
                for sid, count in sim["bottleneck"]:
                    lines.append(f"    • {sid}: {count} rejected")

        lines.append("")
        lines.append("**📈 Portfolio Impact — Managed vs Unmanaged:**")
        if "error" in sim:
            lines.append("  Simulation unavailable")
        else:
            lines.append(f"  Unmanaged: {len(closed_rows)} trades, {sum(_get_r(r) for r in closed_rows):+.2f}R")
            lines.append(f"  Managed:   {sim['accepted_count']} trades, {sim['accepted_r']:+.2f}R")
            # Efficiency: R per trade
            unmanaged_rpt = sum(_get_r(r) for r in closed_rows) / len(closed_rows) if closed_rows else 0
            managed_rpt = sim['accepted_r'] / sim['accepted_count'] if sim['accepted_count'] else 0
            lines.append(f"  R/trade:   {managed_rpt:+.3f}R managed vs {unmanaged_rpt:+.3f}R unmanaged")
            lines.append(f"  Efficiency gain: managed trades average {managed_rpt - unmanaged_rpt:+.3f}R more per trade")
            lines.append(f"  Total R given up: {sim['rejected_r']:+.2f}R across {sim['rejected_count']} rejected trades")
            lines.append(f"  _(Portfolio limits: {limits['max_positions']} pos, {limits['max_heat_pct']}% heat, "
                        f"{limits['max_same_sector']} sector, {limits['max_same_asset_class']} asset class)_")
        # End of managed section

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
            r_seq = [(t.get("exit_date", ""), _get_r(t)) for t in trades]
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
    ap.add_argument("--since-date", type=str, default=None,
                    help="Only include trades on or after this date (YYYY-MM-DD). Default: 2026-09-14 (gauntlet go-live)")
    ap.add_argument("--all", action="store_true", help="Include all trades since inception (override since-date)")
    ap.add_argument("--post", metavar="CHANNEL_ID", help="Post report to Discord channel")
    ap.add_argument("--dry-run", action="store_true", help="Show what would be posted without posting")
    args = ap.parse_args()
    
    since_date = None
    if not args.all:
        if args.since_date:
            since_date = datetime.date.fromisoformat(args.since_date)
        # else: use default GAUNTLET_CUTOVER inside build_report

    report = build_report(since_hours=args.since_hours, since_date=since_date)

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
