#!/usr/bin/env python3
"""Wrapper for x-strategy-scout cron: runs scout, outputs summary for delivery."""
import subprocess, sys
from pathlib import Path

result = subprocess.run(
    ["python3", "scripts/validation/scout_x_strategies.py", "--max-candidates", "5", "--threshold", "35"],
    cwd="/root/HermesForge",
    capture_output=True, text=True, timeout=180
)

# Print the scout output
print(result.stdout)
if result.stderr:
    print(result.stderr, file=sys.stderr)

# Check for generated HYP notes
hyp_dir = Path("/root/HermesForge/06-Strategies/Hypotheses")
new_hyps = sorted(hyp_dir.glob("STR-*.md"), key=lambda p: p.stat().st_mtime, reverse=True)[:3]
if new_hyps:
    print("\n📁 New HYP notes:")
    for h in new_hyps:
        print(f"  {h.name}")

sys.exit(result.returncode)