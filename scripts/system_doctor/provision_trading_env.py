#!/usr/bin/env python3
"""
provision_trading_env.py — US-193: provision + verify the canonical HermesForge
trading interpreter.

WHY: cron .sh wrappers resolve their interpreter via resolve_python.sh. The
runtime venv it used to return is re-staged by `hermes update`, which silently
drops manually-installed deps (the exact root cause of the Daily Signal Scanner
streak=29 and the F&G / Paper-Capture failures — a missing parquet engine).

The canonical trading interpreter is a DEDICATED venv OUTSIDE ~/.hermes/installs/
so `hermes update` cannot wipe it. This script installs the full trading dep set
(requirements-trading.txt) into that venv and VERIFIES every import.

Usage:
    python3 provision_trading_env.py                 # provision the canonical venv
    python3 provision_trading_env.py --check         # verify only, no install
    python3 provision_trading_env.py --python PATH   # provision an explicit venv
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import venv
from pathlib import Path

# Canonical interpreter (must match resolve_python.sh's TRADING_VENV).
CANONICAL_VENV = Path("/root/.hermes/venv")  # dedicated Forge trading venv

# The full trading dep set — MUST stay in sync with requirements-trading.txt
# and the FULL_DEPS import list in resolve_python.sh.
FULL_DEPS_IMPORT = "import pandas, numpy, scipy, sklearn, yfinance, mplfinance, pyarrow, yaml, requests"

REQUIREMENTS = Path(__file__).resolve().parent / "requirements-trading.txt"


def _venv_python(venv_dir: Path) -> Path:
    p = venv_dir / "bin" / "python3"
    return p if p.exists() else venv_dir / "bin" / "python"


def _run(cmd: list[str], **kw) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True, **kw)


def create_venv(venv_dir: Path) -> Path:
    """Create the venv if missing; return the venv python path."""
    if not (venv_dir / "bin" / "python3").exists():
        venv.EnvBuilder(with_pip=True).create(str(venv_dir))
    return _venv_python(venv_dir)


def check_deps(python: Path) -> bool:
    r = _run([str(python), "-c", FULL_DEPS_IMPORT])
    return r.returncode == 0


def provision(venv_dir: Path, dry_check: bool = False) -> dict:
    python = create_venv(venv_dir)
    before = check_deps(python)

    if dry_check:
        return {"python": str(python), "before": before, "installed": 0,
                "after": before, "ok": before}

    installed = 0
    if not before:
        r = _run([str(python), "-m", "pip", "install", "--disable-pip-version-check",
                  "-r", str(REQUIREMENTS)])
        if r.returncode != 0:
            print(r.stdout[-2000:], file=sys.stderr)
            print(r.stderr[-2000:], file=sys.stderr)
            return {"python": str(python), "before": before, "installed": -1,
                    "after": False, "ok": False,
                    "error": "pip install failed"}
        # Count what got installed (best effort)
        installed = -1  # unknown exact count; mark as "installed something"
    else:
        installed = 0

    after = check_deps(python)
    return {"python": str(python), "before": before, "installed": installed,
            "after": after, "ok": after}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="verify only, no install")
    ap.add_argument("--python", type=str, default=None,
                    help="explicit venv dir (default: %s)" % CANONICAL_VENV)
    args = ap.parse_args()

    target = Path(args.python) if args.python else CANONICAL_VENV
    result = provision(target, dry_check=args.check)

    python = result["python"]
    print(f"trading interpreter: {python}")
    print(f"deps before: {result['before']}")
    if args.check:
        print(f"deps present (full set): {result['after']}")
    else:
        print(f"install triggered: {not result['before']}")
        print(f"deps after:  {result['after']}")
    print(f"RESULT: {'OK' if result['ok'] else 'FAIL'}")
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())