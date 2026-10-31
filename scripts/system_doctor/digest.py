#!/usr/bin/env python3
"""system_doctor/digest.py — US-161 confidence digest renderer.

Renders the Section 3.2 digest template to stdout from the shared findings
queue (findings.jsonl) + scan state (findings.state.json). This is the
MECHANICAL renderer only — it does not post to Discord, does not decide what
is an issue (thresholds did that), and does not auto-fix. Delivery + T3
synthesis belong to the orchestrator/cron layer (out of scope).

Fail-closed (5.2): if findings.state.json is missing or stale (older than
STALE_WINDOW), it reports "doctor did not complete" — never "0 findings".

Stdlib only: json, pathlib, datetime, hashlib, tempfile, sys.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

HF_ROOT = Path(os.environ.get("HERMESFORGE_ROOT", "/root/HermesForge"))
CACHE_DIR = Path(os.environ.get("SYSTEM_DOCTOR_CACHE", f"{HF_ROOT}/cache/system-doctor"))
FINDINGS_JSONL = CACHE_DIR / "findings.jsonl"
STATE_JSON = CACHE_DIR / "findings.state.json"
DIGEST_STATE_JSON = CACHE_DIR / "digest.state.json"

STALE_WINDOW = timedelta(hours=24)  # doctor runs at 06:00; digest at 07:00

CATEGORY_LABEL = {
    "cron_error": "cron error logs",
    "data_freshness": "data freshness",
    "model_staleness": "model staleness",
    "cost_drift": "cost drift",
    "disk_ssh_security": "disk/ssh/security posture",
    "upstream_git": "upstream git",
    "doctor_self": "doctor self-monitoring",
}


def _iso_parse(ts):
    if not ts:
        return None
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return None


def load_findings() -> list[dict]:
    if not FINDINGS_JSONL.exists():
        return []
    out = []
    for line in FINDINGS_JSONL.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return out


def load_state() -> dict | None:
    if not STATE_JSON.exists():
        return None
    try:
        return json.loads(STATE_JSON.read_text())
    except json.JSONDecodeError:
        return None


# --------------------------------------------------------------------------
# Digest suppression (US-161 D2 / "[SILENT]") — change detection over open
# findings. The snapshot captures exactly the four change triggers the spec
# defines: new open, newly resolved, new Tier-2, doctor_self verdict change.
# Count/evidence/timestamp drift is deliberately NOT a trigger, so the digest
# stays silent between genuinely new events.
# --------------------------------------------------------------------------
def _open_snapshot(findings: list[dict]) -> list[dict]:
    """Canonical, order-stable snapshot of open findings for comparison."""
    entries = []
    for f in findings:
        if f.get("status") != "open":
            continue
        e = {
            "id": f.get("id"),
            "status": f.get("status"),
            "risk_tier": f.get("risk_tier"),
            "category": f.get("category"),
        }
        if f.get("category") == "doctor_self":
            # doctor_self "verdict" == its summary text; capture it so a
            # same-id verdict change is still detected.
            e["summary"] = f.get("summary")
        entries.append(e)
    entries.sort(key=lambda x: (str(x.get("id")) or ""))
    return entries


def _snapshot_signature(entries: list[dict]) -> str:
    payload = json.dumps(entries, sort_keys=True, separators=(",", ":"),
                         ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def load_digest_state() -> dict | None:
    if not DIGEST_STATE_JSON.exists():
        return None
    try:
        return json.loads(DIGEST_STATE_JSON.read_text())
    except json.JSONDecodeError:
        return None


def write_digest_state(entries: list[dict]) -> None:
    """Persist the last-digested snapshot (atomic write convention)."""
    obj = {
        "last_digest_ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "signature": _snapshot_signature(entries),
        "open_findings": entries,
    }
    DIGEST_STATE_JSON.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(DIGEST_STATE_JSON.parent), suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as fh:
            json.dump(obj, fh, ensure_ascii=False, indent=2)
        os.replace(tmp, DIGEST_STATE_JSON)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def render() -> str:
    now = datetime.now(timezone.utc)
    stamp = now.strftime("%Y-%m-%d %H:%M UTC")

    state = load_state()
    last_scan = _iso_parse(state.get("last_full_scan_ts")) if state else None

    # Fail-closed: stale or absent state -> "doctor did not complete".
    if state is None:
        return _fail("findings.state.json absent (doctor never ran on schedule)")
    if last_scan is None:
        return _fail("findings.state.json has no last_full_scan_ts")
    if (now - last_scan) > STALE_WINDOW:
        return _fail(
            f"doctor did not complete — last scan {last_scan.isoformat()} older "
            f"than {int(STALE_WINDOW.total_seconds() // 3600)}h")

    findings = load_findings()
    open_ = [f for f in findings if f.get("status") == "open"]
    tier2 = [f for f in open_ if f.get("risk_tier") == 2]
    tier1 = [f for f in open_ if f.get("risk_tier") == 1]

    not_inspected = []
    for cat, info in (state.get("categories") or {}).items():
        if info.get("verdict") in ("not_inspected", "error"):
            not_inspected.append((cat, info.get("verdict"), info.get("last_verdict_ts")))

    resolved = len([f for f in findings if f.get("status") == "resolved"])
    n_open = len(open_)

    lines: list[str] = []
    lines.append(f"**🩺 System Doctor — Confidence Digest** · {stamp}")
    lines.append("")

    # Auto-fixed — always rendered at 0 with the Phase-2 parenthetical.
    lines.append("**Auto-fixed:** 0")
    lines.append("_(none — fix layer (Phase 2) is not enabled yet; this is the expected value)_")
    lines.append("")

    # Need sign-off (Tier 2).
    lines.append(f"**Need sign-off (Tier 2):** {len(tier2)}")
    if tier2:
        for f in tier2:
            lines.append(f"• {f.get('summary','')} — why: {_why(f)}; deferral "
                         f"consequence: {_consequence(f)}.")
            lines.append(f"  _(human-gated: {CATEGORY_LABEL.get(f.get('category'), f.get('category'))})_")
    else:
        lines.append("_(none)_")
    lines.append("")

    # Tier 1 findings (queued, not acted).
    lines.append(f"**Tier 1 findings (queued, not acted):** {len(tier1)}")
    if tier1:
        for f in tier1:
            lines.append(f"• {f.get('summary','')} — why: {_why(f)}; consequence: "
                         f"{_consequence(f)}.")
    else:
        lines.append("_(none)_")
    lines.append("")

    # Trading-boundary anomalies — always zero by construction.
    lines.append("**Trading-boundary anomalies:** 0")
    lines.append("_(kill-switch, size-cap, secrets, LIVE_TRADING_ENABLED: no change, no touch)_")
    lines.append("")

    # NOT inspected — mandatory, non-empty when any category lacks a verdict.
    lines.append("**NOT inspected this cycle:**")
    if not_inspected:
        for cat, verdict, ts in not_inspected:
            lines.append(f"• {cat}: {CATEGORY_LABEL.get(cat, cat)} — {verdict} (no verdict)")
    else:
        lines.append("_(all six categories returned clean/finding this cycle)_")
    lines.append("")

    lines.append(f"**Queue:** {FINDINGS_JSONL} — {n_open} open · {resolved} resolved")
    return "\n".join(lines)


def _fail(reason: str) -> str:
    return (
        f"**🩺 System Doctor — Confidence Digest** · "
        f"{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}\n\n"
        f"⚠️ **doctor did not complete** — {reason}.\n"
        f"_(fail-closed: refusing to render '0 findings' from a stale/absent scan)_"
    )


def _why(f: dict) -> str:
    return (f.get("evidence") or {}).get("detail", "") or f.get("summary", "")


def _consequence(f: dict) -> str:
    cat = f.get("category", "")
    return {
        "cron_error": "missed scheduled output / silent data gap",
        "disk_ssh_security": "unchanged exposure / degraded posture",
        "upstream_git": "uncommitted work drifts from main",
        "data_freshness": "stale market inputs",
        "model_staleness": "retired/routed model continues to fire",
        "cost_drift": "spend may exceed cap",
        "doctor_self": "doctor blind spot persists (silent false-clean risk)",
    }.get(cat, "condition persists")


def main() -> int:
    # Fail-closed: absent/stale scan state always renders (never suppressed) —
    # "doctor did not complete" must fire every cycle until it recovers.
    state = load_state()
    last_scan = _iso_parse(state.get("last_full_scan_ts")) if state else None
    if (state is None or last_scan is None
            or (datetime.now(timezone.utc) - last_scan) > STALE_WINDOW):
        print(render())
        return 0

    # Suppression gate: identical open-findings snapshot since last digest
    # -> [SILENT] emit nothing and do NOT update state.
    findings = load_findings()
    snapshot = _open_snapshot(findings)
    signature = _snapshot_signature(snapshot)
    prev = load_digest_state()
    if prev and prev.get("signature") == signature:
        return 0

    # Change (or first run): render AND persist the new snapshot.
    print(render())
    write_digest_state(snapshot)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())