"""Tests for ledger_prior.py + its wiring (US-215, EPIC-017 Phase 5).

Covers:
  - prior_for avoids a mechanism that failed G4/G5 (post-mortem record),
    including a renamed/re-skin with underscores/hyphens/spaces.
  - prior_for prefers a mechanism that passed G3+ and stands in Active/Live.
  - prior_for stays neutral for an unrelated mechanism.
  - the real repo's canonical G4 failure (cross-sectional momentum) is avoided.
  - the two integration mappers (edge_factory + scout) turn a G4-failed
    mechanism into an "avoid" verdict BEFORE proposing.
"""

import os
import shutil
import sys
import tempfile
from pathlib import Path

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))            # scripts/gauntlet
sys.path.insert(0, os.path.join(_HERE, "..", "..", "validation"))  # scripts/validation

import pytest  # noqa: E402

import ledger_prior as lp  # noqa: E402
import edge_factory as ef  # noqa: E402
import scout_x_strategies as scout  # noqa: E402


def _write_postmortem(pm_dir: Path, strategy_class: str, gate: str,
                      strategy_id: str = "STR-x") -> None:
    pm_dir.mkdir(parents=True, exist_ok=True)
    (pm_dir / f"{strategy_id}.md").write_text(
        f"---\ntype: postmortem\nstrategy_id: {strategy_id}\n"
        f"strategy_class: {strategy_class}\nsignal_class: systematic\n"
        f"gate: {gate}\nstatus: failed\n---\n\n# {strategy_id}\n"
    )


def _write_active(reg_dir: Path, sid: str) -> None:
    (reg_dir / "Active").mkdir(parents=True, exist_ok=True)
    (reg_dir / "Active" / f"{sid}.md").write_text(
        f"---\nid: {sid}\ntype: strategy\n---\n"
    )


@pytest.fixture()
def temp_priors(monkeypatch):
    tmpdir = Path(tempfile.mkdtemp())
    pm_dir = tmpdir / "PostMortems"
    reg_dir = tmpdir / "strategies"
    (reg_dir / "Active").mkdir(parents=True)
    (reg_dir / "Live").mkdir(parents=True)
    monkeypatch.setattr(lp, "POSTMORTEM_DIR", pm_dir)
    monkeypatch.setattr(lp, "POSTMORTEM_INDEX", pm_dir / "_INDEX.md")
    monkeypatch.setattr(lp, "REGISTRY", reg_dir)
    yield tmpdir
    shutil.rmtree(tmpdir, ignore_errors=True)


# ── prior_for unit behaviour ──────────────────────────────────────────────

def test_g4_failed_mechanism_is_avoided(temp_priors):
    _write_postmortem(temp_priors / "PostMortems",
                      "cross-sectional-momentum", "G4")
    prior = lp.prior_for({"description": "cross-sectional momentum long top decile"})
    assert prior.verdict == "avoid"
    assert prior.gate == "G4"
    assert prior.requires_variant is True
    assert prior.matched == "cross-sectional-momentum"


def test_g5_failed_mechanism_is_avoided(temp_priors):
    _write_postmortem(temp_priors / "PostMortems", "funding-carry", "G5")
    prior = lp.prior_for({"primitives": ["funding_carry"],
                          "description": "funding carry directional fade"})
    assert prior.verdict == "avoid"
    assert prior.gate == "G5"


def test_reskin_with_underscores_still_avoided(temp_priors):
    # Same mechanism re-labelled with underscores + spaces must still match.
    _write_postmortem(temp_priors / "PostMortems",
                      "cross-sectional-momentum", "G4")
    prior = lp.prior_for({
        "primitives": ["cross_sectional_momentum", "funding_filter"],
        "description": "cross sectional momentum",
    })
    assert prior.verdict == "avoid"


def test_standing_g3_mechanism_is_preferred(temp_priors):
    _write_active(temp_priors / "strategies", "STR-PASS")
    prior = lp.prior_for({"strategy_id": "STR-PASS"})
    assert prior.verdict == "prefer"
    assert prior.requires_variant is False


def test_unrelated_mechanism_is_neutral(temp_priors):
    _write_postmortem(temp_priors / "PostMortems",
                      "cross-sectional-momentum", "G4")
    prior = lp.prior_for({"description": "volatility carry term structure"})
    assert prior.verdict == "neutral"
    assert prior.requires_variant is False


def test_g3_failure_is_not_avoided(temp_priors):
    # A G3 (execution-realism) post-mortem is NOT in AVOID_GATES, and its
    # signal class (systematic) is NOT blocked, so it must fall through to
    # neutral (or prefer) — never "avoid".
    _write_postmortem(temp_priors / "PostMortems",
                      "funding-carry-directional", "G3")
    prior = lp.prior_for({"description": "funding carry directional fade"})
    assert prior.verdict in ("neutral", "prefer")


def test_g3_liquidity_sweep_is_avoided_via_blocked_class(temp_priors):
    # A liquidity-sweep seed is avoided at the US-191 intake gate (blocked
    # signal class ict-smc) regardless of the post-mortem gate being G3.
    _write_postmortem(temp_priors / "PostMortems", "liquidity-sweep", "G3")
    prior = lp.prior_for({"description": "liquidity sweep reversal"})
    assert prior.verdict == "avoid"
    assert prior.gate == "G0"


# ── Real repo integration (the canonical US-216 G4 record) ───────────────

def test_real_repo_cross_sectional_momentum_is_avoided():
    # No monkeypatch: run against the real post-mortem index.
    prior = lp.prior_for({
        "primitives": ["cross_sectional_momentum"],
        "description": "cross-sectional momentum long top decile",
    })
    assert prior.verdict == "avoid"
    assert prior.gate == "G4"


# ── Wiring: edge_factory + scout mappers reject G4/G5 before proposing ───

def test_edge_factory_mapper_rejects_g4(temp_priors):
    _write_postmortem(temp_priors / "PostMortems",
                      "cross-sectional-momentum", "G4")
    rules = {
        "entry_conditions": ["Momentum / Trend following"],
        "indicators": [],
        "source_title": "Cross-Sectional Momentum in Crypto",
        "snippet": "long the top decile by cross-sectional momentum",
    }
    prior = ef._prior_for_candidate(rules)
    assert prior.verdict == "avoid"
    assert prior.gate == "G4"


def test_scout_mapper_rejects_g4(temp_priors):
    _write_postmortem(temp_priors / "PostMortems",
                      "cross-sectional-momentum", "G4")
    candidate = {
        "title": "Cross-sectional momentum factor",
        "thesis": "long the top decile cross-sectional momentum",
        "source_text": "cross sectional momentum ranking",
        "spec": {"entry": ["rank by cross-sectional momentum"],
                 "exit": [], "results": {}, "timeframe": None,
                 "instruments": []},
    }
    prior = scout._prior_for_candidate(candidate)
    assert prior["verdict"] == "avoid"
    assert prior["gate"] == "G4"


if __name__ == "__main__":
    print("run with pytest: `python -m pytest tests/test_ledger_prior.py`")