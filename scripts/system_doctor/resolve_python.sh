#!/usr/bin/env bash
# ============================================================================
# resolve_python.sh — US-163 step 1: durable interpreter resolution for
# HermesForge cron .sh wrappers.
#
# WHY THIS EXISTS
#   Cron `.sh` wrappers that call bare `python3` resolve to the BARE TOOLS
#   Python (/root/.hermes/tools/python-3.14.x), which has NO third-party deps
#   (yaml, requests, mplfinance, discord, ...). This is the exact failure mode
#   that broke `discover_connections` (yaml) and the Daily Signal Scanner
#   (mplfinance), and that `hermes update` re-triggers by re-staging the
#   interpreter and wiping manual installs.
#
# CONVENTION
#   Never invoke bare `python3` from a HermesForge cron wrapper. Instead:
#       PYTHONBIN="$(/root/HermesForge/scripts/system_doctor/resolve_python.sh)"
#       "$PYTHONBIN" /root/HermesForge/scripts/system_doctor/collector.py "$@"
#
# RESOLUTION ORDER (first hit wins)
#   1. $PYTHONBIN env override (caller pins it explicitly; must be executable)
#   2. The runtime's CURRENT dependency-complete venv, read from the install's
#      facts.json (`packages.venv.environment`), which `hermes update` keeps
#      pointed at the live environment. This survives re-staging.
#   3. Newest-match fallback: any `environments/*/venv/bin/python3` that can
#      actually `import yaml, requests` (dependency-complete verification).
#
# This resolver itself depends on NOTHING (bash + find/sed), so it cannot be
# broken by the very dependency rot it exists to route around.
# ============================================================================
set -euo pipefail

INSTALL_ROOT="/root/.hermes/installs"

# 1. Explicit caller override.
if [[ -n "${PYTHONBIN:-}" ]]; then
  if [[ -x "$PYTHONBIN" ]]; then
    printf '%s\n' "$PYTHONBIN"
    exit 0
  fi
  echo "resolve_python.sh: PYTHONBIN='$PYTHONBIN' is not executable" >&2
  exit 1
fi

# 2. Current dependency-complete venv (authoritative) from facts.json.
for facts in "$INSTALL_ROOT"/*/facts.json; do
  [[ -f "$facts" ]] || continue
  envpath="$(sed -n 's/.*"environment"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' "$facts")"
  if [[ -n "$envpath" && -x "$envpath/bin/python3" ]]; then
    printf '%s\n' "$envpath/bin/python3"
    exit 0
  fi
done

# 3. Fallback: newest `venv/bin/python3` that can import yaml + requests.
found=""
while IFS= read -r p; do
  if [[ -x "$p" ]] && "$p" -c 'import yaml, requests' >/dev/null 2>&1; then
    found="$p"
    break
  fi
done < <(find "$INSTALL_ROOT" -path '*/venv/bin/python3' -type f -printf '%T@ %p\n' 2>/dev/null \
          | sort -rn | cut -d' ' -f2-)

if [[ -n "$found" ]]; then
  printf '%s\n' "$found"
  exit 0
fi

echo "resolve_python.sh: no dependency-complete venv python found under $INSTALL_ROOT" >&2
exit 1