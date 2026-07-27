#!/usr/bin/env python3
"""
Hand-off contract validator for HermesForge multi-agent task delegation.

Per ADR-005 (Stage-Based Model Floors), every delegate_task call between
HermesForge agents must declare a hand-off contract before the task fires.
This script validates that a contract is well-formed and enforces the
tier floor for the declared stage.

This is NOT a runtime interceptor -- there is no orchestration service in
front of delegate_task to hook into. This script is a hard gate that the
calling agent's own instructions (SOUL.md) require it to run and treat as
blocking before it is allowed to delegate. Skipping the call is an ADR-005
violation, logged as such if caught by Red Team or a governance audit --
but it is not mechanically unskippable. Be honest about this limitation
when reporting on Workstream 2 status.

Usage:
    python3 validate_handoff.py contract.json

Exit code 0 = valid, proceed with delegate_task.
Exit code 1 = invalid, do NOT delegate. Fix the contract or escalate.
"""
import json
import sys
from datetime import datetime, timezone

# Stage -> minimum required tier, per ADR-005 Part A stage vocabulary.
STAGE_TIER_FLOOR = {
    "explore": "T3",
    "draft": "T3",
    "boilerplate": "T4",
    "test-gen": "T3",
    "decide": "T2",
    "synthesize": "T2",
    "commit": "T2",
}

TIER_RANK = {"T4": 0, "T3": 1, "T2": 2}

REQUIRED_FIELDS = ["stage", "tier", "consumes", "produces", "downstream_allowed"]

LOG_PATH = "/root/HermesForge/07-Risk/Governance/handoff_audit_log.jsonl"


def validate(contract: dict) -> list[str]:
    errors = []

    for field in REQUIRED_FIELDS:
        if field not in contract:
            errors.append(f"missing required field: {field}")

    if errors:
        return errors  # can't validate further without required fields

    stage = contract["stage"]
    tier = contract["tier"]

    if stage not in STAGE_TIER_FLOOR:
        errors.append(
            f"unknown stage '{stage}' -- must be one of {list(STAGE_TIER_FLOOR)}"
        )
        return errors

    floor = STAGE_TIER_FLOOR[stage]
    if tier not in TIER_RANK:
        errors.append(f"unknown tier '{tier}' -- must be one of {list(TIER_RANK)}")
        return errors

    if TIER_RANK[tier] < TIER_RANK[floor]:
        errors.append(
            f"tier '{tier}' is below the hard floor for stage '{stage}' "
            f"(floor is '{floor}'). Downgrade is never permitted -- "
            f"per ADR-005 force-escalate rule, only upward changes are allowed."
        )

    if not isinstance(contract["downstream_allowed"], list):
        errors.append("downstream_allowed must be a list of permitted consumers")

    return errors


def log_result(contract: dict, errors: list[str]) -> None:
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "contract": contract,
        "valid": len(errors) == 0,
        "errors": errors,
    }
    with open(LOG_PATH, "a") as f:
        f.write(json.dumps(entry) + "\n")


def main():
    if len(sys.argv) != 2:
        print("usage: validate_handoff.py contract.json", file=sys.stderr)
        sys.exit(1)

    with open(sys.argv[1]) as f:
        contract = json.load(f)

    errors = validate(contract)
    log_result(contract, errors)

    if errors:
        print("HAND-OFF CONTRACT INVALID -- do not delegate:", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        sys.exit(1)

    print(f"OK: stage='{contract['stage']}' tier='{contract['tier']}' -- contract valid")
    sys.exit(0)


if __name__ == "__main__":
    main()
