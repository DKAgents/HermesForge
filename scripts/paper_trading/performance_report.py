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
import json
import argparse
import pathlib
import datetime

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import trade_log

# ── Gauntlet go-live: first date trades were captured with cost-adjusted fills ──
GAUNTLET_CUTOVER = datetime.date(2026, 9, 14)

# ── R source-of-truth (US-223) ──────────────────────────────────────────────
# Bar-level hostile-fill ledgers (the ONLY fill-realistic R sources). Two are
# authoritative; the frozen v2 STR-Q ledger and the .bak.us169 backup are never
# read (lu-02: v1 is the authoritative scoreboard).
STR_Q_STRATEGY = "STR-Q-liquidity-sweep"
# The six swing strategies covered by hostile_fills.py (daily bars).
SWING_STRATEGIES = {
    "STR-VIXC-vix-contango-breakout",
    "STR-B-macd-histogram-divergence",
    "STR-A-ma-pullback-fibonacci",
    "STR-I-adaptive-trend",
    "STR-D-sr-role-reversal",
    "STR-DEBASEMENT-treasury-buyback",
}
STRQ_LEDGER = pathlib.Path(__file__).parent / "hostile_fill_report_strq.jsonl"
SWING_LEDGER = pathlib.Path(__file__).parent / "hostile_fill_report.jsonl"

# Join keys per strategy: STR-Q uses signal_id (unique intraday identity), the
# six swing strategies use trade_id (daily, signal_id == trade_id).
def _join_key(strategy_id: str, row: dict) -> str:
    if strategy_id == STR_Q_STRATEGY:
        return row.get("signal_id", "")
    if strategy_id in SWING_STRATEGIES:
        return row.get("trade_id", "")
    return ""


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


def _load_hostile_ledger(path: pathlib.Path, key_field: str) -> dict:
    """Read a hostile-fill jsonl into a canonical scored map {key: row}.

    Canonical row = the `closed` stage row with a non-null `hostile_r`; on
    multiple such rows the latest `timestamp_utc` wins. skip/open/entry rows
    (hostile_r is None) contribute no scored entry. The frozen v2 and the
    .bak.us169 backup are NEVER read because they are never passed here.
    """
    canonical = {}
    if not path.exists():
        return canonical
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            if r.get("stage") != "closed":
                continue
            if r.get("hostile_r") is None:
                continue
            key = r.get(key_field, "")
            if not key:
                continue
            cur = canonical.get(key)
            if cur is None or (r.get("timestamp_utc") or "") >= (cur.get("timestamp_utc") or ""):
                canonical[key] = r
    return canonical


def resolve_fill_realistic(closed_rows: list[dict]) -> dict:
    """Single R source-of-truth (US-223).

    Primary: bar-level hostile_r from the two ACTIVE hostile-fill ledgers —
    STR-Q joined on signal_id, the six swing strategies on trade_id. This is
    the ONLY value permitted as the headline. outlier_excluded rows and trades
    with no joinable hostile_r (skip/open stage, purged bars) are NOT scored:
    they are counted in `unscored_count`, never silently filled with gauntlet_r.

    Secondary: gauntlet_r (cost-adjusted but close-fill — NOT fill-realistic),
    summed separately for the labelled reference line.

    Returns {summary, per_trade_map}. Raises AssertionError if a (strategy, key)
    resolves in both active ledgers (cross-ledger overlap must not happen).
    """
    strq_map = _load_hostile_ledger(STRQ_LEDGER, "signal_id")
    swing_map = _load_hostile_ledger(SWING_LEDGER, "trade_id")

    per_trade_map = {}          # (strategy_id, key) -> hostile_r float
    scored = []                 # list of (strategy_id, hostile_r, entry_date)
    unscored_count = 0
    gauntlet_total = 0.0
    gauntlet_count = 0

    for row in closed_rows:
        sid = row.get("strategy_id", "")
        key = _join_key(sid, row)

        # Secondary (gauntlet_r / raw r_multiple) — always computed, never the headline.
        gauntlet_total += _get_r(row)
        gauntlet_count += 1

        # Primary resolution (US-224): prefer the persisted authoritative
        # hostile_r already backfilled onto trades.csv. This is, by construction,
        # the same closed-stage/non-null/latest-wins value (outlier rows left
        # empty during backfill). Fall back to the jsonls only when empty, so the
        # report decouples from the ledgers over time.
        hr_row = None
        value = None
        entry_date = ""
        csv_hr = row.get("hostile_r", "")
        if csv_hr not in (None, "", "None"):
            try:
                value = float(csv_hr)
            except (ValueError, TypeError):
                value = None
            if value is not None:
                entry_date = (row.get("entry_date") or "")[:10]

        if value is None:
            if sid == STR_Q_STRATEGY:
                hr_row = strq_map.get(key)
            elif sid in SWING_STRATEGIES:
                hr_row = swing_map.get(key)
            # else: strategy has no bar-level hostile ledger -> no fill-realistic R.

            if hr_row is None or hr_row.get("outlier_excluded"):
                unscored_count += 1
                continue
            value = float(hr_row["hostile_r"])
            entry_date = (hr_row.get("entry_date") or "")[:10]

        ck = (sid, key)
        if ck in per_trade_map:
            # Cross-ledger overlap for the same canonical key — must be impossible
            # (strategy sets are disjoint); abort loudly rather than double-count.
            raise AssertionError(f"duplicate hostile resolution across ledgers: {ck}")
        per_trade_map[ck] = value
        scored.append((sid, value, entry_date))

    total_r = sum(v for _, v, _ in scored)
    wins = sum(1 for _, v, _ in scored if v > 0)
    dates = [d for _, _, d in scored if d]

    by_strategy = {}
    for sid, v, _ in scored:
        s = by_strategy.setdefault(sid, {"total_r": 0.0, "count": 0, "wins": 0})
        s["total_r"] += v
        s["count"] += 1
        if v > 0:
            s["wins"] += 1

    summary = {
        "available": len(scored) > 0,
        "total_r": total_r,
        "scored_count": len(scored),
        "wins": wins,
        "win_rate": (wins / len(scored) * 100) if scored else 0.0,
        "min_entry_date": min(dates) if dates else "",
        "max_entry_date": max(dates) if dates else "",
        "unscored_count": unscored_count,
        "closed_count": len(closed_rows),
        "gauntlet_total": gauntlet_total,
        "gauntlet_count": gauntlet_count,
        "by_strategy": by_strategy,
    }
    return {"summary": summary, "per_trade_map": per_trade_map}


def _emit_fill_realistic_headline(resolution: dict) -> list[str]:
    """Render the fill-realistic R headline from the PRIMARY resolution ONLY.

    This emitter reads ONLY the fill-realistic summary fields. It accepts the
    gauntlet (secondary) value nowhere in its signature/path — the optimistic
    number is emitted by _emit_gauntlet_secondary instead. This is the fail-closed
    guard: absence of fill-realistic data yields an explicit "unavailable" line,
    never a gauntlet_r fallback in the headline.
    """
    s = resolution["summary"]
    lines = ["**Fill-Realistic R** _(bar-level hostile fills — source of truth)_"]
    if not s["available"]:
        lines.append("  Fill-realistic R: unavailable for this window")
        reason = "no bar-level hostile ledger rows resolvable for this window (no ledger / all-skip / purged bars)"
        lines.append(f"  _({reason})_")
        return lines

    noc = (f" ({s['min_entry_date']} to {s['max_entry_date']}, post-retention only)"
           if s["min_entry_date"] else "")
    lines.append(
        f"  {s['total_r']:+.2f}R on {s['scored_count']} fill-realistic trades{noc}, "
        f"{s['win_rate']:.1f}% win"
    )
    if s["unscored_count"]:
        lines.append(
            f"  _({s['scored_count']} fill-realistic trades of {s['closed_count']} closed; "
            f"{s['unscored_count']} have no re-derivable bar-level R)_"
        )
    # Coverage provenance note (mandatory narrative, US-223 spec §2.2).
    # Verified US-223 Q3: the swing daily-bar source (~/.hermes/market_data/*.parquet,
    # incl. crypto/) is INTACT back to 2018 — the swing span IS re-derivable and
    # genuinely broader. STR-Q's 5m bars were purged (US-189), so its bar-level
    # history is recoverable only within the 5m retention window.
    lines.append("  _(swing daily-bar source intact → swing span re-derivable; STR-Q 5m pre-purge history unrecoverable — US-189)_")
    for sid in sorted(s["by_strategy"]):
        st = s["by_strategy"][sid]
        pct = (st["wins"] / st["count"] * 100) if st["count"] else 0.0
        lines.append(f"    {sid}: {st['total_r']:+.2f}R on {st['count']}, {pct:.0f}% win")
    return lines


def _emit_gauntlet_secondary(resolution: dict) -> list[str]:
    """Render the demoted cost-adjusted (close-fill) reference line.

    guantlet_r = gross_r − fee_drag; fills at signal close; no bar-level
    fill-timing correction. This is NOT fill-realistic and is labelled as such.
    """
    s = resolution["summary"]
    lines = [
        "**Cost-adjusted only** _(NOT fill-realistic — paper/close-fill, no bar-level fill-timing)_",
        f"  gauntlet_r: {s['gauntlet_total']:+.2f}R on {s['gauntlet_count']} closed trades (reference only)",
    ]
    return lines


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


def _emit_funding_carry_section() -> list[str]:
    """Render the paper-forward funding-carry (STR-FNDCARRY) status (US-230).

    Reads open positions + closed episodes from the carry module's OWN
    functions (read_ledger / load_state) — never re-parses the jsonl/state
    files separately. The funding-vs-basis SPLIT is preserved: the headline is
    funding-only (net_funding), and basis_pnl is flagged separately (US-179),
    never folded into the headline.
    """
    try:
        import funding_carry_paper as fcp
    except ImportError:
        # Carry module unavailable -> omit the section entirely rather than
        # risk corrupting the existing report.
        return []

    state = fcp.load_state()
    episodes = [r for r in fcp.read_ledger() if r.get("type") == "episode"]
    open_positions = state.get("open", {}) or {}

    header = "**Funding Carry (STR-FNDCARRY)** _(maker-only, delta-neutral, paper-forward)_"

    if not episodes and not open_positions:
        # One quiet line rather than dropping the section (US-230 AC).
        return [header, "  STR-FNDCARRY: no episodes yet — accumulating"]

    lines = [header]

    # Open carry positions (coin + entry).
    if open_positions:
        pos_lines = []
        for coin in sorted(open_positions):
            p = open_positions[coin]
            tid = p.get("trade_id", "?")
            et = p.get("entry_ts")
            if et:
                entry = datetime.datetime.fromtimestamp(
                    et / 1000, datetime.timezone.utc).strftime("%Y-%m-%d")
            else:
                entry = "?"
            pos_lines.append(f"{coin} ({tid}, since {entry})")
        lines.append("  Open: " + ", ".join(pos_lines))
    else:
        lines.append("  Open: none")

    # Closed episodes — funding-only headline, basis flagged separately.
    if episodes:
        total_net_funding = sum(float(r.get("net_funding") or 0.0) for r in episodes)
        basis_vals = [float(r["basis_pnl"]) for r in episodes
                      if r.get("basis_pnl") is not None]
        basis_has = bool(basis_vals)
        lines.append(
            f"  Closed: {len(episodes)} episode(s), net_funding "
            f"{total_net_funding:+.2f} USD (HEADLINE, funding-only)"
        )
        if basis_has:
            lines.append(
                f"  _basis_pnl: {sum(basis_vals):+.2f} USD "
                f"(flagged separately — not in headline)_"
            )
        for r in episodes:
            nf = float(r.get("net_funding") or 0.0)
            bp = r.get("basis_pnl")
            bp_str = f"{float(bp):+.2f}" if bp is not None else "n/a"
            lines.append(f"    {r.get('trade_id')}: net_funding {nf:+.2f} USD · basis {bp_str}")
    else:
        lines.append("  Closed: none")

    return lines


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

    # ── 1. Fill-realistic R (HEADLINE — bar-level hostile fills) ──
    # US-223: resolve the single R source-of-truth and lead with it. The
    # optimistic gauntlet_r is demoted to a labeled reference line (§2) and is
    # structurally incapable of appearing in this headline slot.
    resolution = resolve_fill_realistic(closed_rows)
    lines.extend(_emit_fill_realistic_headline(resolution))
    lines.append("")

    # ── 2. Cost-adjusted only (NOT fill-realistic) — demoted reference ──
    lines.extend(_emit_gauntlet_secondary(resolution))

    total_r = _total(closed_rows)  # gauntlet_r-based Managed/Unmanaged (secondary)
    unmanaged_rpt = (total_r / len(closed_rows)) if closed_rows else 0.0
    lines.append("  **Managed-Portfolio view** _(cost-adjusted, NOT fill-realistic)_")
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

    # ── 4. Funding Carry (STR-FNDCARRY) — ADDITIVE (US-230) ──
    lines.append("")
    lines.extend(_emit_funding_carry_section())

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
