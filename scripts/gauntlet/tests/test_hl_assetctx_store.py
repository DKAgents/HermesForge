"""
Tests for hl_assetctx_store.py — the Hyperliquid assetCtxs snapshot store
(US-185 basis / US-186 positioning).

Covers:
  * idempotent append (same (coin, time) twice -> 2nd inserts 0),
  * the US-186 extension fields (day_ntl_vlm / day_base_vlm / prev_day_px)
    round-trip through append_snapshot,
  * golden read: read_basis basis_bps vector, and read_positioning oi_usd
    derivation (open_interest is BASE units; oi_usd = oi * mark_px).

Self-runnable (pytest-style ``tmp_path`` accepted via __main__ fallback),
mirroring test_hl_funding_store.py.
"""

import sys
import os
import pathlib
import sqlite3

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "data"))

import hl_assetctx_store as s  # noqa: E402


def _fresh_conn(tmp_path):
    conn = sqlite3.connect(str(tmp_path / "assetctx.db"))
    for p in s.PRAGMAS:
        conn.execute(p)
    conn.executescript(s._SCHEMA)
    conn.commit()
    return conn


def _row(coin, time, mark_px=None, oracle_px=None, funding=None, premium=None,
         open_interest=None, day_ntl_vlm=None, day_base_vlm=None,
         prev_day_px=None):
    return {"coin": coin, "time": time, "mark_px": mark_px,
            "oracle_px": oracle_px, "funding": funding, "premium": premium,
            "open_interest": open_interest, "day_ntl_vlm": day_ntl_vlm,
            "day_base_vlm": day_base_vlm, "prev_day_px": prev_day_px}


def test_append_same_snapshot_twice_inserts_zero(tmp_path):
    conn = _fresh_conn(tmp_path)
    rows = [_row("BTC", 3600000, mark_px=78000.0, oracle_px=78010.0,
                 day_ntl_vlm=884212397.4, day_base_vlm=11350.4, prev_day_px=77477.0),
            _row("ETH", 3600000, mark_px=2000.0, oracle_px=2000.5)]
    n1 = s.append_snapshot(conn, rows)
    n2 = s.append_snapshot(conn, rows)   # re-snapshot same (coin,time) -> 0
    assert n1 == 2
    assert n2 == 0
    conn.close()


def test_positioning_fields_roundtrip_and_oi_usd(tmp_path):
    # Exercise the PUBLIC open_store/append/read path against a temp STORE_DIR
    # so read_positioning (which opens the store itself) is isolated.
    orig = s.STORE_DIR
    try:
        s.STORE_DIR = pathlib.Path(tmp_path)
        conn = s.open_store()
        s.append_snapshot(conn, [
            _row("BTC", 3600000, mark_px=78000.0, oracle_px=78010.0,
                 funding=0.0000125, premium=-0.00027207, open_interest=40193.21552,
                 day_ntl_vlm=884212397.421, day_base_vlm=11350.404, prev_day_px=77477.0),
        ])
        conn.close()

        df = s.read_positioning("BTC")
        assert len(df) == 1
        r = df.iloc[0]
        assert abs(r["open_interest"] - 40193.21552) < 1e-6
        assert abs(r["day_ntl_vlm"] - 884212397.421) < 1e-3
        assert abs(r["day_base_vlm"] - 11350.404) < 1e-3
        assert abs(r["prev_day_px"] - 77477.0) < 1e-6
        # oi_usd = open_interest (BASE) * mark_px
        assert abs(r["oi_usd"] - 40193.21552 * 78000.0) < 1e-3
    finally:
        s.STORE_DIR = orig


def test_read_basis_golden_vector(tmp_path):
    orig = s.STORE_DIR
    try:
        s.STORE_DIR = pathlib.Path(tmp_path)
        conn = s.open_store()
        # mark 78000 vs oracle 78010 -> (78000-78010)/78010*1e4 = -1.2819... bps
        s.append_snapshot(conn, [
            _row("BTC", 3600000, mark_px=78000.0, oracle_px=78010.0),
            _row("BTC", 7200000, mark_px=78100.0, oracle_px=78000.0),
        ])
        conn.close()

        df = s.read_basis("BTC")
        assert list(df["time"]) == [3600000, 7200000]
        assert abs(df["basis_bps"].iloc[0] - (-10.0 / 78010.0 * 1e4)) < 1e-9
        assert abs(df["basis_bps"].iloc[1] - (100.0 / 78000.0 * 1e4)) < 1e-9
    finally:
        s.STORE_DIR = orig


def test_read_positioning_empty(tmp_path):
    orig = s.STORE_DIR
    try:
        s.STORE_DIR = pathlib.Path(tmp_path)
        conn = s.open_store()
        conn.close()
        df = s.read_positioning("BTC")
        assert df.empty
        assert list(df.columns) == ["time", "mark_px", "open_interest", "oi_usd",
                                    "funding", "premium", "day_ntl_vlm",
                                    "day_base_vlm", "prev_day_px"]
    finally:
        s.STORE_DIR = orig


if __name__ == "__main__":
    import tempfile
    for name, fn in sorted(list(globals().items())):
        if name.startswith("test_") and callable(fn):
            with tempfile.TemporaryDirectory() as d:
                fn(pathlib.Path(d))
            print(f"PASS {name}")
    print("all hl_assetctx_store tests passed")