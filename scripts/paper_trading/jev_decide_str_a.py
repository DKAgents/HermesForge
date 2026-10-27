#!/usr/bin/env python3
"""
Jev decision request for STR-A-ma-pullback-fibonacci.
Follow-up after decay check flagged 80% decay probability.
"""
import sys
sys.path.insert(0, '/root/HermesForge/scripts/gauntlet')

from jev_client import JevClient
import json

strategy_id = "STR-A-ma-pullback-fibonacci"

# Stats from the decay check run
stats = {
    "strategy_id": strategy_id,
    "recent_stats": {
        "count": 10,
        "avg_r": -0.096,
        "win_rate": 0.1,
        "profit_factor": 0.68,
        "current_losing_streak": 2,
        "max_losing_streak": 2,
    },
    "backtest_baseline": {}
}

jev = JevClient()

# Decision request: what action to take
try:
    decision = jev.noul(
        state=stats,
        instructions=f"Strategy {strategy_id} shows 80% edge decay probability. "
                     f"It has 10 closed trades with avg R -0.096, 10% win rate, "
                     f"profit factor 0.68, consecutive losing streak of 2. "
                     f"What action should be taken?",
        true_criteria="Demote: remove from active strategies, archive to dead strategies. "
                     "The edge is broken, not just a drawdown. Insufficient trade count "
                     "to justify further paper trading.",
        false_criteria="Watch: keep in active but reduce position sizing. "
                      "The sample is small (10 trades). May recover. "
                      "Mark for review in 2 weeks."
    )
    print(f"Jev decision on demotion probability: {decision:.0%}")
    print(f"Interpretation: {'DEMOTE' if decision > 0.5 else 'WATCH' if decision > 0.25 else 'KEEP'}")
except Exception as e:
    print(f"Jev decision error: {e}")
    decision = None

# Second question: insufficient data?
try:
    data_q = jev.noul(
        state=stats,
        instructions=f"Strategy {strategy_id} has only 10 closed trades. "
                     f"Is this sufficient to make a demotion decision?",
        true_criteria="Insufficient data: 10 trades is too few for a statistically "
                     "meaningful decay assessment. Need more trades before demoting.",
        false_criteria="Sufficient data: The performance is clear enough (0.1 win rate, "
                      "negative avg R across all trades) to act on."
    )
    print(f"Jev insufficient-data probability: {data_q:.0%}")
    print(f"Interpretation: {'INSUFFICIENT DATA' if data_q > 0.5 else 'DATA SUFFICIENT'}")
except Exception as e:
    print(f"Jev data question error: {e}")
    data_q = None

print()
print("=" * 60)
print("DECISION SUMMARY")
print("=" * 60)
recommendation = None
if decision is not None:
    if decision > 0.65 and (data_q is None or data_q < 0.5):
        recommendation = "demote"
    elif decision > 0.5:
        recommendation = "demote_with_caveat"
    elif decision > 0.25:
        recommendation = "watch"
    else:
        recommendation = "keep"

print(f"  Strategy: {strategy_id}")
print(f"  Demotion probability: {decision:.0%}" if decision else "  Demotion probability: N/A")
print(f"  Insufficient-data probability: {data_q:.0%}" if data_q else "  Insufficient-data probability: N/A")
print(f"  Recommended action: {recommendation}")