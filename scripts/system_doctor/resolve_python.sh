#!/usr/bin/env bash
# ============================================================================
# resolve_python.sh — US-163/193: durable interpreter resolution for HermesForge
# cron .sh wrappers.
#
# WHY THIS EXISTS
#   Cron `.sh` wrappers that call bare `python3` resolve to the BARE TOOLS
#   Python, which has NO third-party deps (yaml, requests, pandas, mplfinance,
#   pyarrow, ...). Interpreter drift caused the Daily Signal Scanner (streak=29)
#   and the F&G / Paper-Capture failures: the runtime venv was MISSING pyarrow,
#   so pandas `to_parquet` raised ImportError, and `hermes update` re-staging
#   kept silently wiping manual installs.
#
# US-193 — SINGLE SOURCE-OF-TRUTH INTERPRETER
#   The canonical trading interpreter is the dedicated Forge venv TRADING_VENV,
#   which lives OUTSIDE ~/.hermes/installs/ so `hermes update` cannot re-stage it.
#   Provision it (full dep set incl. pyarrow) with:
#       /root/HermesForge/scripts/system_doctor/provision_trading_env.py
#   The full dep set is pinned in requirements-trading.txt; the import probe below
#   MUST stay in sync with it.
#
# CONVENTION
#   Never invoke bare `python3` from a HermesForge cron wrapper. Instead:
#       PYTHONBIN="$(/root/HermesForge/scripts/system_doctor/resolve_python.sh)"
#       "$PYTHONBIN" /root/HermesForge/scripts/.../foo.py "$@"
#
# RESOLUTION ORDER (first hit wins; every candidate is VERIFIED against the
# FULL trading dep set, so a silently-stripped env is skipped, never trusted):
#   1. $PYTHONBIN env override (caller pins it explicitly; must be executable)
#   2. TRADING_VENV — canonical durable Forge trading venv (full set)
#   3. facts.json venv (the runtime's current env) — full set
#   4. newest environments/*/venv that imports the full set
#
# The resolver itself depends on NOTHING (bash + find/sed), so it cannot be
# broken by the very dependency rot it exists to route around.
# ============================================================================
set -euo pipefail

INSTALL_ROOT="/root/.hermes/installs"
TRADING_VENV="/root/.hermes/venv"   # canonical durable Forge trading interpreter (US-193)

# Full trading dep set — MUST match requirements-trading.txt.
FULL_DEPS='import pandas, numpy, scipy, sklearn, yfinance, mplfinance, pyarrow, yaml, requests'

full_deps_ok() {
    [[ -x "$1" ]] && "$1" -c "$FULL_DEPS" >/dev/null 2>&1
}

# 1. Explicit caller override.
if [[ -n "${PYTHONBIN:-}" ]]; then
  if [[ -x "$PYTHONBIN" ]]; then
    printf '%s\n' "$PYTHONBIN"
    exit 0
  fi
  echo "resolve_python.sh: PYTHONBIN='$PYTHONBIN' is not executable" >&2
  exit 1
fi

# 2. Canonical durable Forge trading venv (US-193 — authoritative).
if full_deps_ok "$TRADING_VENV/bin/python3"; then
    printf '%s\n' "$TRADING_VENV/bin/python3"
    exit 0
fi

# 3. Current dependency-complete venv (authoritative fallback) from facts.json.
for facts in "$INSTALL_ROOT"/*/facts.json; do
  [[ -f "$facts" ]] || continue
  envpath="$(sed -n 's/.*"environment"[[:space:]]*:[[:space:]]*"\\([^\"]*\\)".*/\\1/p' "$facts")"
  if [[ -n "$envpath" ]] && full_deps_ok "$envpath/bin/python3"; then
    printf '%s\n' "$envpath/bin/python3"
    exit 0
  fi
done

# 4. Newest environments/*/venv/bin/python3 that imports the full trading set.
found=""
while IFS= read -r p; do
  if full_deps_ok "$p"; then
    found="$p"
    break
  fi
done < <(find "$INSTALL_ROOT" -path '*/venv/bin/python3' -type f -printf '%T@ %p\n' 2>/dev/null \
          | sort -rn | cut -d' ' -f2-)

if [[ -n "$found" ]]; then
  printf '%s\n' "$found"
  exit 0
fi

echo "resolve_python.sh: no dependency-complete venv python (full trading set) found; run provision_trading_env.py" >&2
exit 1