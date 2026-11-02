"""seed_dedupe.py — US-206 (EPIC-017 Phase 2) mechanism-based seed dedupe.

Dedupe every new seed against the trials ledger by MECHANISM, not by name, so
the same economic mechanism is not silently re-run under a new label. A
near-duplicate mechanism is linked to its prior trial and requires a
pre-registered ``variant_argument`` before it may proceed.

Mechanism identity: the seed's ``primitives`` list (the structured entry-
primitive modules declared in the US-202 frontmatter) is the canonical encoding
of the mechanism, NOT the ``hypothesis_id`` or ``description`` string. A
"renamed re-skin" therefore keeps its primitive signatures and is caught by
primitive-set Jaccard similarity.

A prior mechanism is only a DUPLICATE risk if it has actually been TRIALED
(its ``hypothesis_id`` appears in the trials ledger). Hypothesis notes that were
never run do not block a new seed.

```python
check = dedupe_check(new_seed)
if check["duplicate"]:
    # → link to check["prior"]["hypothesis_id"]; require a non-empty
    #   `variant_argument` (pre-registered variant) before re-running.
```
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

try:
    import trials_ledger as _ledger
except ImportError:  # pragma: no cover
    _ledger = None

try:
    import hypothesis_register as _register
except ImportError:  # pragma: no cover
    _register = None

# Jaccard similarity at/above which two primitive-sets are a near-duplicate
# mechanism. 0.5 means "share >= half of the union of primitives".
MECHANISM_SIMILARITY_THRESHOLD = 0.5


def _normalize_tokens(values) -> frozenset:
    """Normalize each primitive to an alphanumeric token set."""
    out = set()
    for v in values or []:
        s = re.sub(r"[^a-z0-9]+", " ", str(v).lower()).strip()
        if s:
            out.add(s)
    return frozenset(out)


def mechanism_signature(entry: Dict[str, Any]) -> frozenset:
    """The mechanism signature = normalized set of primitives (name-agnostic)."""
    return _normalize_tokens(entry.get("primitives"))


def _jaccard(a: frozenset, b: frozenset) -> float:
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def _trialed_hypothesis_ids(ledger) -> set:
    return {t.get("hypothesis_id") for t in ledger if t.get("hypothesis_id")}


def find_prior_mechanism(
    entry: Dict[str, Any],
    hypotheses: Optional[List[Dict[str, Any]]] = None,
    ledger: Optional[List[Dict[str, Any]]] = None,
    threshold: float = MECHANISM_SIMILARITY_THRESHOLD,
) -> Optional[Dict[str, Any]]:
    """Return the best prior TRIALED hypothesis with a near-duplicate mechanism.

    Returns None when there is no near-duplicate mechanism among previously
    trialed hypotheses. The returned dict carries ``hypothesis_id``,
    ``similarity``, ``shared_primitives`` and ``prior_primitives`` so intake can
    LINK the new seed to its prior trial.
    """
    sig = mechanism_signature(entry)
    if not sig:
        return None

    if ledger is None:
        ledger = _ledger.read_all() if _ledger is not None else []
    trialed = _trialed_hypothesis_ids(ledger)
    if not trialed:
        return None

    if hypotheses is None:
        hypotheses = _register.list_all() if _register is not None else []

    best = None
    for h in hypotheses:
        hid = h.get("hypothesis_id")
        if not hid or hid == entry.get("hypothesis_id"):
            continue
        if hid not in trialed:
            continue  # only flag against mechanisms that actually ran
        psig = mechanism_signature(h)
        if not psig:
            continue
        sim = _jaccard(sig, psig)
        if sim >= threshold and (best is None or sim > best["similarity"]):
            best = {
                "hypothesis_id": hid,
                "similarity": sim,
                "shared_primitives": sorted(sig & psig),
                "prior_primitives": sorted(psig),
            }
    return best


def dedupe_check(
    entry: Dict[str, Any],
    hypotheses: Optional[List[Dict[str, Any]]] = None,
    ledger: Optional[List[Dict[str, Any]]] = None,
    threshold: float = MECHANISM_SIMILARITY_THRESHOLD,
) -> Dict[str, Any]:
    """US-206 dedupe verdict for a new seed.

    Returns ``{duplicate, prior, requires_variant_argument,
    variant_argument_present}``. When ``duplicate`` is True the caller must LINK
    to ``prior["hypothesis_id"]`` and, unless a ``variant_argument`` is already
    present, REQUIRE a pre-registered variant argument before re-running.
    """
    prior = find_prior_mechanism(entry, hypotheses=hypotheses,
                                 ledger=ledger, threshold=threshold)
    if prior is None:
        return {
            "duplicate": False,
            "prior": None,
            "requires_variant_argument": False,
            "variant_argument_present": False,
        }
    has_variant = bool((entry.get("variant_argument") or "").strip())
    return {
        "duplicate": True,
        "prior": prior,
        "requires_variant_argument": not has_variant,
        "variant_argument_present": has_variant,
    }


if __name__ == "__main__":
    # No-op demo (requires a populated ledger); real behaviour is covered by
    # tests/test_seed_dedupe.py.
    print("seed_dedupe — see tests/test_seed_dedupe.py for mechanism-dedupe checks")