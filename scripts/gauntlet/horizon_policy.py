"""horizon_policy.py — US-204 (EPIC-017 Phase 2) horizon-preference intake gate.

Prefer 4h–7d holding horizons. Intraday 5m seeds (holding/exit window <= 5
minutes — a pure scalp) are gated: they must carry an explicit argument that the
gross edge clears 4x the all-in taker cost, OR a maker-only execution plan;
otherwise they are REJECTED pre-G0.

The ``horizon`` field is the holding/exit window (US-202 spec 1.1, distinct from
``timeframe``, the signal bar). A seed is a "5m seed" when its horizon resolves
to a maximum holding time of <= 5 minutes.

The 4x-taker hurdle is derived from the single venue-cost authority
(``fee_source.get_round_trip_bps("crypto")`` = taker*2 + slippage + funding),
so the gate can never diverge from the G0 cost model (ADR-009).
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple

# fee_source lives in the same directory (scripts/gauntlet). Fail-closed on the
# import so the module still loads where fee_source is absent.
try:
    import fee_source as _fee_source
except ImportError:  # pragma: no cover
    _fee_source = None

# Minutes per unit for horizon parsing.
_UNIT_MIN = {"m": 1, "h": 60, "d": 1440, "w": 10080}

# Preferred holding band (inclusive), minutes.
PREFERRED_MIN_MINUTES = 4 * 60          # 4h
PREFERRED_MAX_MINUTES = 7 * 24 * 60     # 7d


def _split(horizon: str) -> List[str]:
    return [p for p in re.split(r"[\s\-–—/]+", (horizon or "").strip().lower())
            if p]


def _implied_unit(parts: List[str]) -> str:
    """Unit for unitless tokens (e.g. ``"1"`` in ``"1-7d"`` inherits ``d``)."""
    for suffix in ("d", "h", "w"):
        for p in parts:
            if p.endswith(suffix):
                return suffix
    return "m"


def parse_horizon_max_minutes(horizon: Optional[str]) -> Optional[int]:
    """Return the maximum holding time in minutes, or None if unparseable.

    Examples: ``"5m"`` -> 5, ``"1-5d"`` -> 7200, ``"4-48h"`` -> 2880,
    ``"5m-4h"`` -> 240, ``"daily"`` -> None.
    """
    if not isinstance(horizon, str):
        return None
    parts = _split(horizon)
    if not parts:
        return None
    implicit = _implied_unit(parts)
    max_min: Optional[int] = None
    for p in parts:
        m = re.fullmatch(r"(\d+(?:\.\d+)?)(m|h|d|w)?", p)
        if not m:
            return None
        num = float(m.group(1))
        unit = m.group(2) or implicit
        if unit not in _UNIT_MIN:
            return None
        mins = int(round(num * _UNIT_MIN[unit]))
        max_min = mins if max_min is None else max(max_min, mins)
    return max_min


def is_5m_seed(horizon: Optional[str]) -> bool:
    """True if the horizon is a <=5-minute (scalp) holding window."""
    mx = parse_horizon_max_minutes(horizon)
    return mx is not None and mx <= 5


def horizon_tag(horizon: Optional[str]) -> str:
    """Tag a horizon: ``fast`` (<=5m) / ``preferred`` (4h–7d) / ``other``."""
    mx = parse_horizon_max_minutes(horizon)
    if mx is None:
        return "other"
    if mx <= 5:
        return "fast"
    if PREFERRED_MIN_MINUTES <= mx <= PREFERRED_MAX_MINUTES:
        return "preferred"  # 4h..7d preferred band
    return "other"


def four_x_taker_hurdle_bps() -> float:
    """4x the all-in taker round-trip cost (bps) — the 5m gross-edge hurdle."""
    if _fee_source is not None:
        return 4.0 * _fee_source.get_round_trip_bps("crypto")
    return 4.0 * 11.5  # fail-closed static: 4.5*2 taker + 2.5 slip + 0.5 funding


def validate_horizon(entry: Dict[str, Any],
                     hurdle_bps: Optional[float] = None) -> Tuple[bool, List[str]]:
    """US-204 horizon gate.

    Returns ``(ok, errors)``:
      * non-5m seeds admit (``ok=True``, no errors) — horizon is merely tagged,
      * 5m seeds with ``execution_mode == "maker"`` admit (maker-only plan),
      * 5m taker seeds admit ONLY if ``expected_gross_edge_bps >= hurdle`` AND a
        non-empty ``fast_horizon_argument`` is present,
      * otherwise reject with a per-condition reason (pre-G0).
    """
    horizon = entry.get("horizon")
    if not is_5m_seed(horizon):
        return (True, [])

    errors: List[str] = []
    mode = entry.get("execution_mode")
    if mode == "maker":
        return (True, [])  # maker-only execution plan satisfies the gate

    # taker 5m seed: require an explicit gross-edge-clears-4x-taker-cost argument
    edge = entry.get("expected_gross_edge_bps")
    arg = (entry.get("fast_horizon_argument") or "").strip()

    if hurdle_bps is None:
        hurdle_bps = four_x_taker_hurdle_bps()

    if not arg:
        errors.append(
            "5m taker seed requires an explicit argument that gross edge clears "
            "4x all-in taker cost (set 'fast_horizon_argument')"
        )
    if not (isinstance(edge, (int, float)) and not isinstance(edge, bool)
            and edge >= hurdle_bps):
        errors.append(
            f"5m taker seed expected_gross_edge_bps {edge!r} < 4x taker cost "
            f"hurdle {hurdle_bps:.1f} bps"
        )
    return (len(errors) == 0, errors)


if __name__ == "__main__":
    samples = [
        {"horizon": "4h-48h", "execution_mode": "taker",
         "expected_gross_edge_bps": 15},
        {"horizon": "1-5d", "execution_mode": "taker",
         "expected_gross_edge_bps": 22},
        {"horizon": "5m", "execution_mode": "taker",
         "expected_gross_edge_bps": 8},
        {"horizon": "5m", "execution_mode": "maker", "expected_gross_edge_bps": 8},
        {"horizon": "5m", "execution_mode": "taker",
         "expected_gross_edge_bps": 60,
         "fast_horizon_argument": "4x taker cost cleared at 60 bps gross "
                                  "vs 46 bps hurdle"},
    ]
    for s in samples:
        ok, errs = validate_horizon(s)
        print(f"horizon={s['horizon']:8s} mode={s['execution_mode']:5s} "
              f"edge={s['expected_gross_edge_bps']:>3} -> ok={ok} {errs}")