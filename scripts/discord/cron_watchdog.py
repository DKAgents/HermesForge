#!/usr/bin/env python3
"""cron_watchdog.py — Silent health check. Webhook alert ONLY on failure."""
import json, os, time, pathlib, subprocess, datetime

# Load env
env_file = os.path.expanduser("~/.hermes/.env")
with open(env_file) as ef:
    for line in ef:
        line = line.strip()
        if "=" in line and not line.startswith("#"):
            k, _, v = line.partition("=")
            os.environ[k.strip()] = v.strip().strip('"').strip("'")

WEBHOOK = os.environ.get("CROSSPOST_WEBHOOK_1532020053548208328", "")
if not WEBHOOK:
    exit(0)

def alert(msg):
    """Post a one-line Discord alert via webhook."""
    payload = json.dumps({"content": msg})
    subprocess.run([
        "curl", "-s", "-X", "POST",
        "-H", "Content-Type: application/json",
        "-d", payload,
        WEBHOOK
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=10)

errors = []

# 1. Check jobs.json for error status
jobs_file = os.path.expanduser("~/.hermes/cron/jobs.json")
try:
    with open(jobs_file) as jf:
        jobs = json.load(jf)
    for j in jobs.get("jobs", []):
        if j.get("last_status") == "error" and j.get("failure_streak", 0) > 0:
            name = j.get("name", j.get("id", "?"))
            streak = j.get("failure_streak", 0)
            errors.append(f"{name} (streak {streak})")
except Exception as e:
    alert(f"Watchdog: Cannot read jobs.json ({e})")
    exit(1)

# 2. STR-Q sweep freshness (< 20 min)
sweep_dir = os.path.expanduser("~/.hermes/cron/output/b9fb0afb1e29")
try:
    files = sorted(pathlib.Path(sweep_dir).glob("*.md"))
    if not files:
        errors.append("STR-Q sweep: NO output files")
    else:
        age = time.time() - files[-1].stat().st_mtime
        if age > 1200:
            errors.append(f"STR-Q sweep: stale ({int(age/60)} min)")
except FileNotFoundError:
    errors.append("STR-Q sweep: output directory missing")

# 3. Daily Signal Scanner ran today? (check after 15:00 UTC)
now = datetime.datetime.utcnow()
if now.hour >= 15:
    scan_dir = os.path.expanduser("~/.hermes/cron/output/3f49a07a2f04")
    today = now.strftime("%Y-%m-%d")
    found = list(pathlib.Path(scan_dir).glob(f"{today}*.md"))
    if not found:
        errors.append("Daily Signal Scanner: not run today")

# Report only if there are issues
if errors:
    msg = "**Watchdog Alert**" + chr(10)
    for e in errors:
        msg += "- " + e + chr(10)
    alert(msg)

exit(0)
