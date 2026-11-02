"""
Hypothesis Register Skill Module (PROP-001).

Pre-register hypotheses before backtests. Every hypothesis gets a note with
falsification criteria and expected effect size BEFORE any backtest runs.
The trials ledger records the hypothesis_id.

Seed pool: HYP-01 through HYP-10 from PROP-001.

US-202 (EPIC-017 Phase 2): every hypothesis must now carry REQUIRED structured
frontmatter before G0. ``validate_frontmatter`` enforces the schema (including
the load-bearing ``counterparty`` field) and ``register`` / ``pre_register_from_seed_pool``
REJECT (write nothing) when validation fails. Rejection happens at INTAKE —
never at a later gate.

Storage: append-only JSONL at /root/HermesForge/data/gauntlet/hypotheses.jsonl
"""

from __future__ import annotations

import json
import math
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

# US-191: hard signal-class intake gate (fast-fail retail-TA / chart-pattern /
# ICT-SMC BEFORE G0). Reject at registration time, not skill-prior-only.
# FAIL-CLOSED: the import is unconditional — if signal_class cannot be
# imported, this module fails to load and register() is unavailable, so intake
# can never silently bypass the gate on an ImportError.
from signal_class import intake_verdict as _signal_intake  # same dir


HYPOTHESES_FILE = os.path.join(
    os.path.dirname(__file__), "..", "..", "data", "gauntlet", "hypotheses.jsonl"
)
# Resolve to absolute path
HYPOTHESES_FILE = os.path.abspath(HYPOTHESES_FILE)


# ---------------------------------------------------------------------------
# US-202: required frontmatter contract (architect_us202_hypothesis_frontmatter_spec.md)
# ---------------------------------------------------------------------------

# Part 1 field table — fields 1..14 are REQUIRED. In insertion order (the order
# the architect spec lists them).
REQUIRED_FIELDS = [
    "hypothesis_id", "source", "venue", "instruments", "horizon",
    "entry_logic", "exit_logic", "expected_gross_edge_bps",
    "cost_hurdle_bps", "data_dependencies", "counterparty",
    "execution_mode", "falsification_criteria", "primitives",
]

# Part 1.3 enum constraints
SOURCE_ENUM = {"human", "council", "web", "generated"}
EXEC_MODE_ENUM = {"taker", "maker"}
VENUE = "hyperliquid"  # the ONLY supported venue today (any other value rejected)

# Fields that must be non-empty LISTS (Part 2.2 rule 6).
_LIST_FIELDS = {"instruments", "data_dependencies", "primitives"}
# Fields that must be finite numbers (Part 2.2 rule 5).
_NUMERIC_FIELDS = {"expected_gross_edge_bps", "cost_hurdle_bps"}


def validate_frontmatter(entry: Dict[str, Any]) -> tuple[bool, List[str]]:
    """Validate the US-202 hypothesis frontmatter schema.

    Returns ``(ok, errors)`` where ``errors`` lists a human-readable reason per
    failing field (so a scraper/generator agent can be corrected), not a bare
    boolean. Every field in ``REQUIRED_FIELDS`` is treated identically — the
    load-bearing ``counterparty`` field gets no softer treatment (Part 1.2).

    Rejection rules (Part 2.2), all collected (not first-only) so a dry-run
    intake can surface every defect at once:

    1. any required field missing / empty string / empty list -> error;
    2. ``source`` not in SOURCE_ENUM -> error;
    3. ``execution_mode`` not in EXEC_MODE_ENUM -> error;
    4. ``venue != "hyperliquid"`` -> error;
    5. ``expected_gross_edge_bps`` / ``cost_hurdle_bps`` not finite -> error;
    6. ``instruments`` / ``data_dependencies`` / ``primitives`` not non-empty
       lists -> error.
    """
    errors: List[str] = []

    # Rule 1 — presence + non-empty (counterparty included, identically).
    for field in REQUIRED_FIELDS:
        if field not in entry or entry[field] is None:
            errors.append(f"missing required field '{field}'")
            continue
        val = entry[field]
        if isinstance(val, bool):
            errors.append(f"required field '{field}' must not be a boolean")
        elif isinstance(val, str) and val.strip() == "":
            errors.append(f"required field '{field}' is empty")
        elif isinstance(val, (list, tuple)) and len(val) == 0:
            errors.append(f"required field '{field}' is empty")

    # Rule 2/3/4 — enum / venue constraints (only if the value was present, so a
    # missing field is reported once under rule 1, not duplicated here).
    if entry.get("source") is not None and entry.get("source") not in SOURCE_ENUM:
        errors.append(
            f"source must be one of {sorted(SOURCE_ENUM)}, got {entry.get('source')!r}"
        )
    if entry.get("execution_mode") is not None and entry.get("execution_mode") not in EXEC_MODE_ENUM:
        errors.append(
            f"execution_mode must be one of {sorted(EXEC_MODE_ENUM)}, "
            f"got {entry.get('execution_mode')!r}"
        )
    if entry.get("venue") is not None and entry.get("venue") != VENUE:
        errors.append(f"venue must be '{VENUE}', got {entry.get('venue')!r}")

    # Rule 5 — numeric fields must be finite numbers (reject bool/NaN/inf/str).
    for field in _NUMERIC_FIELDS:
        val = entry.get(field)
        if val is None or field not in entry:
            continue  # already reported missing under rule 1
        if isinstance(val, bool) or not isinstance(val, (int, float)) \
                or not math.isfinite(float(val)):
            errors.append(f"'{field}' must be a finite number, got {val!r}")

    # Rule 6 — list fields must actually be lists (non-emptiness checked above).
    for field in _LIST_FIELDS:
        val = entry.get(field)
        if val is None:
            continue
        if not isinstance(val, (list, tuple)):
            errors.append(
                f"'{field}' must be a non-empty list, got {type(val).__name__}"
            )

    return (len(errors) == 0, errors)


# Seed pool from PROP-001, upgraded to carry the full US-202 frontmatter.
# 5m-horizon seeds (HYP-02/03/04/08) are authored with the full schema here;
# the US-204 horizon-preference gate is a SEPARATE post-frontmatter check and is
# deliberately NOT run during seed-pool pre-registration (the seed pool is the
# pre-existing corpus, not a new intake).
SEED_POOL: List[Dict[str, Any]] = [
    {
        "hypothesis_id": "HYP-01",
        "source": "human",
        "venue": "hyperliquid",
        "instruments": ["universe:hl-perps"],
        "horizon": "4-48h",
        "entry_logic": "Fade crowded positioning when perp funding rate exceeds "
                       "its 95th percentile AND open interest is still rising.",
        "exit_logic": "Exit on funding mean-reversion below the 80th percentile, "
                      "or a hard stop at 1x structure-wide ATR against the entry.",
        "expected_gross_edge_bps": 15,
        "cost_hurdle_bps": 45,
        "data_dependencies": ["hl:fundingHistory", "hl:assetCtxs.openInterest"],
        "counterparty": "Late retail longs crowding a high-funding regime — they "
                        "accept negative funding carry because they are "
                        "momentum-chasing, not carry-aware, so the unwind pays "
                        "them to hold and price corrects against them.",
        "execution_mode": "taker",
        "falsification_criteria": "Sharpe < 0.5 over 200+ trades, or edge "
                                  "disappears after funding < 80th %ile.",
        "primitives": ["funding_z", "oi_trend", "regime"],
        "description": "Funding-extreme unwind. Fade crowded positioning when "
                       "funding >95th %ile + OI still rising.",
        "tier": "T3",
        "timeframe": "1h-6h",
    },
    {
        "hypothesis_id": "HYP-02",
        "source": "human",
        "venue": "hyperliquid",
        "instruments": ["universe:hl-perps"],
        "horizon": "5m",
        "entry_logic": "Enter range breakouts only when price moves up AND open "
                       "interest rises (the new-money quadrant), confirming "
                       "conviction behind the move.",
        "exit_logic": "Stop below the broken range at structure support; target "
                      "1.5x the range width; time-stop after one session.",
        "expected_gross_edge_bps": 20,
        "cost_hurdle_bps": 45,
        "data_dependencies": ["hl:l2Book", "hl:assetCtxs.openInterest",
                              "hl:candleSnapshot"],
        "counterparty": "Range-bound short-term traders and stop-resting liquidity "
                        "positioned on the wrong side of the breakout — they are "
                        "forced to cover as new-money OI confirms direction.",
        "execution_mode": "taker",
        "falsification_criteria": "Win rate < 45% or PF < 1.2 in quadrant 1 only.",
        "primitives": ["oi_quadrant", "range_breakout"],
        "description": "OI-confirmed breakout. Range breakouts only in "
                       "price↑/OI↑ quadrant (new money).",
        "tier": "T2",
        "timeframe": "5m",
    },
    {
        "hypothesis_id": "HYP-03",
        "source": "human",
        "venue": "hyperliquid",
        "instruments": ["universe:hl-perps"],
        "horizon": "5m-15m",
        "entry_logic": "After a liquidation cascade, enter the first retrace in "
                       "the direction opposite to the forced liquidation pressure.",
        "exit_logic": "Exit at the prior structure or 2x ATR; stop at the cascade "
                      "extreme (give back the full cascade range).",
        "expected_gross_edge_bps": 25,
        "cost_hurdle_bps": 45,
        "data_dependencies": ["okx:liquidation", "hl:assetCtxs.openInterest",
                              "hl:candleSnapshot"],
        "counterparty": "Forced liquidations of over-leveraged positions — "
                        "liquidators and cascaded traders dump regardless of "
                        "value, creating overshoot that the retrace fades.",
        "execution_mode": "taker",
        "falsification_criteria": "No significant return anomaly in the 30min "
                                  "following cascade events (p > 0.10).",
        "primitives": ["liquidation_cascade", "retrace"],
        "description": "Cascade exhaustion. After liquidation cascade, first "
                       "retrace tradeable opposite direction.",
        "tier": "T3",
        "timeframe": "5m-15m",
    },
    {
        "hypothesis_id": "HYP-04",
        "source": "human",
        "venue": "hyperliquid",
        "instruments": ["universe:hl-perps"],
        "horizon": "5m",
        "entry_logic": "Trade the directional drift in the minutes surrounding "
                       "the hourly funding settlement boundary.",
        "exit_logic": "Exit immediately after the settlement window closes; stop "
                      "at 1x ATR against the entry.",
        "expected_gross_edge_bps": 10,
        "cost_hurdle_bps": 45,
        "data_dependencies": ["hl:fundingHistory", "hl:candleSnapshot"],
        "counterparty": "Funding-rate hedgers mechanically rebalancing at "
                        "settlement — their scheduled flow creates predictable "
                        "drift that late retail misprices.",
        "execution_mode": "taker",
        "falsification_criteria": "Median return in settlement window not "
                                  "significantly different from non-settlement "
                                  "windows (p > 0.05).",
        "primitives": ["funding_z", "settlement_countdown"],
        "description": "Settlement-hour drift. Directional drift around hourly "
                       "funding settlement boundary.",
        "tier": "T3",
        "timeframe": "5m",
    },
    {
        "hypothesis_id": "HYP-05",
        "source": "human",
        "venue": "hyperliquid",
        "instruments": ["universe:hl-perps"],
        "horizon": "1-7d",
        "entry_logic": "Long the top-decile and short the bottom-decile 7-day "
                       "perp return, gated so funding is not extreme against "
                       "the position.",
        "exit_logic": "Rebalance weekly; exit on rank decay below the median or "
                      "a 2σ idiosyncratic stop.",
        "expected_gross_edge_bps": 30,
        "cost_hurdle_bps": 45,
        "data_dependencies": ["hl:candleSnapshot", "hl:fundingHistory"],
        "counterparty": "Momentum under-reaction and slow capital flows into "
                        "recent winners — delayed indexers and trend followers "
                        "who pay the spread to catch up after the move.",
        "execution_mode": "taker",
        "falsification_criteria": "Long-short spread not significantly > 0 after "
                                  "costs across 3 consecutive rolling windows.",
        "primitives": ["momentum_7d", "funding_filter"],
        "description": "Cross-sectional perp momentum. Long top-decile / short "
                       "bottom-decile 7-day return with funding filter.",
        "tier": "T1",
        "timeframe": "1d",
    },
    {
        "hypothesis_id": "HYP-06",
        "source": "human",
        "venue": "hyperliquid",
        "instruments": ["BTC", "universe:alts"],
        "horizon": "5m-4h",
        "entry_logic": "Short the alt residual against its BTC-beta-implied "
                       "price when the residual exceeds 2σ.",
        "exit_logic": "Cover when the residual reverts to its mean; stop at 3σ "
                      "against the entry.",
        "expected_gross_edge_bps": 18,
        "cost_hurdle_bps": 45,
        "data_dependencies": ["hl:candleSnapshot", "hl:assetCtxs.markPx",
                              "hl:assetCtxs.oraclePx"],
        "counterparty": "Alts traders pricing off a stale BTC-beta estimate — "
                        "they trade yesterday's relationship rather than current "
                        "cross-sectional fair value.",
        "execution_mode": "taker",
        "falsification_criteria": "PF < 1.1 after accounting for two-leg "
                                  "round-trip costs.",
        "primitives": ["btc_beta", "residual_reversion"],
        "description": "BTC-beta residual reversion. Alt residual against "
                       "BTC-beta-implied price, reverts when >2σ.",
        "tier": "T2",
        "timeframe": "5m-4h",
    },
    {
        "hypothesis_id": "HYP-07",
        "source": "human",
        "venue": "hyperliquid",
        "instruments": ["BTC", "ETH", "SOL"],
        "horizon": "5m-1h",
        "entry_logic": "Break the Asia-session range with European-session "
                       "confirmation, then carry the position toward the US open.",
        "exit_logic": "Stop at the Asia-range low; target the measured move to "
                      "the next session's support/resistance.",
        "expected_gross_edge_bps": 12,
        "cost_hurdle_bps": 45,
        "data_dependencies": ["hl:candleSnapshot"],
        "counterparty": "Session-bound retail resting orders at the Asia-range "
                        "extremes — European and early-US flow runs those stops "
                        "into a confirmed continuation.",
        "execution_mode": "taker",
        "falsification_criteria": "Session-conditional PF < 1.0 when EU "
                                  "confirmation missing.",
        "primitives": ["asia_range", "eu_continuation", "session"],
        "description": "Asia-range / EU-continuation. Asia range break, "
                       "EU-confirmed, carried through US open.",
        "tier": "T2",
        "timeframe": "5m-1h",
    },
    {
        "hypothesis_id": "HYP-08",
        "source": "human",
        "venue": "hyperliquid",
        "instruments": ["universe:hl-perps"],
        "horizon": "5m",
        "entry_logic": "When the mark price diverges from the CEX-weighted-median "
                       "oracle beyond normal noise, fade the dislocation toward "
                       "snap-back.",
        "exit_logic": "Exit when mark-oracle basis converges or at 0.5x the "
                      "dislocation; hard stop at 1x the dislocation.",
        "expected_gross_edge_bps": 8,
        "cost_hurdle_bps": 45,
        "data_dependencies": ["hl:assetCtxs.markPx", "hl:assetCtxs.oraclePx",
                              "okx:ticker"],
        "counterparty": "Basis-insensitive takers forcing the mark away from the "
                        "oracle — market makers and arb desks restore fair value, "
                        "capturing the reversion against impatient flow.",
        "execution_mode": "taker",
        "falsification_criteria": "Dislocation magnitude insufficient to cover "
                                  "fees at 90th percentile size.",
        "primitives": ["oracle_divergence", "snap_back"],
        "description": "Oracle-mark dislocation. Mark vs CEX-weighted-median "
                       "oracle divergence snap-back.",
        "tier": "T3",
        "timeframe": "5m",
    },
    {
        "hypothesis_id": "HYP-09",
        "source": "human",
        "venue": "hyperliquid",
        "instruments": ["universe:hl-perps"],
        "horizon": "1-5d",
        "entry_logic": "Enter a directional expansion when ATR-percentile "
                       "<20th (compression) breaks out into a structural move.",
        "exit_logic": "Exit at a 1.5x ATR target or on volatility "
                      "mean-reversion; stop at the compression low.",
        "expected_gross_edge_bps": 22,
        "cost_hurdle_bps": 45,
        "data_dependencies": ["hl:candleSnapshot", "hl:assetCtxs.premium"],
        "counterparty": "Volatility sellers and range-scalpers who flattened "
                        "vol into the compression regime — they are "
                        "under-positioned when the structural break reprices "
                        "realized vol against them.",
        "execution_mode": "taker",
        "falsification_criteria": "False breakout rate > 60% or post-expansion "
                                  "drift < 1.5x ATR.",
        "primitives": ["atr_percentile", "vol_expansion", "regime"],
        "description": "Volatility compression expansion. ATR-percentile <20th "
                       "into directional expansion on structural break.",
        "tier": "T1",
        "timeframe": "1h-4h",
    },
    {
        "hypothesis_id": "HYP-10",
        "source": "human",
        "venue": "hyperliquid",
        "instruments": ["universe:new-listings"],
        "horizon": "1-14d",
        "entry_logic": "Long newly-listed perps exhibiting persistent funding "
                       "skew plus a directional drift.",
        "exit_logic": "Exit on listing-age end or funding convergence; stop at "
                      "2x ATR against the entry.",
        "expected_gross_edge_bps": 35,
        "cost_hurdle_bps": 45,
        "data_dependencies": ["hl:fundingHistory", "hl:assetCtxs.openInterest",
                              "hl:candleSnapshot"],
        "counterparty": "Early hedgers and sellers underpricing a fresh "
                        "listing's informational asymmetry — they short/sell "
                        "before the market discovers fair value, funding the drift.",
        "execution_mode": "taker",
        "falsification_criteria": "Drift not significantly different from zero "
                                  "for listings after 2026-Q1 (p > 0.05).",
        "primitives": ["new_listing", "funding_skew", "drift"],
        "description": "New-listing drift. Newly listed perps, persistent "
                       "funding skew + directional drift.",
        "tier": "T1",
        "timeframe": "4h-1d",
    },
]


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _load_all() -> List[Dict[str, Any]]:
    """Load all hypothesis entries from the JSONL file."""
    if not os.path.exists(HYPOTHESES_FILE):
        return []
    entries = []
    with open(HYPOTHESES_FILE, "r") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return entries


def _write_entry(entry: Dict[str, Any]) -> None:
    """Append a single entry to the JSONL file."""
    os.makedirs(os.path.dirname(HYPOTHESES_FILE), exist_ok=True)
    with open(HYPOTHESES_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")


def _entry_exists(hypothesis_id: str) -> bool:
    """Check if a hypothesis_id already exists in the ledger."""
    entries = _load_all()
    for entry in entries:
        if entry.get("hypothesis_id") == hypothesis_id:
            return True
    return False


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def register(entry: Dict[str, Any]) -> Dict[str, Any]:
    """
    Register a new hypothesis from a full US-202 frontmatter dict.

    Args:
        entry: a dict carrying the 14 required frontmatter fields
            (``hypothesis_id``, ``source``, ``venue``, ``instruments``,
            ``horizon``, ``entry_logic``, ``exit_logic``,
            ``expected_gross_edge_bps``, ``cost_hurdle_bps``,
            ``data_dependencies``, ``counterparty``, ``execution_mode``,
            ``falsification_criteria``, ``primitives``) plus any optional
            fields (``description``, ``tier``, ``holding_class``,
            ``timeframe``, ...), which are carried through verbatim.

    Returns:
        The registered entry dict with ``registered_at``, ``trials`` and
        ``status`` appended.

    Raises:
        ValueError: if the frontmatter fails validation (missing/invalid
            fields — rejected at INTAKE, before G0), if ``hypothesis_id``
            already exists, or if the signal-class intake gate (US-191)
            blocks the hypothesis.
    """
    if not isinstance(entry, dict):
        raise TypeError("register() expects a frontmatter dict")

    hypothesis_id = entry.get("hypothesis_id")
    if hypothesis_id is None or (isinstance(hypothesis_id, str)
                                 and hypothesis_id.strip() == ""):
        raise ValueError("hypothesis_id is required")
    hypothesis_id = str(hypothesis_id)

    if _entry_exists(hypothesis_id):
        raise ValueError(
            f"Hypothesis '{hypothesis_id}' already registered. "
            f"Use get('{hypothesis_id}') to retrieve it."
        )

    # US-202: validate frontmatter FIRST — missing/invalid fields (esp.
    # counterparty) reject at intake, before any other gate or write.
    ok, errors = validate_frontmatter(entry)
    if not ok:
        raise ValueError(
            f"Hypothesis '{hypothesis_id}' rejected at intake (before G0): "
            + "; ".join(errors)
        )

    # US-191: hard signal-class intake gate — reject retail-TA / chart-pattern /
    # ICT-SMC BEFORE G0. Enforcement at registration, not skill-prior-only.
    # Fail-closed: the gate always runs (the import is unconditional above).
    desc = entry.get("description") or entry.get("entry_logic") or ""
    prims = entry.get("primitives") or []
    verdict = _signal_intake(hypothesis_id=hypothesis_id,
                             description=desc,
                             primitives=prims)
    if not verdict["admitted"]:
        raise ValueError(
            f"Hypothesis '{hypothesis_id}' rejected at intake (before G0): "
            f"{verdict['reason']} (signal_class='{verdict['signal_class']}')"
        )

    holding_class = entry.get("holding_class", "")
    allowed = {"scalp", "day", "swing", "position"}
    if holding_class and holding_class not in allowed:
        raise ValueError(f"holding_class must be one of {sorted(allowed)}")

    record = dict(entry)
    record["registered_at"] = datetime.now(timezone.utc).isoformat()
    record["trials"] = []
    record["status"] = "registered"

    _write_entry(record)
    return record


def pre_register_from_seed_pool() -> List[Dict[str, Any]]:
    """
    Register all 10 hypotheses from the PROP-001 seed pool if not already
    registered.

    Returns:
        List of entries that were actually registered (skips duplicates).
    """
    registered = []
    for entry in SEED_POOL:
        hid = entry.get("hypothesis_id")
        if _entry_exists(hid):
            continue
        result = register(entry)
        registered.append(result)
    return registered


def list_all() -> List[Dict[str, Any]]:
    """Return all registered hypotheses."""
    return _load_all()


def get(hypothesis_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve a hypothesis by ID.

    Returns:
        The hypothesis dict, or None if not found.
    """
    entries = _load_all()
    for entry in entries:
        if entry.get("hypothesis_id") == hypothesis_id:
            return entry
    return None


def link_trial(hypothesis_id: str, trial_id: str) -> None:
    """
    Link a trials_ledger entry to this hypothesis.

    Updates the hypothesis entry in-place by appending trial_id to its
    'trials' list.

    Raises:
        ValueError: if hypothesis_id not found.
    """
    entries = _load_all()
    target_entry = None

    for entry in entries:
        if entry.get("hypothesis_id") == hypothesis_id:
            target_entry = entry
            break

    if target_entry is None:
        raise ValueError(f"Hypothesis '{hypothesis_id}' not found.")

    if "trials" not in target_entry:
        target_entry["trials"] = []

    if trial_id not in target_entry["trials"]:
        target_entry["trials"].append(trial_id)

    # Rewrite the file (JSONL is append-only but we need to update in place)
    with open(HYPOTHESES_FILE, "w") as f:
        for entry in entries:
            f.write(json.dumps(entry) + "\n")