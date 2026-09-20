#!/usr/bin/env python3
"""
Polymarket macro feed — query key prediction markets, output JSON for briefing pipeline.
Read-only, no auth required. Run daily via cron or ad-hoc.

Output: scripts/gauntlet/polymarket_macro.json
"""
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path("/root/HermesForge")
OUTPUT_PATH = PROJECT_ROOT / "scripts" / "gauntlet" / "polymarket_macro.json"
POLYMARKET_SCRIPT = Path("/root/.hermes/skills/research/polymarket/scripts/polymarket.py")

# Markets to track — search queries that map to relevant events
SEARCHES = [
    ("fed-rate-cut", "Federal Reserve rate cut"),
    ("recession-2026", "Recession 2026"),
    ("cpi-inflation", "CPI inflation"),
    ("s&p-500", "S&P 500 price"),
    ("bitcoin-price", "Bitcoin price"),
    ("oil-price", "Oil price"),
    ("treasury-yield", "Treasury yield"),
]

def search_market(query: str, label: str) -> dict:
    """Search Polymarket and extract top market probabilities."""
    try:
        result = subprocess.run(
            ["python3", str(POLYMARKET_SCRIPT), "search", query],
            capture_output=True, text=True, timeout=15
        )
        if result.returncode != 0:
            return {"label": label, "error": "search failed"}

        output = result.stdout

        # Parse the human-readable output
        markets = []
        current_market = None

        for line in output.split('\n'):
            line = line.strip()
            if not line:
                continue

            # Match: "=== Market Name ===" or "=== slug ==="
            if line.startswith("===") and line.endswith("==="):
                if "slug:" in line:
                    continue
                name = line.strip("= ").strip()
                if current_market:
                    markets.append(current_market)
                current_market = {"name": name, "yes_pct": None, "no_pct": None, "volume": None}
                continue

            # Match: "Yes: X.X% / No: Y.Y%  |  Volume: $Z.ZM"
            if "Yes:" in line and "No:" in line and current_market:
                parts = line.split("|")
                prob_part = parts[0].strip() if parts else ""
                vol_part = parts[1].strip() if len(parts) > 1 else ""

                # Parse Yes/No
                yes_match = prob_part.split("Yes:")[1].split("/")[0].strip() if "Yes:" in prob_part else None
                no_match = prob_part.split("No:")[1].split("%")[0].strip() if "No:" in prob_part else None
                if yes_match:
                    try:
                        current_market["yes_pct"] = float(yes_match.replace("%", ""))
                    except ValueError:
                        pass
                if no_match:
                    try:
                        current_market["no_pct"] = float(no_match.replace("%", ""))
                    except ValueError:
                        pass

                # Parse volume
                if "Volume:" in vol_part:
                    vol_str = vol_part.split("Volume:")[1].strip().replace("$", "").replace(",", "")
                    if vol_str.endswith("M"):
                        try:
                            current_market["volume"] = float(vol_str[:-1]) * 1_000_000
                        except ValueError:
                            pass
                    elif vol_str.endswith("K"):
                        try:
                            current_market["volume"] = float(vol_str[:-1]) * 1_000
                        except ValueError:
                            pass
                    elif vol_str:
                        try:
                            current_market["volume"] = float(vol_str)
                        except ValueError:
                            pass

        if current_market:
            markets.append(current_market)

        # Keep only markets with probabilities
        valid = [m for m in markets if m.get("yes_pct") is not None]
        return {"label": label, "markets": valid[:5], "count": len(valid)}

    except Exception as e:
        return {"label": label, "error": str(e)}

def main():
    results = []
    for query, label in SEARCHES:
        print(f"  Querying: {label}...")
        r = search_market(query, label)
        results.append(r)
        if "markets" in r:
            for m in r["markets"]:
                print(f"    {m['name'][:60]}: {m['yes_pct']}%")

    # Build output
    output = {
        "updated": datetime.now(timezone.utc).isoformat(),
        "markets": results,
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(output, indent=2))
    print(f"\n  ✅ Written: {OUTPUT_PATH}")

    # Print summary for cron delivery
    print("\n=== MACRO SNAPSHOT ===")
    for r in results:
        if "error" in r:
            print(f"  {r['label']}: ERROR — {r['error']}")
        elif not r.get("markets"):
            print(f"  {r['label']}: no markets found")
        else:
            top = r["markets"][0]
            print(f"  {r['label']}: {top['name'][:50]} — {top['yes_pct']}%")

if __name__ == "__main__":
    main()