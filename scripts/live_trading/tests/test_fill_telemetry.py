"""
Tests for fill_telemetry.py — M-10 live-fill telemetry logger + read path.

Covers: well-formed record writes and round-trip reads, fail-closed schema
validation (missing required field / bad side / bad order_type / bad instrument),
no-fill records, the since_ms filter, and the G3 recalibration aggregation.
"""

import sys
import os
import json
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest

import fill_telemetry as ft


@pytest.fixture
def tmp_log(tmp_path, monkeypatch):
    """Point the module at a fresh temp log file for each test."""
    p = tmp_path / "fill_telemetry.jsonl"
    monkeypatch.setattr(ft, "LOG_PATH", p)
    return p


def _make_fill(**overrides):
    rec = {
        "venue": "hyperliquid",
        "instrument": "perp",
        "coin": "ETH",
        "side": "sell",
        "order_type": "maker",
        "filled": True,
        "queue_position": 3,
        "time_to_fill_ms": 1200,
        "fill_price": 3000.0,
        "fill_size": 0.5,
        "size_usd": 1500.0,
        "fees_bps": 1.5,
        "fees_usd": 0.225,
        "markout_1m_bps": 0.4,
        "markout_5m_bps": -1.1,
        "markout_1h_bps": -3.0,
        "strategy_id": "STR-FNDCARRY",
        "trade_id": "STR-FNDCARRY-ETH-1109A",
    }
    rec.update(overrides)
    return rec


def test_record_writes_well_formed_jsonl(tmp_log):
    ft.record_fill(_make_fill())
    rows = ft.read_fills()
    assert len(rows) == 1
    r = rows[0]
    assert r["schema"] == ft.SCHEMA_VERSION
    for k in ("venue", "instrument", "coin", "side", "order_type", "filled"):
        assert k in r
    assert r["venue"] == "hyperliquid"
    assert r["filled"] is True
    assert r["ts"] and r["ts_ms"] is not None
    # The record must carry the markouts + fees + time-to-fill + queue position.
    assert r["markout_1m_bps"] == 0.4
    assert r["markout_5m_bps"] == -1.1
    assert r["markout_1h_bps"] == -3.0
    assert r["fees_bps"] == 1.5
    assert r["queue_position"] == 3
    assert r["time_to_fill_ms"] == 1200


def test_record_persists_across_reads(tmp_log):
    ft.record_fill(_make_fill())
    ft.record_fill(_make_fill(trade_id="STR-FNDCARRY-ETH-1109B", filled=False,
                              queue_position=None, time_to_fill_ms=None,
                              markout_1m_bps=None))
    rows = ft.read_fills()
    assert len(rows) == 2
    assert rows[0]["filled"] is True
    assert rows[1]["filled"] is False


def test_validation_rejects_missing_required(tmp_log):
    for field in ft.REQUIRED_FIELDS:
        rec = _make_fill()
        del rec[field]
        with pytest.raises(ValueError):
            ft.record_fill(rec)


def test_validation_rejects_bad_enum(tmp_log):
    with pytest.raises(ValueError):
        ft.record_fill(_make_fill(side="hold"))
    with pytest.raises(ValueError):
        ft.record_fill(_make_fill(order_type="iceberg"))
    with pytest.raises(ValueError):
        ft.record_fill(_make_fill(instrument="futures"))
    with pytest.raises(ValueError):
        ft.record_fill(_make_fill(filled="yes"))


def test_since_ms_filter(tmp_log):
    ft.record_fill(_make_fill(ts_ms=1000))
    ft.record_fill(_make_fill(ts_ms=2000, trade_id="STR-FNDCARRY-ETH-1109B"))
    assert len(ft.read_fills(since_ms=1500)) == 1
    assert len(ft.read_fills(since_ms=3000)) == 0


def test_g3_recalibration_aggregation(tmp_log):
    # One maker fill (adverse-selected: negative short-horizon markouts),
    # one taker fill, one no-fill.
    ft.record_fill(_make_fill(ts_ms=1000))  # maker, filled
    ft.record_fill(_make_fill(ts_ms=2000, trade_id="T2", order_type="taker",
                              fees_bps=4.5, markout_1m_bps=-2.0,
                              markout_5m_bps=-1.0, markout_1h_bps=1.0,
                              time_to_fill_ms=50))
    ft.record_fill(_make_fill(ts_ms=3000, trade_id="T3", filled=False))

    cal = ft.g3_recalibration_input()
    assert cal["n_records"] == 3
    assert cal["n_fills"] == 2
    assert cal["fill_rate"] == pytest.approx(2 / 3)
    assert cal["maker_ratio"] == pytest.approx(0.5)  # 1 of 2 fills maker
    assert cal["time_to_fill_ms"]["n"] == 2
    assert cal["markout_1m_bps"]["n"] == 2
    assert cal["markout_1m_bps"]["mean"] == pytest.approx((0.4 + -2.0) / 2)


def test_read_fills_empty_without_log(tmp_log):
    assert ft.read_fills() == []
    assert ft.g3_recalibration_input()["n_records"] == 0