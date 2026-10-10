#!/usr/bin/env python3
"""
jev_cron_triage.py — US-156: JEV-powered cron output triage

Classifies cron job output as OK / WARN / CRITICAL using JEV System One.
Reduces T3 token spend by only escalating CRITICAL outputs to the LLM agent.

Usage:
    python3 jev_cron_triage.py --input <file|-> [--cron-name NAME]
    
    Reads cron output from file or stdin, classifies it, prints JSON result.
    
Exit codes:
    0 = OK (no escalation needed)
    1 = WARN (summary may be useful)
    2 = CRITICAL (full agent escalation required)
"""

import sys
import os
import json
import argparse
from pathlib import Path

# ── Load JEV API key ──────────────────────────────────────────────────────
def _load_api_key() -> str:
    """Load TYPESAFE_API_KEY from ~/.hermes/.env"""
    env_path = Path.home() / ".hermes" / ".env"
    if not env_path.exists():
        return os.environ.get("TYPESAFE_API_KEY", "")
    
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if line.startswith("TYPESAFE_API_KEY="):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    return os.environ.get("TYPESAFE_API_KEY", "")


# ── JEV classification ────────────────────────────────────────────────────
def _classify_with_jev(output_text: str, cron_name: str = "", api_key: str = "") -> dict:
    """Use JEV to classify cron output severity."""
    sys.path.insert(0, str(Path("/root/HermesForge/scripts/gauntlet")))
    from jev_client import JevClient
    
    jev = JevClient(api_key=api_key)
    
    # Truncate output to reasonable context window for JEV
    context = output_text[:4000] if len(output_text) > 4000 else output_text
    
    prompt = f"""Cron job{f' {cron_name}' if cron_name else ''} output:

{context}

Classify this output as:
- ok: normal, healthy, no issues. Routine completion.
- warn: minor issues, warnings, data staleness, non-critical errors
- critical: failures, crashes, missing data, broken pipeline, requires immediate attention"""

    try:
        result = jev.choice(prompt, "classification", {
            "ok": "routine",
            "warn": "attention", 
            "critical": "escalate"
        })
        return {
            "classification": result.get("choice", "warn"),
            "confidence": round(result.get("confidence", 0), 4),
            "error": None
        }
    except Exception as e:
        # Fail-open: if JEV is down, classify as WARN (let agent decide)
        return {
            "classification": "warn",
            "confidence": 0,
            "error": str(e)[:200]
        }


def triage(output_text: str, cron_name: str = "") -> dict:
    """Main triage function. Returns classification dict."""
    api_key = _load_api_key()
    if not api_key:
        return {
            "classification": "warn",
            "confidence": 0,
            "error": "TYPESAFE_API_KEY not found"
        }
    
    result = _classify_with_jev(output_text, cron_name, api_key)
    return result


def main():
    parser = argparse.ArgumentParser(description="JEV Cron Output Triage")
    parser.add_argument("--input", help="File to read (default: stdin)", default="-")
    parser.add_argument("--cron-name", help="Cron job name for context", default="")
    parser.add_argument("--json", action="store_true", help="Output JSON only")
    args = parser.parse_args()
    
    # Read input
    if args.input == "-":
        output_text = sys.stdin.read()
    else:
        output_text = Path(args.input).read_text()
    
    if not output_text.strip():
        result = {"classification": "ok", "confidence": 1.0, "error": None}
    else:
        result = triage(output_text, args.cron_name)
    
    if args.json:
        print(json.dumps(result))
    else:
        classification = result["classification"]
        icon = {"ok": "✅", "warn": "⚠️", "critical": "🔴"}.get(classification, "❓")
        print(f"{icon} CRON TRIAGE: {classification.upper()} (conf={result['confidence']:.0%})")
        if result.get("error"):
            print(f"   JEV error: {result['error']}")
    
    # Exit code for shell integration
    exit_codes = {"ok": 0, "warn": 1, "critical": 2}
    sys.exit(exit_codes.get(classification, 1))


if __name__ == "__main__":
    main()