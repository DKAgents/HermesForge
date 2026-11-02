"""Tests for universe_filter.py — US-203 (HL-only intake router)."""

import sys
import os
import tempfile
import shutil

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest  # noqa: E402

import universe_filter as uf  # noqa: E402

# A small deterministic HL universe for offline tests (BTC/ETH/SOL).
_TEST_UNIVERSE = frozenset({"BTC", "ETH", "SOL"})


@pytest.fixture(autouse=True)
def temp_parked_file(monkeypatch):
    tmpdir = tempfile.mkdtemp()
    monkeypatch.setattr(uf, "PARKED_FILE",
                        os.path.join(tmpdir, "parked_seeds.jsonl"))
    yield
    shutil.rmtree(tmpdir, ignore_errors=True)


def _seed(instruments):
    return {
        "hypothesis_id": "UF-TEST",
        "source": "human",
        "instruments": instruments,
        "horizon": "4h-48h",
        "entry_logic": "test entry",
    }


def test_equity_seed_routes_to_parked():
    r = uf.route_intake(_seed(["NVDA"]), universe=_TEST_UNIVERSE)
    assert r["route"] == "parked"
    assert r["non_hl"][0]["instrument"] == "NVDA"


def test_fx_and_gold_route_to_parked():
    for inst in (["EURUSD"], ["XAUUSD"], ["GLD"], ["NVDA", "BTC"]):
        r = uf.route_intake(_seed(inst), universe=_TEST_UNIVERSE)
        assert r["route"] == "parked", inst


def test_crypto_seed_routes_to_gauntlet():
    r = uf.route_intake(_seed(["BTC", "ETH"]), universe=_TEST_UNIVERSE)
    assert r["route"] == "gauntlet"
    assert r["non_hl"] == []


def test_universe_selector_is_eligible():
    r = uf.route_intake(_seed(["universe:hl-perps"]), universe=_TEST_UNIVERSE)
    assert r["route"] == "gauntlet"


def test_asset_class_detection():
    assert uf.detect_non_hl_class("EURUSD") == uf.ASSET_CLASS_FX
    assert uf.detect_non_hl_class("XAUUSD") == uf.ASSET_CLASS_COMMODITY
    assert uf.detect_non_hl_class("SPY") == uf.ASSET_CLASS_INDEX
    assert uf.detect_non_hl_class("NVDA") == uf.ASSET_CLASS_EQUITY
    assert uf.detect_non_hl_class("SOMETHING_ELSE") is None


def test_park_seed_writes_parked_backlog():
    r = uf.route_intake(_seed(["NVDA"]), universe=_TEST_UNIVERSE)
    assert r["route"] == "parked"
    uf.park_seed(_seed(["NVDA"]), reason=r["reason"])
    parked = uf.list_parked()
    assert len(parked) == 1
    assert parked[0]["hypothesis_id"] == "UF-TEST"
    assert parked[0]["parked_reason"].startswith("non-Hyperliquid")


if __name__ == "__main__":
    import tempfile
    for name, fn in sorted(list(globals().items())):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"PASS {name}")
    print("all universe_filter tests passed")