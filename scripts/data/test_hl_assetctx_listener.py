"""Tests for hl_assetctx_listener.py + the US-199 store extension.

Self-runnable (no pytest dependency): `python3 test_hl_assetctx_listener.py`.
Covers:
  * source-provenance column migration + gap table creation (fail-safe upgrade
    of a pre-US-199 store),
  * append_snapshot(source=...) provenance + unknown-source coercion,
  * ws frame parsing: index-aligned coin mapping, delisted skip, field parse,
  * ws length-mismatch -> dropped (fail-closed, no mislabeled writes),
  * record_gap idempotency.
"""

import os
import pathlib
import sqlite3
import sys
import tempfile

sys.path.insert(0, os.path.dirname(__file__))

import hl_assetctx_store as store  # noqa: E402
import hl_assetctx_listener as L  # noqa: E402


def _coin_map():
    return [
        {"name": "BTC", "isDelisted": False},
        {"name": "ETH", "isDelisted": False},
        {"name": "MATIC", "isDelisted": True},   # delisted -> must be skipped
        {"name": "SOL", "isDelisted": False},
    ]


def _ctx(markPx="100", oraclePx="101", funding="0.0000125", openInterest="1000"):
    return {
        "funding": funding, "openInterest": openInterest, "prevDayPx": "90",
        "dayNtlVlm": "5000", "premium": "0.001", "oraclePx": oraclePx,
        "markPx": markPx, "midPx": "100", "impactPxs": ["99", "101"],
        "dayBaseVlm": "50",
    }


# -- store schema / provenance -------------------------------------------

def test_schema_migration_adds_source_and_gap_table():
    with tempfile.TemporaryDirectory() as d:
        orig = store.STORE_DIR
        try:
            store.STORE_DIR = pathlib.Path(d)
            conn = store.open_store()
            cols = {r[1] for r in conn.execute("PRAGMA table_info(asset_ctx)")}
            assert "source" in cols
            tables = {r[0] for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'")}
            assert "assetctx_gaps" in tables
            conn.close()
        finally:
            store.STORE_DIR = orig


def test_append_snapshot_source_provenance_and_coercion():
    with tempfile.TemporaryDirectory() as d:
        orig = store.STORE_DIR
        try:
            store.STORE_DIR = pathlib.Path(d)
            conn = store.open_store()
            rows = [{"coin": "BTC", "time": 1000, "mark_px": 1.0}]
            store.append_snapshot(conn, rows, source="ws")
            store.append_snapshot(conn, [{"coin": "ETH", "time": 1000,
                                          "mark_px": 2.0}], source="backfill")
            store.append_snapshot(conn, [{"coin": "SOL", "time": 1000,
                                          "mark_px": 3.0}], source="nonsense")
            got = dict(conn.execute(
                "SELECT coin, source FROM asset_ctx").fetchall())
            assert got["BTC"] == "ws"
            assert got["ETH"] == "backfill"
            assert got["SOL"] == "poll"   # unknown -> fail-closed 'poll'
            conn.close()
        finally:
            store.STORE_DIR = orig


def test_record_gap_idempotent():
    with tempfile.TemporaryDirectory() as d:
        orig = store.STORE_DIR
        try:
            store.STORE_DIR = pathlib.Path(d)
            conn = store.open_store()
            store.record_gap(conn, "BTC", 1000, 2000, detected=9999)
            store.record_gap(conn, "BTC", 1000, 2000, detected=9999)  # idempotent
            n = conn.execute("SELECT COUNT(*) FROM assetctx_gaps").fetchone()[0]
            assert n == 1
            conn.close()
        finally:
            store.STORE_DIR = orig


# -- ws frame parsing ----------------------------------------------------

def test_parse_ws_maps_coins_and_skips_delisted():
    lst = L.AssetCtxListener()
    lst.universe = _coin_map()
    data = {"dex": "", "ctxs": [_ctx() for _ in range(4)]}
    rows = lst._parse_ws(data, 1234567890)
    coins = [r["coin"] for r in rows]
    assert coins == ["BTC", "ETH", "SOL"]  # MATIC (delisted) skipped
    # field parsing: strings -> floats
    btc = rows[0]
    assert btc["time"] == 1234567890
    assert btc["mark_px"] == 100.0
    assert btc["oracle_px"] == 101.0
    assert btc["funding"] == 0.0000125
    assert btc["open_interest"] == 1000.0


def test_parse_ws_length_mismatch_returns_none():
    lst = L.AssetCtxListener()
    lst.universe = _coin_map()  # length 4
    lst.refresh_universe = lambda: None  # hermetic: no network in unit test
    data = {"dex": "", "ctxs": [_ctx() for _ in range(3)]}  # length 3
    rows = lst._parse_ws(data, 1234567890)
    assert rows is None  # fail-closed: never write a misaligned frame


def test_parse_ws_missing_ctxs_returns_none():
    lst = L.AssetCtxListener()
    lst.universe = _coin_map()
    assert lst._parse_ws({"dex": ""}, 1234567890) is None


def test_parse_rest_uses_universe_mapping():
    lst = L.AssetCtxListener()
    lst.universe = _coin_map()
    rows = lst._parse_rest([_ctx() for _ in range(4)], 999)
    assert [r["coin"] for r in rows] == ["BTC", "ETH", "SOL"]


if __name__ == "__main__":
    for name, fn in sorted(list(globals().items())):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"PASS {name}")
    print("all hl_assetctx_listener tests passed")