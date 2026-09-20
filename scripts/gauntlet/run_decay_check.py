#!/usr/bin/env python3
"""
One-shot decay watch runner for cron.
Maps actual trades.csv columns into the schema decay_watch expects,
runs check_decay on every active strategy, and reports results.
"""
import csv
import os
import sys
import json
from datetime import datetime, timezone

sys.path.insert(0, "/root/HermesForge/scripts/gauntlet")
from decay_watch import check_decay

TRADES_CSV = "/root/HermesForge/scripts/paper_trading/trades.csv"
ACTIVE_DIR = "/root/HermesForge/06-Strategies/Active"
HYPOTHESES_DIR = "/root/HermesForge/06-Strategies/Hypotheses"


def extract_strategy_id(md_path: str) -> str | None:
    """Extract strategy_id from YAML frontmatter in a .md file.
    Prioritizes 'strategy_id:' over 'id:' since some files use 'id:' as the note identifier.
    Handles malformed frontmatter with duplicate --- separators."""
    with open(md_path) as f:
        lines = f.readlines()

    strategy_id_val = None
    id_val = None

    for line in lines:
        stripped = line.strip()

        # Stop scanning once we leave the frontmatter (first --- after the opening ---)
        if stripped.startswith("---") and (strategy_id_val or id_val):
            # We're past the frontmatter
            pass

        if stripped.startswith("strategy_id:"):
            strategy_id_val = stripped.split("strategy_id:", 1)[1].strip()
        elif stripped.startswith("|strategy_id:"):
            strategy_id_val = stripped.split("|strategy_id:", 1)[1].strip()
        elif stripped.startswith("id:") and stripped.split("id:", 1)[1].strip().startswith("STR-"):
            id_val = stripped.split("id:", 1)[1].strip()

    # strategy_id takes priority
    return strategy_id_val or id_val


def load_trades(csv_path: str, strategy_ids: set) -> dict:
    """
    Read trades CSV and map to decay_watch schema.
    CSV has: r_multiple, gauntlet_r, cost_drag_r (no pnl, realised_slippage, modelled_slippage).
    We map: r_multiple → pnl (proxy since risk is constant), gauntlet_r → R.
    """
    by_sid = {sid: [] for sid in strategy_ids}
    try:
        with open(csv_path) as f:
            reader = csv.DictReader(f)
            for row in reader:
                sid = row.get("strategy_id", "")
                if sid not in by_sid:
                    continue
                # Only count closed trades
                status = row.get("status", "")
                if status != "closed":
                    continue
                try:
                    r_mult = float(row.get("r_multiple", 0) or 0)
                except ValueError:
                    r_mult = 0.0
                try:
                    gauntlet_r = float(row.get("gauntlet_r", 0) or 0)
                except ValueError:
                    gauntlet_r = 0.0
                try:
                    cost_drag = float(row.get("cost_drag_r", 0) or 0)
                except ValueError:
                    cost_drag = 0.0

                by_sid[sid].append({
                    "pnl": r_mult,
                    "R": gauntlet_r,
                    "realised_slippage": cost_drag,
                    "modelled_slippage": 0.0,  # Not in CSV; slippage check won't trigger
                    "ticker": row.get("ticker", ""),
                })
    except FileNotFoundError:
        print(f"WARNING: trades CSV not found at {csv_path}")

    return by_sid


def main():
    # 1. Discover active strategies
    active_files = sorted(
        f for f in os.listdir(ACTIVE_DIR) if f.endswith(".md")
    )
    active_map = {}  # strategy_id → file_path
    for fname in active_files:
        path = os.path.join(ACTIVE_DIR, fname)
        sid = extract_strategy_id(path)
        if sid:
            active_map[sid] = path
        else:
            print(f"WARNING: Could not extract strategy_id from {fname}")

    print(f"Active strategies found: {len(active_map)}")
    for sid, path in active_map.items():
        fname = os.path.basename(path)
        print(f"  {sid}  ←  {fname}")

    # 2. Load trades, mapping only to active strategy IDs
    trades_by_sid = load_trades(TRADES_CSV, set(active_map.keys()))
    for sid, trades in trades_by_sid.items():
        print(f"  {sid}: {len(trades)} closed trades loaded")

    # 3. Run decay check on each active strategy
    results = []
    for sid in sorted(active_map.keys()):
        trades = trades_by_sid.get(sid, [])
        result = check_decay(sid, trades)
        results.append({
            "strategy_id": sid,
            "file": os.path.basename(active_map[sid]),
            "trades_loaded": len(trades),
            **result,
        })

    # 4. Summarize
    print("\n" + "=" * 60)
    print("DECAY WATCH RESULTS")
    print("=" * 60)

    any_decayed = False
    for r in results:
        sid = r["strategy_id"]
        fname = r["file"]
        healthy = r["healthy"]
        metrics = r["metrics"]
        trades_n = r["trades_loaded"]

        status_icon = "✅" if healthy else "🔴 DECAY"
        print(f"\n{status_icon} {sid} ({fname}) — {trades_n} trades")
        print(f"   Trailing PF: {metrics.get('trailing_pf', 'N/A')}")
        print(f"   Avg-R windows: {metrics.get('avg_r_windows', 'N/A')}")
        print(f"   Slippage violations: {metrics.get('slippage_violations', 0)}")

        if not healthy:
            any_decayed = True
            print(f"   TRIGGER: {r['trigger']}")

    # 5. Output JSON for downstream processing
    output = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "any_decayed": any_decayed,
        "results": [
            {
                "strategy_id": r["strategy_id"],
                "file": r["file"],
                "healthy": r["healthy"],
                "trigger": r.get("trigger"),
                "metrics": r["metrics"],
                "trades_loaded": r["trades_loaded"],
            }
            for r in results
        ],
    }
    print(f"\n--- JSON ---")
    print(json.dumps(output, indent=2))

    return 0 if not any_decayed else 1


if __name__ == "__main__":
    sys.exit(main())