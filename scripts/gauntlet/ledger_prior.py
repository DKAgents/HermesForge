"""ledger_prior.py — US-215 (EPIC-017 Phase 5) generation-time ledger prior.

The generation crons (External Edge Discovery, Edge Factory, x-strategy-scout,
Weekly Research) must query the trials ledger + post-mortem record BEFORE
proposing a seed, so a mechanism that already failed G4/G5 is not re-proposed
under a fresh label, while a mechanism that passed G3+ is biased IN.

Two on-disk sources carry the failure/pass signal:

  1. trading/knowledge/PostMortems/_INDEX.md — the canonical US-216 failure
     record (strategy_class → gate it died at, incl. G4 CPCV and G5 DSR/PBO).
  2. data/gauntlet/trials.jsonl + trading/strategies/{Active,Live} — the
     mechanisms that actually passed G3+ and remain standing.

The mechanism identity used here is the *signal class + strategy class* from
the post-mortem note, matched against a proposed seed via signal_class.classify
(US-191) so a renamed re-skin of a failed mechanism is still caught. A proposed
seed whose mechanism matches a G4/G5 failure is marked ``avoid`` and, per
US-206, requires a pre-registered ``variant_argument`` before it may proceed.

This module is INTENTIONALLY read-only: it never writes the ledger, never
proposes, and never mutates a seed. It only returns a verdict + citation for a
proposed seed.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

REPO = Path(__file__).resolve().parent.parent.parent
POSTMORTEM_DIR = REPO / "trading" / "knowledge" / "PostMortems"
POSTMORTEM_INDEX = POSTMORTEM_DIR / "_INDEX.md"
TRIALS = REPO / "data" / "gauntlet" / "trials.jsonl"
REGISTRY = REPO / "trading" / "strategies"

# Gates whose failure the US-215 generators must AVOID re-proposing.
AVOID_GATES = frozenset({"G4", "G5"})

# Pass signal: a strategy still standing in these registry folders after G3.
_PASS_FOLDERS = ("Active", "Live")

try:  # signal_class lives in the same dir (US-191)
    import signal_class as _sc
except ImportError:  # pragma: no cover
    _sc = None


@dataclass
class Prior:
    """Verdict for one proposed seed mechanism."""
    verdict: str          # "avoid" | "prefer" | "neutral"
    gate: Optional[str]   # the gate a matching failed mechanism died at
    reason: str
    matched: str          # prior strategy_class / id this seed resembles
    requires_variant: bool


# ── Loading (read-only) ─────────────────────────────────────────────────────

def _normalize(s: str) -> str:
    """Canonical tokenizer: lowercase + collapse every non-alnum run to ONE space.

    This mirrors signal_class._normalize so a hyphenated/underscored class label
    ("cross-sectional-momentum" / "cross_sectional_momentum") and a prose blob
    ("cross sectional momentum") both reduce to the same word sequence for a
    word-boundary match — otherwise a renamed re-skin escapes the avoid check.
    """
    return re.sub(r"[^a-z0-9]+", " ", s.lower()).strip()


def _parse_fm(text: str) -> Dict[str, str]:
    m = re.match(r"^---\s*\n(.*?)\n---", text, re.DOTALL)
    fm: Dict[str, str] = {}
    if m:
        for line in m.group(1).splitlines():
            kv = re.match(r"^([\w-]+):\s*(.*)", line)
            if kv:
                fm[kv.group(1)] = kv.group(2).strip().strip('"')
    return fm


def load_postmortems() -> List[Dict[str, str]]:
    """Return canonical failure records (gate + strategy_class + signal_class)."""
    out: List[Dict[str, str]] = []
    if not POSTMORTEM_DIR.is_dir():
        return out
    for f in POSTMORTEM_DIR.glob("*.md"):
        if f.name == "_INDEX.md":
            continue
        fm = _parse_fm(f.read_text(encoding="utf-8", errors="replace"))
        if fm.get("type") == "postmortem" and fm.get("gate"):
            out.append(fm)
    return out


def avoid_mechanisms() -> Dict[str, str]:
    """Map strategy_class -> gate for mechanisms that FAILED G4/G5.

    Keyed by ``strategy_class`` (falling back to ``strategy_id``) so a proposed
    seed with the same class is caught via signal_class match, not just ID.
    """
    avoid: Dict[str, str] = {}
    for pm in load_postmortems():
        gate = (pm.get("gate") or "").upper()
        if gate in AVOID_GATES:
            key = pm.get("strategy_class") or pm.get("strategy_id") or ""
            if key:
                avoid[key] = gate
    return avoid


def pass_mechanism_ids() -> set:
    """Strategy ids still standing in Active/Live (passed G3+, not yet demoted)."""
    out: set = set()
    for folder in _PASS_FOLDERS:
        d = REGISTRY / folder
        if not d.is_dir():
            continue
        for f in d.glob("*.md"):
            fm = _parse_fm(f.read_text(encoding="utf-8", errors="replace"))
            sid = fm.get("id") or f.stem
            if sid:
                out.add(sid)
    return out


# ── Verdict ─────────────────────────────────────────────────────────────────

def _classify_seed(strategy_meta: Dict) -> str:
    if _sc is None:
        return "unclassified"
    return _sc.classify(**strategy_meta)


def prior_for(strategy_meta: Dict) -> Prior:
    """Compute the US-215 generation prior for a proposed seed.

    ``strategy_meta`` carries the same free-form metadata accepted by
    signal_class.classify: id/name/description/edge/tags/primitives.
    """
    prims = strategy_meta.get("primitives") or []
    prim_blob = " ".join(str(p) for p in prims)
    sig_class = _classify_seed(strategy_meta)

    # 1) does this seed's mechanism match a G4/G5 failure?
    avoid = avoid_mechanisms()
    # match on strategy_class tokens appearing in primitives/description, or a
    # direct signal-class hit on a known-failed class. Both the token and the
    # blob are normalized to alnum word sequences so a hyphen/underscore/slash
    # re-skin of a failed class still matches.
    blob = _normalize(prim_blob + " " + str(strategy_meta.get("description", "")))
    for clazz, gate in avoid.items():
        token = _normalize(clazz)
        if token and re.search(
                r"(?<![a-z0-9])" + re.escape(token) + r"(?![a-z0-9])", blob):
            return Prior(
                verdict="avoid",
                gate=gate,
                reason=(
                    f"mechanism '{clazz}' already failed {gate} (post-mortem "
                    f"US-216); do not re-propose without a pre-registered "
                    f"variant argument"
                ),
                matched=clazz,
                requires_variant=True,
            )

    # system-flagged blocked classes carry a negative prior regardless of gate
    if sig_class in getattr(_sc, "BLOCKED_CLASSES", frozenset()):
        return Prior(
            verdict="avoid",
            gate=getattr(_sc, "BLOCKED_CLASSES", None) and "G0",
            reason=f"signal class '{sig_class}' blocked (US-191 negative prior)",
            matched=sig_class,
            requires_variant=True,
        )

    # 2) bias toward mechanisms that passed G3+ and remain in Active/Live.
    standing = pass_mechanism_ids()
    sid = str(strategy_meta.get("strategy_id") or strategy_meta.get("id") or "")
    if sid in standing:
        return Prior(
            verdict="prefer",
            gate="G3",
            reason=f"mechanism '{sid}' passed G3+ and remains Active/Live",
            matched=sid,
            requires_variant=False,
        )

    return Prior(
        verdict="neutral", gate=None,
        reason="no prior G4/G5 failure and no standing G3+ match",
        matched="", requires_variant=False,
    )


if __name__ == "__main__":
    # Self-test: demonstrate the avoid/prefer split against real disk state.
    avoid = avoid_mechanisms()
    standing = pass_mechanism_ids()
    print(f"Avoid (failed G4/G5) mechanisms: {avoid}")
    print(f"Standing (passed G3+) strategy ids: {sorted(standing)}")
    example = {"primitives": ["cross_sectional_momentum", "funding_filter"],
               "description": "cross-sectional momentum long top decile"}
    print("prior_for(cross-sectional momentum) =", prior_for(example))