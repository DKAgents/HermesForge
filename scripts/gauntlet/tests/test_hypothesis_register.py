"""
Tests for hypothesis_register.py — HR1 through HR8 (legacy) + US-202 intake
validation (HI1 through HI6).
"""

import sys
import os
import tempfile
import shutil

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest

# We need to patch the HYPOTHESES_FILE to a temp location for testing.
# Import the module and override.
import hypothesis_register as hr_mod  # noqa: E402


@pytest.fixture(autouse=True)
def temp_hypotheses_file(monkeypatch):
    """Overwrite HYPOTHESES_FILE with a temp file for isolation."""
    tmpdir = tempfile.mkdtemp()
    tmpfile = os.path.join(tmpdir, "hypotheses.jsonl")
    monkeypatch.setattr(hr_mod, "HYPOTHESES_FILE", tmpfile)
    yield tmpfile
    shutil.rmtree(tmpdir, ignore_errors=True)


def _full_entry(hid="TEST-H01", **overrides):
    """A complete, valid US-202 frontmatter (all 14 required fields)."""
    entry = {
        "hypothesis_id": hid,
        "source": "human",
        "venue": "hyperliquid",
        "instruments": ["BTC", "ETH"],
        "horizon": "4h-48h",
        "entry_logic": "Enter when the funding-carry signal is extreme.",
        "exit_logic": "Exit on convergence or a 1x ATR stop.",
        "expected_gross_edge_bps": 15.0,
        "cost_hurdle_bps": 45.0,
        "data_dependencies": ["hl:fundingHistory"],
        "counterparty": "Late retail longs accepting negative funding carry.",
        "execution_mode": "taker",
        "falsification_criteria": "Sharpe < 0.5 over 100 trades",
        "primitives": ["funding_z", "oi_trend"],
        "description": "Test hypothesis for unit tests.",
        "tier": "T2",
        "timeframe": "5m",
    }
    entry.update(overrides)
    return entry


def _make_hypothesis(hid="TEST-H01"):
    return hr_mod.register(_full_entry(hid))


# ---------------------------------------------------------------------------
# HR1: register creates entry
# ---------------------------------------------------------------------------

def test_HR1_register_creates_entry():
    entry = _make_hypothesis("HYP-11")
    assert entry["hypothesis_id"] == "HYP-11"
    assert entry["description"] == "Test hypothesis for unit tests."
    assert entry["falsification_criteria"] == "Sharpe < 0.5 over 100 trades"
    assert entry["expected_gross_edge_bps"] == 15.0
    assert entry["tier"] == "T2"
    assert entry["venue"] == "hyperliquid"
    assert entry["timeframe"] == "5m"
    assert entry["horizon"] == "4h-48h"
    assert entry["source"] == "human"
    assert entry["execution_mode"] == "taker"
    assert "counterparty" in entry
    assert "BTC" in entry["instruments"]
    assert "funding_z" in entry["primitives"]
    assert entry["registered_at"]
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
        hr_mod.register(_full_entry("HYP-DUP1"))


# ---------------------------------------------------------------------------
# HR3: list_all returns entries
# ---------------------------------------------------------------------------

def test_HR3_list_all_returns_entries():
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
    registered = hr_mod.pre_register_from_seed_pool()
    assert len(registered) == 10, f"Expected 10, got {len(registered)}"

    ids = sorted([e["hypothesis_id"] for e in registered])
    expected = [f"HYP-{i:02d}" for i in range(1, 11)]
    assert ids == expected, f"Got IDs: {ids}"

    # Each seed-pool entry must already satisfy validate_frontmatter (no
    # regression — the full 14-field corpus still registers).
    for entry in hr_mod.SEED_POOL:
        ok, errors = hr_mod.validate_frontmatter(entry)
        assert ok, f"{entry['hypothesis_id']} fails frontmatter: {errors}"

    # Each registered entry carries the canonical fields.
    for entry in registered:
        assert entry["status"] == "registered"
        assert "counterparty" in entry and entry["counterparty"]
        assert entry["venue"] == "hyperliquid"

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

    for field in ["hypothesis_id", "description", "falsification_criteria",
                  "expected_gross_edge_bps", "tier", "venue", "timeframe",
                  "primitives", "registered_at", "trials", "status",
                  "source", "instruments", "horizon", "entry_logic",
                  "exit_logic", "cost_hurdle_bps", "data_dependencies",
                  "counterparty", "execution_mode"]:
        assert field in entry, f"Missing required field: {field}"

    assert isinstance(entry["expected_gross_edge_bps"], (int, float))
    assert isinstance(entry["primitives"], list)
    assert isinstance(entry["trials"], list)
    assert len(entry["counterparty"]) > 0


# ---------------------------------------------------------------------------
# US-202 — intake validation (HI1..HI6)
# ---------------------------------------------------------------------------

def test_HI1_missing_counterparty_rejected_and_writes_nothing():
    before = hr_mod.list_all()
    seed = _full_entry("HYP-NO-CPTY")
    del seed["counterparty"]

    with pytest.raises(ValueError, match="counterparty"):
        hr_mod.register(seed)

    # Writes NOTHING (rejected at intake, not a later gate).
    after = hr_mod.list_all()
    assert len(after) == len(before)
    assert hr_mod.get("HYP-NO-CPTY") is None


def test_HI2_web_source_empty_counterparty_rejected():
    seed = _full_entry("HYP-WEB-EMPTY", source="web", counterparty="")
    ok, errors = hr_mod.validate_frontmatter(seed)
    assert not ok
    assert any("counterparty" in e for e in errors)


def test_HI3_validate_frontmatter_reports_per_field_reasons():
    # A seed missing several fields surfaces every defect (not a bare boolean).
    seed = {}
    ok, errors = hr_mod.validate_frontmatter(seed)
    assert not ok
    missing = [e for e in errors if e.startswith("missing required field")]
    assert len(missing) == 14  # all 14 fields absent


def test_HI4_reject_invalid_enum_and_venue_and_numeric():
    seed = _full_entry("HYP-BAD")
    bad = dict(seed, source="telegram", execution_mode="market",
               venue="binance", expected_gross_edge_bps=float("nan"),
               cost_hurdle_bps="a lot", instruments=[])
    ok, errors = hr_mod.validate_frontmatter(bad)
    assert not ok
    joined = "; ".join(errors)
    assert "source must be one of" in joined
    assert "execution_mode must be one of" in joined
    assert "venue must be 'hyperliquid'" in joined
    assert "'expected_gross_edge_bps' must be a finite number" in joined
    assert "'cost_hurdle_bps' must be a finite number" in joined
    assert "instruments" in joined


def test_HI5_full_seed_pool_entries_pass_validation():
    # No regression: every pre-authored seed passes the new contract.
    for entry in hr_mod.SEED_POOL:
        ok, errors = hr_mod.validate_frontmatter(entry)
        assert ok, f"{entry['hypothesis_id']}: {errors}"


def test_HI6_full_14_field_entry_registers():
    entry = _make_hypothesis("HYP-OK14")
    assert entry["status"] == "registered"
    assert hr_mod.get("HYP-OK14") is not None