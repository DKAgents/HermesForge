"""
Hypothesis Register Skill Module (PROP-001).

Pre-register hypotheses before backtests. Every hypothesis gets a note with
falsification criteria and expected effect size BEFORE any backtest runs.
The trials ledger records the hypothesis_id.

Seed pool: HYP-01 through HYP-10 from PROP-001.

Storage: append-only JSONL at /root/HermesForge/data/gauntlet/hypotheses.jsonl
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


HYPOTHESES_FILE = os.path.join(
    os.path.dirname(__file__), "..", "..", "data", "gauntlet", "hypotheses.jsonl"
)
# Resolve to absolute path
HYPOTHESES_FILE = os.path.abspath(HYPOTHESES_FILE)

# Seed pool from PROP-001
SEED_POOL: List[Dict[str, Any]] = [
    {
        "hypothesis_id": "HYP-01",
        "description": "Funding-extreme unwind. Fade crowded positioning when "
                       "funding >95th %ile + OI still rising.",
        "falsification_criteria": "Sharpe < 0.5 over 200+ trades, or edge "
                                   "disappears after funding < 80th %ile.",
        "expected_effect_size_bps": 15,
        "tier": "T3",
        "venue": "hyperliquid",
        "timeframe": "1h-6h",
        "primitives": ["funding_z", "oi_trend", "regime"],
        "likeliest_killer": "G6",
    },
    {
        "hypothesis_id": "HYP-02",
        "description": "OI-confirmed breakout. Range breakouts only in "
                       "price↑/OI↑ quadrant (new money).",
        "falsification_criteria": "Win rate < 45% or PF < 1.2 in quadrant 1 only.",
        "expected_effect_size_bps": 20,
        "tier": "T2",
        "venue": "hyperliquid",
        "timeframe": "5m",
        "primitives": ["oi_quadrant", "range_breakout"],
        "likeliest_killer": "G3",
    },
    {
        "hypothesis_id": "HYP-03",
        "description": "Cascade exhaustion. After liquidation cascade, first "
                       "retrace tradeable opposite direction.",
        "falsification_criteria": "No significant return anomaly in the 30min "
                                   "following cascade events (p > 0.10).",
        "expected_effect_size_bps": 25,
        "tier": "T3",
        "venue": "hyperliquid",
        "timeframe": "5m-15m",
        "primitives": ["liquidation_cascade", "retrace"],
        "likeliest_killer": "G2",
    },
    {
        "hypothesis_id": "HYP-04",
        "description": "Settlement-hour drift. Directional drift around hourly "
                       "funding settlement boundary.",
        "falsification_criteria": "Median return in settlement window not "
                                   "significantly different from non-settlement "
                                   "windows (p > 0.05).",
        "expected_effect_size_bps": 10,
        "tier": "T3",
        "venue": "hyperliquid",
        "timeframe": "5m",
        "primitives": ["funding_z", "settlement_countdown"],
        "likeliest_killer": "G0",
    },
    {
        "hypothesis_id": "HYP-05",
        "description": "Cross-sectional perp momentum. Long top-decile / short "
                       "bottom-decile 7-day return with funding filter.",
        "falsification_criteria": "Long-short spread not significantly > 0 after "
                                   "costs across 3 consecutive rolling windows.",
        "expected_effect_size_bps": 30,
        "tier": "T1",
        "venue": "hyperliquid",
        "timeframe": "1d",
        "primitives": ["momentum_7d", "funding_filter"],
        "likeliest_killer": "G6",
    },
    {
        "hypothesis_id": "HYP-06",
        "description": "BTC-beta residual reversion. Alt residual against "
                       "BTC-beta-implied price, reverts when >2σ.",
        "falsification_criteria": "PF < 1.1 after accounting for two-leg "
                                   "round-trip costs.",
        "expected_effect_size_bps": 18,
        "tier": "T2",
        "venue": "hyperliquid",
        "timeframe": "5m-4h",
        "primitives": ["btc_beta", "residual_reversion"],
        "likeliest_killer": "G0",
    },
    {
        "hypothesis_id": "HYP-07",
        "description": "Asia-range / EU-continuation. Asia range break, "
                       "EU-confirmed, carried through US open.",
        "falsification_criteria": "Session-conditional PF < 1.0 when EU "
                                   "confirmation missing.",
        "expected_effect_size_bps": 12,
        "tier": "T2",
        "venue": "hyperliquid",
        "timeframe": "5m-1h",
        "primitives": ["asia_range", "eu_continuation", "session"],
        "likeliest_killer": "G5",
    },
    {
        "hypothesis_id": "HYP-08",
        "description": "Oracle-mark dislocation. Mark vs CEX-weighted-median "
                       "oracle divergence snap-back.",
        "falsification_criteria": "Dislocation magnitude insufficient to cover "
                                   "fees at 90th percentile size.",
        "expected_effect_size_bps": 8,
        "tier": "T3",
        "venue": "hyperliquid",
        "timeframe": "5m",
        "primitives": ["oracle_divergence", "snap_back"],
        "likeliest_killer": "G0",
    },
    {
        "hypothesis_id": "HYP-09",
        "description": "Volatility compression expansion. ATR-percentile <20th "
                       "into directional expansion on structural break.",
        "falsification_criteria": "False breakout rate > 60% or post-expansion "
                                   "drift < 1.5x ATR.",
        "expected_effect_size_bps": 22,
        "tier": "T1",
        "venue": "hyperliquid",
        "timeframe": "1h-4h",
        "primitives": ["atr_percentile", "vol_expansion", "regime"],
        "likeliest_killer": "G4",
    },
    {
        "hypothesis_id": "HYP-10",
        "description": "New-listing drift. Newly listed perps, persistent "
                       "funding skew + directional drift.",
        "falsification_criteria": "Drift not significantly different from zero "
                                   "for listings after 2026-Q1 (p > 0.05).",
        "expected_effect_size_bps": 35,
        "tier": "T1",
        "venue": "hyperliquid",
        "timeframe": "4h-1d",
        "primitives": ["new_listing", "funding_skew", "drift"],
        "likeliest_killer": "G5",
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

def register(
    hypothesis_id: str,
    description: str,
    falsification_criteria: str,
    expected_effect_size_bps: float,
    tier: str,
    venue: str,
    timeframe: str,
    primitives: List[str],
) -> Dict[str, Any]:
    """
    Register a new hypothesis.

    Args:
        hypothesis_id: unique identifier (e.g., 'HYP-11').
        description: plain-language description of the hypothesis.
        falsification_criteria: measurable criteria that would falsify it.
        expected_effect_size_bps: expected gross edge in basis points.
        tier: discovery tier (T0-T4).
        venue: exchange/venue.
        timeframe: signal timeframe (e.g., '5m', '1h').
        primitives: list of entry primitive names used.

    Returns:
        The registered entry dict with timestamp.

    Raises:
        ValueError: if hypothesis_id already exists.
    """
    if _entry_exists(hypothesis_id):
        raise ValueError(
            f"Hypothesis '{hypothesis_id}' already registered. "
            f"Use get('{hypothesis_id}') to retrieve it."
        )

    timestamp = datetime.now(timezone.utc).isoformat()

    entry = {
        "hypothesis_id": hypothesis_id,
        "description": description,
        "falsification_criteria": falsification_criteria,
        "expected_effect_size_bps": expected_effect_size_bps,
        "tier": tier,
        "venue": venue,
        "timeframe": timeframe,
        "primitives": primitives,
        "registered_at": timestamp,
        "trials": [],
        "status": "registered",
    }

    _write_entry(entry)
    return entry


def pre_register_from_seed_pool() -> List[Dict[str, Any]]:
    """
    Register all 10 hypotheses from the PROP-001 seed pool if not already
    registered.

    Returns:
        List of entries that were actually registered (skips duplicates).
    """
    registered = []
    for entry in SEED_POOL:
        hid = entry["hypothesis_id"]
        if _entry_exists(hid):
            continue
        result = register(
            hypothesis_id=hid,
            description=entry["description"],
            falsification_criteria=entry["falsification_criteria"],
            expected_effect_size_bps=entry["expected_effect_size_bps"],
            tier=entry["tier"],
            venue=entry["venue"],
            timeframe=entry["timeframe"],
            primitives=entry["primitives"],
        )
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
    target_idx = None
    target_entry = None

    for i, entry in enumerate(entries):
        if entry.get("hypothesis_id") == hypothesis_id:
            target_idx = i
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
        for i, entry in enumerate(entries):
            f.write(json.dumps(entry) + "\n")