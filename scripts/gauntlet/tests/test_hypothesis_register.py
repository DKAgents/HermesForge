"""
Tests for hypothesis_register.py — HR1 through HR8.
"""

import sys
import os
import tempfile
import shutil

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import json
import pytest

# We need to patch the HYPOTHESES_FILE to a temp location for testing.
# Import the module and override.
import hypothesis_register as hr_mod


@pytest.fixture(autouse=True)
def temp_hypotheses_file(monkeypatch):
    """Overwrite HYPOTHESES_FILE with a temp file for isolation."""
    tmpdir = tempfile.mkdtemp()
    tmpfile = os.path.join(tmpdir, "hypotheses.jsonl")
    monkeypatch.setattr(hr_mod, "HYPOTHESES_FILE", tmpfile)
    yield tmpfile
    shutil.rmtree(tmpdir, ignore_errors=True)


def _make_hypothesis(hid="TEST-H01"):
    """Create a minimal hypothesis entry for testing."""
    return hr_mod.register(
        hypothesis_id=hid,
        description="Test hypothesis for unit tests.",
        falsification_criteria="Sharpe < 0.5 over 100 trades",
        expected_effect_size_bps=15.0,
        tier="T2",
        venue="hyperliquid",
        timeframe="5m",
        primitives=["momentum", "volume"],
    )


# ---------------------------------------------------------------------------
# HR1: register creates entry
# ---------------------------------------------------------------------------

def test_HR1_register_creates_entry():
    entry = _make_hypothesis("HYP-11")
    assert entry["hypothesis_id"] == "HYP-11"
    assert entry["description"] == "Test hypothesis for unit tests."
    assert entry["falsification_criteria"] == "Sharpe < 0.5 over 100 trades"
    assert entry["expected_effect_size_bps"] == 15.0
    assert entry["tier"] == "T2"
    assert entry["venue"] == "hyperliquid"
    assert entry["timeframe"] == "5m"
    assert "momentum" in entry["primitives"]
    assert "volume" in entry["primitives"]
    assert "registered_at" in entry
    assert entry["status"] == "registered"
    assert entry["trials"] == []

    # Verify it was persisted
    found = hr_mod.get("HYP-11")
    assert found is not None
    assert found["hypothesis_id"] == "HYP-11"


# ---------------------------------------------------------------------------
# HR2: duplicate id refused
# ---------------------------------------------------------------------------

def test_HR2_duplicate_id_refused():
    _make_hypothesis("HYP-DUP1")

    with pytest.raises(ValueError, match="already registered"):
        hr_mod.register(
            hypothesis_id="HYP-DUP1",
            description="Duplicate attempt",
            falsification_criteria="Should fail",
            expected_effect_size_bps=10.0,
            tier="T1",
            venue="hyperliquid",
            timeframe="1h",
            primitives=["test"],
        )


# ---------------------------------------------------------------------------
# HR3: list_all returns entries
# ---------------------------------------------------------------------------

def test_HR3_list_all_returns_entries():
    # Start with clean temp file (fixture handles this)
    _make_hypothesis("HYP-A")
    _make_hypothesis("HYP-B")
    _make_hypothesis("HYP-C")

    entries = hr_mod.list_all()
    assert len(entries) == 3
    ids = [e["hypothesis_id"] for e in entries]
    assert "HYP-A" in ids
    assert "HYP-B" in ids
    assert "HYP-C" in ids


# ---------------------------------------------------------------------------
# HR4: get finds existing entry
# ---------------------------------------------------------------------------

def test_HR4_get_finds_existing():
    _make_hypothesis("HYP-FIND")

    entry = hr_mod.get("HYP-FIND")
    assert entry is not None
    assert entry["hypothesis_id"] == "HYP-FIND"
    assert entry["status"] == "registered"


# ---------------------------------------------------------------------------
# HR5: get returns None for missing
# ---------------------------------------------------------------------------

def test_HR5_get_returns_none_for_missing():
    result = hr_mod.get("NONEXISTENT")
    assert result is None


# ---------------------------------------------------------------------------
# HR6: pre_register_from_seed_pool creates 10 entries
# ---------------------------------------------------------------------------

def test_HR6_pre_register_from_seed_pool_creates_10():
    # Start with clean temp file (fixture handles this)
    registered = hr_mod.pre_register_from_seed_pool()
    assert len(registered) == 10, f"Expected 10, got {len(registered)}"

    # All should be HYP-01 through HYP-10
    ids = sorted([e["hypothesis_id"] for e in registered])
    expected = [f"HYP-{i:02d}" for i in range(1, 11)]
    assert ids == expected, f"Got IDs: {ids}"

    # Each should have all required fields
    for entry in registered:
        assert "hypothesis_id" in entry
        assert "description" in entry
        assert "falsification_criteria" in entry
        assert "expected_effect_size_bps" in entry
        assert "tier" in entry
        assert "venue" in entry
        assert "timeframe" in entry
        assert "primitives" in entry
        assert "registered_at" in entry
        assert "trials" in entry
        assert entry["status"] == "registered"
        assert isinstance(entry["primitives"], list)
        assert len(entry["primitives"]) > 0

    # Verify with list_all
    all_entries = hr_mod.list_all()
    assert len(all_entries) == 10

    # Running again should register 0 new entries
    registered2 = hr_mod.pre_register_from_seed_pool()
    assert len(registered2) == 0
    assert len(hr_mod.list_all()) == 10


# ---------------------------------------------------------------------------
# HR7: link_trial updates entry
# ---------------------------------------------------------------------------

def test_HR7_link_trial_updates_entry():
    _make_hypothesis("HYP-LINK")

    hr_mod.link_trial("HYP-LINK", "TRIAL-001")
    entry = hr_mod.get("HYP-LINK")
    assert "TRIAL-001" in entry["trials"]

    # Link another trial
    hr_mod.link_trial("HYP-LINK", "TRIAL-002")
    entry = hr_mod.get("HYP-LINK")
    assert "TRIAL-001" in entry["trials"]
    assert "TRIAL-002" in entry["trials"]
    assert len(entry["trials"]) == 2

    # Duplicate trial id should not be added twice
    hr_mod.link_trial("HYP-LINK", "TRIAL-001")
    entry = hr_mod.get("HYP-LINK")
    assert entry["trials"].count("TRIAL-001") == 1

    # Non-existent hypothesis should raise
    with pytest.raises(ValueError, match="not found"):
        hr_mod.link_trial("NONEXISTENT", "TRIAL-003")


# ---------------------------------------------------------------------------
# HR8: entry has all required fields
# ---------------------------------------------------------------------------

def test_HR8_entry_has_all_required_fields():
    entry = _make_hypothesis("HYP-FULL")

    required_fields = [
        "hypothesis_id",
        "description",
        "falsification_criteria",
        "expected_effect_size_bps",
        "tier",
        "venue",
        "timeframe",
        "primitives",
        "registered_at",
        "trials",
        "status",
    ]

    for field in required_fields:
        assert field in entry, f"Missing required field: {field}"

    # Type checks
    assert isinstance(entry["hypothesis_id"], str)
    assert isinstance(entry["description"], str)
    assert isinstance(entry["expected_effect_size_bps"], (int, float))
    assert isinstance(entry["primitives"], list)
    assert isinstance(entry["trials"], list)
    assert isinstance(entry["status"], str)

    # Non-empty strings for key fields
    assert len(entry["hypothesis_id"]) > 0
    assert len(entry["description"]) > 0
    assert len(entry["falsification_criteria"]) > 0
    assert len(entry["tier"]) > 0
    assert len(entry["venue"]) > 0
    assert len(entry["timeframe"]) > 0