#!/usr/bin/env python3
"""
Wrapper for x-strategy-scout cron: runs scout, outputs summary for delivery.
US-146: reads Edge Discovery candidate URLs for prioritized deep-read.
"""
import subprocess, sys, os
from pathlib import Path

PROJECT_ROOT = Path("/root/HermesForge")

# Ensure nvm/node binaries are on PATH for xurl
_nvm_bin = Path.home() / ".nvm" / "versions" / "node"
if _nvm_bin.exists():
    for _v in sorted(_nvm_bin.iterdir(), reverse=True):
        _bin_dir = _v / "bin"
        if _bin_dir.is_dir():
            os.environ["PATH"] = str(_bin_dir) + ":" + os.environ.get("PATH", "")
            break
CANDIDATES_FILE = PROJECT_ROOT / "code" / "forge-loop" / "edge-discovery-candidates.txt"

# Build command with optional priority URLs from Edge Discovery
cmd = [
    "python3", "scripts/validation/scout_x_strategies.py",
    "--max-candidates", "5",
    "--threshold", "35",
]

if CANDIDATES_FILE.exists():
    cmd.append(f"--priority-file={CANDIDATES_FILE}")
    print(f"📎 Reading Edge Discovery candidates from {CANDIDATES_FILE}")

result = subprocess.run(cmd, cwd=str(PROJECT_ROOT), capture_output=True, text=True, timeout=180)

# Print the scout output
print(result.stdout)
if result.stderr:
    print(result.stderr, file=sys.stderr)

# Check for generated HYP notes
hyp_dir = PROJECT_ROOT / "trading/strategies" / "Hypotheses"
new_hyps = sorted(hyp_dir.glob("STR-*.md"), key=lambda p: p.stat().st_mtime, reverse=True)[:3]
if new_hyps:
    print("\n📁 New HYP notes:")
    for h in new_hyps:
        print(f"  {h.name}")

# Clean up consumed candidate file
if CANDIDATES_FILE.exists():
    CANDIDATES_FILE.unlink()
    print(f"\n🧹 Consumed {CANDIDATES_FILE}")

sys.exit(result.returncode)