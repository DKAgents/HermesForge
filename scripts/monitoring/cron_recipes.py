#!/usr/bin/env python3
"""
cron_recipes.py — Reusable monitoring templates for HermesForge.

Each recipe is a self-contained prompt + schedule + toolset config
that can be used with `hermes cron create` or the cronjob tool.

Usage:
    from cron_recipes import RECIPES
    # Create a liquidation cascade monitor
    recipe = RECIPES["liquidation_cascade"]
    cronjob(action="create", schedule=recipe["schedule"], prompt=recipe["prompt"], ...)
"""

RECIPES = {
    "liquidation_cascade": {
        "name": "Liquidation Cascade Monitor",
        "schedule": "*/2 * * * *",  # every 2 minutes
        "enabled_toolsets": ["terminal", "messaging"],
        "prompt": """You are a HermesForge liquidation cascade monitor. Execute:

cd /root/HermesForge && python3 scripts/monitoring/check_liquidations.py

If the script outputs [SILENT], respond with exactly "[SILENT]".
If the script outputs alert data, format it as a Discord alert and send it
to target "discord:1528555885310513213" with:
- 🔴 LIQUIDATION CASCADE DETECTED
- Coin, direction (longs/shorts liquidated), total size
- Number of liquidations in the window
- Current price and funding rate
- Any open paper trades affected
""",
    },
    "funding_rate_extreme": {
        "name": "Funding Rate Extreme Monitor",
        "schedule": "0 */1 * * *",  # every hour
        "enabled_toolsets": ["terminal", "messaging"],
        "prompt": """You are a HermesForge funding rate monitor. Execute:

cd /root/HermesForge && python3 scripts/monitoring/check_funding_extremes.py

If the script outputs [SILENT], respond with exactly "[SILENT]".
If the script outputs alert data, format it as a Discord alert and send it
to target "discord:1528555885310513213" with:
- ⚠️ FUNDING RATE EXTREME
- Coin, current rate, 30d percentile, direction of risk
- Suggested action (suppress longs/shorts for this coin)
""",
    },
    "oi_spike": {
        "name": "OI Spike Monitor",
        "schedule": "*/15 * * * *",  # every 15 minutes
        "enabled_toolsets": ["terminal", "messaging"],
        "prompt": """You are a HermesForge OI spike monitor. Execute:

cd /root/HermesForge && python3 scripts/monitoring/check_oi_spikes.py

If the script outputs [SILENT], respond with exactly "[SILENT]".
If the script outputs alert data, format it as a Discord alert and send it
to target "discord:1528555885310513213" with:
- 📊 OI SPIKE DETECTED
- Coin, % change, direction (increase/decrease), absolute change in USD
- Current OI and price
- Interpretation (new money entering vs unwinding)
""",
    },
    "daily_confidence_adjustment": {
        "name": "Daily Confidence Adjustment (Pre-Market)",
        "schedule": "30 13 * * 1-5",  # 13:30 UTC weekdays (before US open)
        "enabled_toolsets": ["terminal", "file"],
        "prompt": """You are a HermesForge confidence adjustment agent. Execute:

cd /root/HermesForge && python3 scripts/monitoring/compute_confidence_adjustments.py

This script checks overnight liquidation events, funding rate extremes, and
OI changes, then outputs a JSON file with confidence multipliers for each
strategy. Review the output and post a summary to Discord target "origin"
with:
- Overnight liquidation summary (if any)
- Funding rate regime (neutral/extreme)
- OI trend (building/unwinding)
- Recommended confidence adjustments for today's signal scan
""",
    },
}

if __name__ == "__main__":
    import json
    print(json.dumps({k: {"name": v["name"], "schedule": v["schedule"]} 
                      for k, v in RECIPES.items()}, indent=2))
