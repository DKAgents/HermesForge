#!/usr/bin/env python3
"""
rule_builder.py — US-222 builder: reconstruct a SINGLE-FEATURE trading rule from
a dated position/trade record (a long/short/flat state timeline).

Design (architect_us222_record_reverse_engineering_builder_spec.md):

  * Feature library is SMALL and pre-enumerated (price-derived: SMA cross /
    momentum / breakout; positioning: funding extreme / OI change). Each is a
    thin wrapper over a rolling window of `close` (or an expanding z-score of
    funding / OI delta). No feature is invented.
  * Objective = agreement_IS − λ·feature_count, prefer-fewest (§2.3). For v1
    (orchestrator Q2 resolution) the builder is SINGLE-FEATURE ONLY: it returns
    the one-feature rule with the highest in-sample agreement. A 2-feature
    candidate is computed only to be LOGGED as a v2 note — never auto-promoted.
  * Time-seal (§3): chronological-midpoint split; the RECENT half is sealed OOS
    and the builder never sees it. Random splits are forbidden.
  * Data-gate (§3.3): decline (never force) a record with too few STATE
    TRANSITIONS (not raw rows) in either half.
  * Emission (§2.4): structured rule dict + generated Python function +
    param_hash (stable sort) + feature-library VERSION.

Market-data dependency (Q8): reconstruction requires the instrument's OHLC +
funding + OI series (HL stores). A missing series declines the build
(data-gated); prices are NEVER imputed.

Purely deterministic and side-effect free: no network, no store writes. The
breaker (breaker_harness.py) owns OOS replay + gauntlet handoff + ledger writes.
"""

from __future__ import annotations

import bisect
import hashlib
import json
import math
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable, Optional

# ---------------------------------------------------------------------------
# Feature-library constants
# ---------------------------------------------------------------------------
FEATURE_LIBRARY_VERSION = "1"

# Q1 — small discrete parameter grids (cheap search, tractable multiple-testing).
SMA_N_GRID = (5, 10, 20, 50, 100)
MOMENTUM_N_GRID = (5, 10, 20, 50)
MOMENTUM_K_BPS_GRID = (10, 25, 50, 100)
BREAKOUT_N_GRID = (10, 20, 50, 100)
FUNDING_Z_GRID = (1.0, 2.0, 3.0)
OI_DZ_GRID = (1.0, 2.0, 3.0)

# Q3 — parsimony tuning constants. Prefer-fewest (§2.3) is the binding
# discipline; these only matter once multi-feature search exists. λ penalizes
# each feature in the objective; β is the agreement margin a (k+1)-feature rule
# must clear over the best k-feature rule. In single-feature v1 both are inert
# but DOCUMENTED (not invented prose — they are named constants with rationale).
LAMBDA = 0.05   # objective penalty per feature
BETA = 0.05     # feature-addition agreement margin (2-feature only)

# Q5 — transition-count data-gate (DOCUMENTED defaults; the backtester validates
# them on the synthetic fixtures, not this module). A "transition" is a change
# in carried state between consecutive observations (long↔short, long↔flat,
# short↔flat). A record flat throughout has 0 transitions and carries no
# signal: it is declined, never scored.
MIN_TRAIN_TRANSITIONS = 8   # min in/out transitions in the OLDER (train) half
MIN_OOS_TRANSITIONS = 8     # min in/out transitions in the SEALED (OOS) half

# Q6 — agreement floors (DOCUMENTED defaults). The no-skill baseline is the
# better of always-flat agreement and state-imbalance (majority-class)
# agreement on the OOS half; a reconstructed rule must CLEAR that baseline by
# NO_SKILL_MARGIN to advance. MIN_AGREEMENT_IS is the floor to emit a rule at
# all (a rule that cannot even reproduce the train half is not a reconstruction).
NO_SKILL_MARGIN = 0.10      # agreement_OOS − baseline must exceed this (10 pp)
MIN_AGREEMENT_IS = 0.60     # min in-sample agreement to emit any rule

# Q4 — split fraction (train / total). 0.5 = 50/50 chronological midpoint. The
# "seal recent, chronological, never random" principle holds regardless.
SPLIT_FRACTION = 0.5

# State encoding: +1 long, -1 short, 0 flat, None = undefined (warmup).
_STATE_STR = {1: "long", -1: "short", 0: "flat"}
_STR_STATE = {"long": 1, "short": -1, "flat": 0}


# ---------------------------------------------------------------------------
# Series
# ---------------------------------------------------------------------------

class BarSeries:
    """Instrument bar series required for reconstruction (Q8).

    OHLC + funding + OI. funding is the per-bar hourly funding rate; oi is the
    per-bar open interest. funding_z / oi_delta_z are derived lazily once.
    Missing/incomplete series => the build is data-gated (never imputed).
    """

    def __init__(self, ts, open_, high, low, close, funding=None, oi=None):
        self.ts = list(ts)
        self.open = list(open_)
        self.high = list(high)
        self.low = list(low)
        self.close = list(close)
        self.funding = list(funding) if funding is not None else []
        self.oi = list(oi) if oi is not None else []
        self._funding_z: Optional[list] = None
        self._oi_delta_z: Optional[list] = None

    @property
    def n(self) -> int:
        return len(self.close)

    def complete(self) -> bool:
        """True iff OHLC + funding + OI are all present and equally long."""
        n = self.n
        if n == 0:
            return False
        return (len(self.open) == n and len(self.high) == n
                and len(self.low) == n and len(self.funding) == n
                and len(self.oi) == n)

    @property
    def funding_z(self) -> list:
        if self._funding_z is None:
            self._funding_z = _expanding_z(self.funding)
        return self._funding_z

    @property
    def oi_delta_z(self) -> list:
        if self._oi_delta_z is None:
            self._oi_delta_z = _oi_delta_z_series(self.oi)
        return self._oi_delta_z


def _expanding_z(values) -> list:
    """Expanding z-score: z[i] = (values[i] − mean(values[:i])) / std(values[:i]).

    None for i < 2 (need >=2 prior observations) or zero variance. Mirrors
    funding_state.compute_funding_z / oi_delta.compute_oi_delta_z (latest vs
    prior history), computed over the full series in O(n).
    """
    n = len(values)
    out: list = [None] * n
    if n < 3:
        return out
    s = values[0]
    ss = values[0] * values[0]
    for i in range(1, n):
        cnt = i
        mean = s / cnt
        var = (ss - cnt * mean * mean) / (cnt - 1) if cnt >= 2 else 0.0
        if cnt >= 2 and var > 0:
            out[i] = (values[i] - mean) / math.sqrt(var)
        s += values[i]
        ss += values[i] * values[i]
    return out


def _oi_delta_z_series(oi) -> list:
    """oi_delta_z[i] = expanding z of (oi[i] − oi[i−1]); None for bar 0 / warmup."""
    n = len(oi)
    out: list = [None] * n
    if n < 3:
        return out
    diffs = [oi[i] - oi[i - 1] for i in range(1, n)]
    zs = _expanding_z(diffs)
    for i in range(1, n):
        out[i] = zs[i - 1]
    return out


# ---------------------------------------------------------------------------
# Rolling-window primitives (thin wrappers over `close`)
# ---------------------------------------------------------------------------

def _rolling_mean(vals, n):
    out = [None] * len(vals)
    s = 0.0
    for i, v in enumerate(vals):
        s += v
        if i >= n:
            s -= vals[i - n]
        if i >= n - 1:
            out[i] = s / n
    return out


def _prior_high(vals, n):
    out = [None] * len(vals)
    for i in range(n, len(vals)):
        out[i] = max(vals[i - n:i])
    return out


def _prior_low(vals, n):
    out = [None] * len(vals)
    for i in range(n, len(vals)):
        out[i] = min(vals[i - n:i])
    return out


# ---------------------------------------------------------------------------
# Feature state functions: series -> list[Optional[int]] (aligned to bars)
# ---------------------------------------------------------------------------

def _sma_cross_above(series, n):
    sma = _rolling_mean(series.close, n)
    out = []
    for i in range(series.n):
        out.append(1 if sma[i] is not None and series.close[i] > sma[i]
                   else (0 if sma[i] is not None else None))
    return out


def _sma_cross_below(series, n):
    sma = _rolling_mean(series.close, n)
    out = []
    for i in range(series.n):
        out.append(-1 if sma[i] is not None and series.close[i] < sma[i]
                   else (0 if sma[i] is not None else None))
    return out


def _momentum(series, n, k_bps):
    close = series.close
    out = []
    for i in range(series.n):
        if i < n:
            out.append(None)
            continue
        ret = (close[i] - close[i - n]) / close[i - n] * 10000.0
        out.append(1 if ret > k_bps else (-1 if ret < -k_bps else 0))
    return out


def _breakout_high(series, n):
    close = series.close
    ph = _prior_high(series.high, n)
    pl = _prior_low(series.low, n)
    out = []
    pos = 0
    for i in range(series.n):
        if ph[i] is None or pl[i] is None:
            out.append(None)
            continue
        if pos == 0 and close[i] > ph[i]:
            pos = 1
        elif pos == 1 and close[i] < pl[i]:
            pos = 0
        out.append(pos)
    return out


def _breakout_low(series, n):
    close = series.close
    ph = _prior_high(series.high, n)
    pl = _prior_low(series.low, n)
    out = []
    pos = 0
    for i in range(series.n):
        if ph[i] is None or pl[i] is None:
            out.append(None)
            continue
        if pos == 0 and close[i] < pl[i]:
            pos = -1
        elif pos == -1 and close[i] > ph[i]:
            pos = 0
        out.append(pos)
    return out


def _funding_extreme(funding_z, z, side):
    out = []
    for fz in funding_z:
        if fz is None:
            out.append(None)
        elif side == "long":
            out.append(1 if fz > z else 0)
        else:
            out.append(-1 if fz < -z else 0)
    return out


def _oi_change(oi_delta_z, dz, side):
    out = []
    for o in oi_delta_z:
        if o is None:
            out.append(None)
        elif side == "long":
            out.append(1 if o > dz else 0)
        else:
            out.append(-1 if o < -dz else 0)
    return out


def apply_feature(series, family, params) -> list:
    """Apply a single feature to the series, returning state per bar."""
    if family == "sma_cross_above":
        return _sma_cross_above(series, params["n"])
    if family == "sma_cross_below":
        return _sma_cross_below(series, params["n"])
    if family == "momentum":
        return _momentum(series, params["n"], params["k_bps"])
    if family == "breakout_high":
        return _breakout_high(series, params["n"])
    if family == "breakout_low":
        return _breakout_low(series, params["n"])
    if family == "funding_extreme":
        return _funding_extreme(series.funding_z, params["z"], params["side"])
    if family == "oi_change":
        return _oi_change(series.oi_delta_z, params["dz"], params["side"])
    raise ValueError(f"unknown feature family {family!r}")


def feature_candidates() -> list:
    """Enumerate every single-feature candidate (family + params + direction/exit)."""
    cands = []
    for n in SMA_N_GRID:
        cands.append({"family": "sma_cross_above", "params": {"n": n},
                      "direction": "long", "exit": "flat"})
        cands.append({"family": "sma_cross_below", "params": {"n": n},
                      "direction": "short", "exit": "flat"})
    for n in MOMENTUM_N_GRID:
        for k in MOMENTUM_K_BPS_GRID:
            cands.append({"family": "momentum", "params": {"n": n, "k_bps": k},
                          "direction": "both", "exit": "flat"})
    for n in BREAKOUT_N_GRID:
        cands.append({"family": "breakout_high", "params": {"n": n},
                      "direction": "long", "exit": "flat"})
        cands.append({"family": "breakout_low", "params": {"n": n},
                      "direction": "short", "exit": "flat"})
    for z in FUNDING_Z_GRID:
        cands.append({"family": "funding_extreme", "params": {"z": z, "side": "long"},
                      "direction": "long", "exit": "flat"})
        cands.append({"family": "funding_extreme", "params": {"z": z, "side": "short"},
                      "direction": "short", "exit": "flat"})
    for dz in OI_DZ_GRID:
        cands.append({"family": "oi_change", "params": {"dz": dz, "side": "long"},
                      "direction": "long", "exit": "flat"})
        cands.append({"family": "oi_change", "params": {"dz": dz, "side": "short"},
                      "direction": "short", "exit": "flat"})
    return cands


# ---------------------------------------------------------------------------
# Record normalization (Part 1)
# ---------------------------------------------------------------------------

@dataclass
class NormalizedRecord:
    instrument: str
    venue: str
    asset_class: str
    timeframe: Optional[str]
    source: str
    rows: list  # list of {ts_ms, state, price, size, pnl} sorted by ts_ms
    dropped_timestamp: int = 0
    excluded_direction: int = 0


def _parse_ts(value) -> Optional[float]:
    """ISO-8601 UTC or epoch -> epoch milliseconds. None if unparseable."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        # Heuristic: ms epoch if > 1e12, else seconds.
        v = float(value)
        return v if v > 1e12 else v * 1000.0
    if isinstance(value, str):
        s = value.strip()
        if not s:
            return None
        try:
            dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.timestamp() * 1000.0
        except ValueError:
            return None
    return None


def normalize_record(record: dict) -> NormalizedRecord:
    """Normalize a record dict into a sortable row list, fail-closed (§1.3).

    - rows missing `timestamp` are DROPPED (counted).
    - rows missing/invalid `direction` are EXCLUDED from the timeline (counted).
    - `price`/`size` optional; `pnl` is provenance-only (never a backtest input).
    """
    instrument = record.get("instrument", "")
    venue = record.get("venue", "")
    asset_class = record.get("asset_class", "crypto")
    timeframe = record.get("timeframe")
    source = record.get("source", "record")

    rows = []
    dropped_ts = 0
    excluded_dir = 0
    for r in record.get("records", []) if isinstance(record, dict) else []:
        if not isinstance(r, dict):
            continue
        ts = _parse_ts(r.get("timestamp"))
        if ts is None:
            dropped_ts += 1
            continue
        d = r.get("direction")
        if d not in _STR_STATE:
            excluded_dir += 1
            continue
        rows.append({
            "ts_ms": ts,
            "state": _STR_STATE[d],
            "price": r.get("price"),
            "size": r.get("size"),
            "pnl": r.get("pnl"),
        })

    rows.sort(key=lambda x: x["ts_ms"])
    return NormalizedRecord(
        instrument=instrument, venue=venue, asset_class=asset_class,
        timeframe=timeframe, source=source, rows=rows,
        dropped_timestamp=dropped_ts, excluded_direction=excluded_dir,
    )


def build_state_timeline(rows) -> list:
    """Sorted (ts_ms, state) timeline. Carry-forward is implicit in the read
    function (record_state_at), not materialized here (a snapshot carries to the
    next row by definition of a position snapshot, §1.2)."""
    return [(r["ts_ms"], r["state"]) for r in rows]


def make_record_state_fn(timeline) -> Callable[[float], Optional[int]]:
    """Return fn(ts_ms) -> carried state, or None in unknowable regions.

    Before the first row, and after the last row unless it is flat, are
    unknowable and return None (§1.3) — excluded from agreement scoring.
    """
    tss = [t for t, _ in timeline]
    states = [s for _, s in timeline]
    n = len(timeline)

    def fn(ts):
        idx = bisect.bisect_right(tss, ts) - 1
        if idx < 0:
            return None
        if idx == n - 1:
            # after the last row: known only if the last state is flat
            if ts > tss[-1] and states[-1] != 0:
                return None
        return states[idx]

    return fn


def count_transitions(timeline, *, before: Optional[float] = None,
                      after: Optional[float] = None) -> int:
    """Number of state changes between consecutive timeline entries, optionally
    constrained to entries whose ts is < `before` (train) or >= `after` (OOS).
    A transition is credited to the half containing its LATER entry."""
    n = 0
    for i in range(1, len(timeline)):
        later_ts = timeline[i][0]
        if before is not None and later_ts >= before:
            continue
        if after is not None and later_ts < after:
            continue
        if timeline[i - 1][1] != timeline[i][1]:
            n += 1
    return n


# ---------------------------------------------------------------------------
# Agreement scoring
# ---------------------------------------------------------------------------

def agreement_stats(states, record_state_fn, bar_ts, indices) -> dict:
    """Compute {agreement, matched, scored} over the given bar indices.

    A bar is scored only where BOTH the rule state and the record state are
    known (no warmup, no unknowable region). agreement is None if nothing is
    scored ("no number not computed" — never fabricate an agreement).
    """
    matched = 0
    scored = 0
    for i in indices:
        s = states[i]
        if s is None:
            continue
        r = record_state_fn(bar_ts[i])
        if r is None:
            continue
        scored += 1
        if r == s:
            matched += 1
    if scored == 0:
        return {"agreement": None, "matched": 0, "scored": 0}
    return {"agreement": matched / scored, "matched": matched, "scored": scored}


# ---------------------------------------------------------------------------
# Rule emission (Part 2.4)
# ---------------------------------------------------------------------------

def param_hash(family: str, params: dict) -> str:
    """Stable hash over feature+params (sorted), for ledger dedupe/re-run."""
    canon = json.dumps({"family": family, "params": params},
                       sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canon.encode("utf-8")).hexdigest()[:16]


def _generate_code(family: str, params: dict, direction: str, exit_state: str) -> str:
    return (
        f"def rule(series):\n"
        f"    # {family} {params}  (direction={direction}, exit={exit_state})\n"
        f"    from rule_builder import apply_feature\n"
        f"    return apply_feature(series, {family!r}, {params!r})\n"
    )


def emit_rule(candidate: dict, series, agreement_is, scored, feature_count) -> dict:
    """Build the structured, auditable rule dict (§2.4)."""
    family = candidate["family"]
    params = candidate["params"]
    return {
        "feature": family,
        "params": dict(params),
        "direction": candidate["direction"],
        "exit": candidate["exit"],
        "param_hash": param_hash(family, params),
        "feature_library_version": FEATURE_LIBRARY_VERSION,
        "feature_count": feature_count,
        "agreement_is": round(agreement_is, 6) if agreement_is is not None else None,
        "scored_observations": scored,
        "code": _generate_code(family, params, candidate["direction"],
                               candidate["exit"]),
    }


# ---------------------------------------------------------------------------
# Boundary purge (Part 3.2)
# ---------------------------------------------------------------------------

def boundary_purge_indices(bar_ts, record_state_fn, t_split) -> set:
    """Bar indices in the TRAIN half to exclude because a position is still open
    at t_split. If the carried state at t_split is long/short, walk back through
    the trailing train bars while they share that non-flat state and exclude them
    (their continuation leaks into OOS). Deterministic; a no-op for records that
    are flat at the split."""
    state_at_split = record_state_fn(t_split)
    if state_at_split not in (1, -1):
        return set()
    excluded = set()
    for i in range(len(bar_ts) - 1, -1, -1):
        if bar_ts[i] >= t_split:
            continue
        if record_state_fn(bar_ts[i]) == 0:
            break
        excluded.add(i)
    return excluded


# ---------------------------------------------------------------------------
# The reconstruction driver
# ---------------------------------------------------------------------------

def reconstruct(record: dict, series: Optional[BarSeries]) -> dict:
    """Reconstruct the smallest (single-feature) rule reproducing a record.

    Returns a report dict. `status` is one of:
      - "ok": a rule was emitted (breaker decides advance/kill).
      - "data_gated": declined (missing series, or too few transitions).
      - "insufficient_data": no rule cleared MIN_AGREEMENT_IS.
    """
    norm = normalize_record(record)

    # Q8 — series required; missing/incomplete => data-gated, never impute.
    if series is None or not series.complete():
        return {"status": "data_gated",
                "reason": "missing/incomplete instrument series "
                          "(OHLC + funding + OI required; never imputed)",
                "normalized": norm, "rule": None}

    timeline = build_state_timeline(norm.rows)
    if len(timeline) == 0:
        return {"status": "data_gated", "reason": "no scored observations "
                "(record has no valid timestamp+direction rows)", "rule": None,
                "normalized": norm}

    # Q4 — chronological-midpoint split (NEVER random).
    min_ts = timeline[0][0]
    max_ts = timeline[-1][0]
    t_split = min_ts + (max_ts - min_ts) * SPLIT_FRACTION

    bar_ts = series.ts
    train_indices = [i for i, ts in enumerate(bar_ts) if ts < t_split]
    oos_indices = [i for i, ts in enumerate(bar_ts) if ts >= t_split]

    # Q5 — transition-count data-gate (train and OOS separately).
    train_transitions = count_transitions(timeline, before=t_split)
    oos_transitions = count_transitions(timeline, after=t_split)
    if train_transitions < MIN_TRAIN_TRANSITIONS or oos_transitions < MIN_OOS_TRANSITIONS:
        return {
            "status": "data_gated",
            "reason": (f"insufficient state transitions to measure agreement "
                       f"(train={train_transitions}<{MIN_TRAIN_TRANSITIONS}, "
                       f"oos={oos_transitions}<{MIN_OOS_TRANSITIONS})"),
            "rule": None, "normalized": norm,
            "train_transitions": train_transitions,
            "oos_transitions": oos_transitions,
        }

    record_state_fn = make_record_state_fn(timeline)
    purged = boundary_purge_indices(bar_ts, record_state_fn, t_split)
    train_scored = [i for i in train_indices if i not in purged]

    # Search single features over the train half only (builder never sees OOS).
    best = None
    for cand in feature_candidates():
        states = apply_feature(series, cand["family"], cand["params"])
        stats = agreement_stats(states, record_state_fn, bar_ts, train_scored)
        ag = stats["agreement"]
        if ag is None:
            continue
        if best is None or ag > best["agreement_is"]:
            best = {"candidate": cand, "agreement_is": ag,
                    "scored": stats["scored"], "states": states}

    if best is None or best["agreement_is"] < MIN_AGREEMENT_IS:
        return {"status": "insufficient_data",
                "reason": "no single-feature rule cleared the in-sample "
                          f"agreement floor ({MIN_AGREEMENT_IS})",
                "rule": None, "normalized": norm,
                "best_agreement_is": best["agreement_is"] if best else None}

    rule = emit_rule(best["candidate"], series, best["agreement_is"],
                     best["scored"], feature_count=1)

    # Q2 — single-feature only. Compute (but do NOT auto-promote) a 2-feature
    # conjunction candidate purely as a v2 note.
    v2_note = _best_two_feature_note(best, series, record_state_fn, bar_ts,
                                     train_scored)

    return {
        "status": "ok",
        "rule": rule,
        "normalized": norm,
        "t_split": t_split,
        "train_indices": train_indices,
        "oos_indices": oos_indices,
        "purged_indices": sorted(purged),
        "train_transitions": train_transitions,
        "oos_transitions": oos_transitions,
        "v2_note": v2_note,
    }


def _best_two_feature_note(best, series, record_state_fn, bar_ts, indices) -> str:
    """Log (never promote) the best 2-feature conjunction candidate as a v2 note.

    Conjunction = state where both features agree non-flat in the same direction
    (both long => long, both short => short, else flat). Informational only: the
    returned rule is always the single-feature winner.
    """
    base_family = best["candidate"]["family"]
    base_params = best["candidate"]["params"]
    base_states = best["states"]
    best_pair_ag = None
    best_pair = None
    for cand in feature_candidates():
        if cand["family"] == base_family and cand["params"] == base_params:
            continue
        other = apply_feature(series, cand["family"], cand["params"])
        conj = _conjunction(base_states, other)
        stats = agreement_stats(conj, record_state_fn, bar_ts, indices)
        if stats["agreement"] is None:
            continue
        if best_pair_ag is None or stats["agreement"] > best_pair_ag:
            best_pair_ag = stats["agreement"]
            best_pair = cand
    if best_pair is None:
        return ("single-feature-only (Q2); no 2-feature candidate evaluated "
                "(deferred to v2)")
    return (f"v2 note (not promoted): 2-feature conjunction "
            f"{base_family}{base_params} AND {best_pair['family']}{best_pair['params']} "
            f"agreement_is={best_pair_ag:.4f}")


def _conjunction(a, b) -> list:
    out = []
    for x, y in zip(a, b):
        if x is None or y is None:
            out.append(None)
        elif x == 1 and y == 1:
            out.append(1)
        elif x == -1 and y == -1:
            out.append(-1)
        else:
            out.append(0)
    return out
