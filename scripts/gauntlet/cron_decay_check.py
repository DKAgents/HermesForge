#!/usr/bin/env python3
"""Jev-powered decay check — cron runner.
Runs Jev classification on all active paper trading strategies.
Reports strategies needing intervention (decay_probability > 0.5).
"""
import sys
import os
import csv
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from jev_decay import check_decay
from run_decay_check import extract_strategy_id
from pathlib import Path

ACTIVE_DIR = Path("/root/HermesForge/trading/strategies/Active")
TRADES_CSV = Path("/root/HermesForge/scripts/paper_trading/trades.csv")

def main():
    # 1. Discover active strategies
    active_map = {}
    for fname in sorted(f for f in os.listdir(ACTIVE_DIR) if f.endswith(".md")):
        path = str(ACTIVE_DIR / fname)
        sid = extract_strategy_id(path)
        if sid:
            active_map[sid] = path

    print(f"Active strategies found: {len(active_map)}")
    for sid, path in active_map.items():
        print(f"  {sid}  ←  {os.path.basename(path)}")

    # 2. Load trades
    trades_by_sid = {}
    if TRADES_CSV.exists():
        with open(TRADES_CSV) as f:
            reader = csv.DictReader(f)
            for row in reader:
                sid = row.get("strategy_id", "")
                if sid not in active_map:
                    continue
                if row.get("status", "") != "closed":
                    continue
                if sid not in trades_by_sid:
                    trades_by_sid[sid] = []
                try:
                    r_val = float(row.get("r_multiple", row.get("gauntlet_r", 0)) or 0)
                except ValueError:
                    r_val = 0.0
                trades_by_sid[sid].append({
                    "r": r_val,
                    "date": row.get("date", row.get("exit_date", "")),
                    "ticker": row.get("ticker", ""),
                    "direction": row.get("direction", "long"),
                })

    for sid, trades in trades_by_sid.items():
        avg_r = sum(t["r"] for t in trades) / len(trades) if trades else 0
        print(f"  {sid}: {len(trades)} closed trades (avg R {avg_r:.3f})")

    # 3. Run Jev on each strategy
    any_intervention = False
    flagged = []

    for sid in sorted(active_map.keys()):
        trades = trades_by_sid.get(sid, [])
        n_trades = len(trades)

        result = check_decay(sid, recent_trades=trades)
        dp = result.decay_probability
        rec = result.recommendation
        conf = result.confidence
        jev_err = result.jev_error

        status_icon = "⚠️" if dp and dp > 0.5 else ("❌ JEV_ERR" if jev_err else "✅")
        print(f"\n{status_icon} {sid} ({n_trades} trades)")
        print(f"   Decay probability: {dp:.1%}" if dp is not None else "   Decay probability: N/A")
        print(f"   Confidence: {conf:.1%}" if conf else "   Confidence: N/A")
        print(f"   Recommendation: {rec}")
        print(f"   Jev error: {jev_err}")

        if dp and dp > 0.5:
            any_intervention = True
            flagged.append({
                "strategy_id": sid,
                "trades": n_trades,
                "decay_probability": dp,
                "confidence": conf,
                "recommendation": rec,
            })

    # 4. Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    if flagged:
        print(f"\n{len(flagged)} strategy(ies) need intervention (decay > 50%):")
        for f in flagged:
            print(f"  🔴 {f['strategy_id']}: {f['decay_probability']:.1%} decay — {f['recommendation']}")
    else:
        print("\nAll strategies healthy. No intervention needed.")

    return any_intervention


if __name__ == "__main__":
    sys.exit(main())