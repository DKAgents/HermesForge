"""Tests for seed_dedupe.py — US-206 (mechanism dedupe vs trials ledger)."""

import sys
import os
import tempfile
import shutil

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest  # noqa: E402

import hypothesis_register as hr  # noqa: E402
import trials_ledger as tl  # noqa: E402
import seed_dedupe as sd  # noqa: E402


@pytest.fixture(autouse=True)
def temp_ledgers(monkeypatch):
    tmpdir = tempfile.mkdtemp()
    monkeypatch.setattr(hr, "HYPOTHESES_FILE",
                        os.path.join(tmpdir, "hypotheses.jsonl"))
    monkeypatch.setattr(tl, "LEDGER_PATH",
                        __import__("pathlib").Path(tmpdir) / "trials.jsonl")
    yield tmpdir
    shutil.rmtree(tmpdir, ignore_errors=True)


def _priors_entry(hid, primitives):
    return {
        "hypothesis_id": hid, "source": "human", "venue": "hyperliquid",
        "instruments": ["BTC"], "horizon": "4h-48h",
        "entry_logic": "funding fade", "exit_logic": "convergence",
        "expected_gross_edge_bps": 15, "cost_hurdle_bps": 45,
        "data_dependencies": ["hl:fundingHistory"],
        "counterparty": "late retail longs", "execution_mode": "taker",
        "falsification_criteria": "sharpe<0.5", "primitives": primitives,
    }


def _trial(hid):
    tl.increment_trial(hypothesis_id=hid, param_hash="p", universe_hash="u",
                       period_start="2026-01-01", period_end="2026-01-31",
                       result={"avg_r": -0.5, "pf": 0.8})


def test_renamed_reskin_of_failed_mechanism_is_flagged():
    # Prior mechanism (funding unwind) — trialed and FAILED.
    hr.register(_priors_entry("HYP-PRIOR", ["funding_z", "oi_trend", "regime"]))
    _trial("HYP-PRIOR")

    # Renamed re-skin of the same mechanism (new id, same primitives minus one).
    reskin = _priors_entry("HYP-RESKIN", ["funding_z", "oi_trend"])
    reskin["description"] = "crowded-funding fade"  # different label, same thing

    check = sd.dedupe_check(reskin)
    assert check["duplicate"] is True
    assert check["prior"]["hypothesis_id"] == "HYP-PRIOR"
    assert check["requires_variant_argument"] is True  # no variant argument
    assert check["prior"]["similarity"] >= 0.5


def test_distinct_mechanism_not_flagged():
    hr.register(_priors_entry("HYP-PRIOR", ["funding_z", "oi_trend", "regime"]))
    _trial("HYP-PRIOR")

    fresh = _priors_entry("HYP-FRESH", ["new_listing", "drift"])
    check = sd.dedupe_check(fresh)
    assert check["duplicate"] is False
    assert check["prior"] is None


def test_untrialed_mechanism_does_not_block():
    # A hypothesis registered but NEVER run (no ledger trial) must not block.
    hr.register(_priors_entry("HYP-UNRUN", ["funding_z", "oi_trend", "regime"]))
    fresh = _priors_entry("HYP-NEW", ["funding_z", "oi_trend"])
    check = sd.dedupe_check(fresh)
    assert check["duplicate"] is False


def test_variant_argument_satisfies_pre_registration():
    hr.register(_priors_entry("HYP-PRIOR", ["funding_z", "oi_trend", "regime"]))
    _trial("HYP-PRIOR")

    reskin = _priors_entry("HYP-VARIANT", ["funding_z", "oi_trend"])
    reskin["variant_argument"] = "new short-horizon variant with maker fills"
    check = sd.dedupe_check(reskin)
    assert check["duplicate"] is True
    assert check["requires_variant_argument"] is False
    assert check["variant_argument_present"] is True


if __name__ == "__main__":
    # Fallback runner for environments without pytest — constructs a temporary
    # ledger via the fixture logic manually.
    print("run with pytest: `python -m pytest tests/test_seed_dedupe.py`")