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
    """Read cumulative CORRECTED bar-level hostile STR-Q R from the jsonl ledger.

    Filtered to post-gauntlet entries (>= 2026-09-14) and EXCLUDING degenerate-stop
    outliers (outlier_excluded=True), matching the US-168 v3 "scored" population
    whose corrected net R is −8,447 R (cache/backtester_fidelity_report_v3.md).

    Returns a formatted string with sum, scored count, win rate, and date range.
    Returns 'Pessimistic R: unavailable' on error or empty.
    """
    try:
        import json, pathlib
        jsonl = pathlib.Path(__file__).parent / "hostile_fill_report_strq.jsonl"
        if not jsonl.exists():
            return "Pessimistic R: unavailable (no ledger)"
        total = 0.0
        count = 0
        wins = 0
        mindate = ""
        maxdate = ""
        with open(jsonl) as f:
            for line in f:
                r = json.loads(line)
                hr = r.get("hostile_r")
                if hr is None:
                    continue
                # Exclude degenerate-stop outliers (not part of the scored set).
                if r.get("outlier_excluded"):
                    continue
                d = (r.get("entry_date") or "")[:10]
                # Only include post-gauntlet entries
                if d < "2026-09-14":
                    continue
                total += float(hr)
                count += 1
                if float(hr) > 0:
                    wins += 1
                if d:
                    if not mindate or d < mindate:
                        mindate = d
                    if not maxdate or d > maxdate:
                        maxdate = d
        if count == 0:
            return "Pessimistic R: unavailable"
        wr = wins / count * 100
        return (f"STR-Q bar-level (corrected hostile fills): {total:+.0f}R "
                f"on {count} scored trades, {wr:.1f}% win, {mindate} to {maxdate}")
    except Exception as e:
        return f"Pessimistic R: unavailable ({e})"


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
    accepted_wins = sum(1 for r in accepted if _get_r(r) > 0)
    accepted_win_rate = (accepted_wins / len(accepted) * 100) if accepted else 0.0

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
        "accepted_win_rate": accepted_win_rate,
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

    # PNL lookback windows: 1 week and 1 month
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

    def _total(rlist):
        return sum(_get_r(r) for r in rlist)

    lines = ["📈 **Paper Trading Performance Report**\n"]

    # ── 1. Managed-portfolio performance (LEAD) ──
    total_r = _total(closed_rows)
    unmanaged_rpt = (total_r / len(closed_rows)) if closed_rows else 0.0
    lines.append("**Managed-Portfolio Performance**")
    if closed_rows and len(closed_rows) >= 10:
        sim = _simulate_portfolio_managed(closed_rows)
    else:
        sim = {"error": "insufficient closed trades (<10)"}

    if "error" in sim:
        lines.append(f"  Unmanaged: {len(closed_rows)} trades, {total_r:+.2f}R")
        lines.append("  _(Managed view needs ≥10 closed trades)_")
    else:
        ac_count = sim["accepted_count"]
        rej_count = sim["rejected_count"]
        total_count = ac_count + rej_count
        ac_r = sim["accepted_r"]
        managed_rpt = (ac_r / ac_count) if ac_count else 0.0
        lines.append(f"  Managed: {ac_count}/{total_count} trades, {ac_r:+.2f}R, "
                     f"{sim['accepted_win_rate']:.0f}% win")
        lines.append(f"  Unmanaged: {len(closed_rows)} trades, {total_r:+.2f}R")
        lines.append(f"  R/trade: {managed_rpt:+.2f}R managed vs {unmanaged_rpt:+.2f}R unmanaged")
        lines.append("  _(paper-layer, optimistic fills — see Pessimistic R below for corrected bar-level R)_")
    lines.append("")

    # ── 2. Pessimistic R (bar-level hostile fills, CORRECTED) — R first ──
    lines.append("**Pessimistic R** _(bar-level hostile fills, corrected)_")
    lines.append(f"  {_hostile_strq_r_str()}")
    lines.append("")

    # ── 3. Open positions (brief) ──
    total_heat = sum(float(r.get("position_size_pct", 0) or 0) for r in open_rows)
    lines.append(f"**Open Positions:** {len(open_rows)} open · {total_heat:.1f}% heat")
    if open_rows:
        by_strategy = {}
        for r in open_rows:
            by_strategy.setdefault(r["strategy_id"], []).append(r)
        for sid, trades in by_strategy.items():
            lines.append(f"  {sid}: {len(trades)} ({', '.join(t['ticker'] for t in trades)})")

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
