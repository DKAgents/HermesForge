"""Append-only paper run log. No secrets."""
from datetime import datetime, timezone
from pathlib import Path

LOG = Path("/var/log/hermes-paper.log")

def log_line(source: str, message: str) -> None:
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    line = f"{stamp} {source} {message}\n"
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a") as f:
        f.write(line)
