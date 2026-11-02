"""Tests for ingest_hl_oi_archive.py — the Hyperliquid asset_ctxs OI backfill.

Hermetic + self-runnable (`python3 test_ingest_hl_oi_archive.py`, no pytest, no
AWS, no network): lz4 CSV fixtures are CONSTRUCTED in-process via a ctypes
binding to the system liblz4 (the same library the ingest script falls back to
for decompression) and run through the REAL `decompress_lz4` -> `parse_assetctx_csv`
-> `append_rows` pipeline. No real archive bytes are touched.

Proves the four mandatory correctness traps:
  (a) fabricated-zero 0.0 placeholder -> NULL + <field>_missing flag,
  (b) negative open_interest preserved as real data + open_interest_negative flag
      (NOT nulled — the exact-equality-0.0 rule, never <= 0.0),
  (c) funding-scale change detected + normalized + labeled,
  (d) changed header -> refusal (ArchiveRefused), no guessed mapping.
Plus defense-in-depth: negative-price refusal, out-of-range funding refusal,
over-the-cap row refusal, and store-level INSERT OR IGNORE idempotency + manifest
round-trip (resumability contract).
"""

import ctypes
import os
import pathlib
import sys

sys.path.insert(0, os.path.dirname(__file__))

import ingest_hl_oi_archive as M  # noqa: E402


# ---------------------------------------------------------------------------
# fixture construction (lz4 via system liblz4)
# ---------------------------------------------------------------------------

def _compress(data: bytes) -> bytes:
    lib = M._liblz4()
    lib.LZ4F_compressFrameBound.argtypes = [ctypes.c_size_t, ctypes.c_void_p]
    lib.LZ4F_compressFrameBound.restype = ctypes.c_size_t
    lib.LZ4F_compressFrame.argtypes = [
        ctypes.c_void_p, ctypes.c_size_t, ctypes.c_void_p, ctypes.c_size_t,
        ctypes.c_void_p]
    lib.LZ4F_compressFrame.restype = ctypes.c_size_t
    src = ctypes.create_string_buffer(data)
    bound = lib.LZ4F_compressFrameBound(len(data), None)
    dst = ctypes.create_string_buffer(bound)
    n = lib.LZ4F_compressFrame(dst, bound, src, len(data), None)
    assert not lib.LZ4F_isError(n), lib.LZ4F_getErrorName(n).decode()
    return dst.raw[:n]


HEADER_LINE = ",".join(M.EXPECTED_HEADER)


def _row(time, coin, funding, oi, prev_day_px, day_ntl_vlm, premium, oracle_px,
         mark_px, mid_px, ibid, iask):
    return ",".join(str(x) for x in
                    [time, coin, funding, oi, prev_day_px, day_ntl_vlm, premium,
                     oracle_px, mark_px, mid_px, ibid, iask])


def _lz4_csv(rows, header=HEADER_LINE):
    text = header + "\n" + "\n".join(rows) + "\n"
    return _compress(text.encode("utf-8"))


def _parse(fixture, day="20231101", **kw):
    text = M.decompress_lz4(fixture).decode("utf-8")
    return M.parse_assetctx_csv(text, day, **kw)


def _first(parsed):
    return parsed["rows"][0]


# ---------------------------------------------------------------------------
# (a) fabricated-zero -> NULL + missing flag
# ---------------------------------------------------------------------------

def test_fabricated_zero_to_null():
    row = _row(1699000000000, "BTC", "0.0000125", "0.0", "77477.0",
               "884212397.4", "0.0", "78010.0", "0.0", "0.0", "0.0", "0.0")
    r = _first(_parse(_lz4_csv([row])))
    # placeholder fields -> NULL + flag
    assert r["open_interest"] is None and r["open_interest_missing"] == 1
    assert r["premium"] is None and r["premium_missing"] == 1
    assert r["mark_px"] is None and r["mark_px_missing"] == 1
    assert r["mid_px"] is None and r["mid_px_missing"] == 1
    assert r["impact_bid_px"] is None and r["impact_bid_px_missing"] == 1
    assert r["impact_ask_px"] is None and r["impact_ask_px_missing"] == 1
    # non-placeholder fields preserved verbatim (oracle_px/prev_day_px are NOT
    # subject to the 0.0->missing rule)
    assert r["oracle_px"] == 78010.0
    assert r["prev_day_px"] == 77477.0
    assert r["day_ntl_vlm"] == 884212397.4
    assert r["funding_raw"] == 0.0000125


# ---------------------------------------------------------------------------
# (b) negative open_interest preserved + flagged (never nulled)
# ---------------------------------------------------------------------------

def test_negative_open_interest_preserved_and_flagged():
    row = _row(1699000000000, "SOL", "0.0000100", "-1234.5", "21.0",
               "100000.0", "-0.0001", "21.05", "21.0", "21.02", "20.99", "21.03")
    r = _first(_parse(_lz4_csv([row])))
    assert r["open_interest"] == -1234.5          # real data preserved
    assert r["open_interest_negative"] == 1        # flagged
    assert r["open_interest_missing"] == 0         # NOT missing


def test_zero_oi_is_missing_not_negative_and_positive_oi_is_clean():
    rows = [
        _row(1699000000000, "BTC", "0.0000125", "0.0", "77477.0", "1", "0",
             "78010.0", "78000.0", "78005.0", "77999.0", "78006.0"),
        _row(1699000060000, "BTC", "0.0000125", "40193.2", "77477.0", "1", "0",
             "78010.0", "78000.0", "78005.0", "77999.0", "78006.0"),
    ]
    parsed = _parse(_lz4_csv(rows))
    zero = parsed["rows"][0]
    pos = parsed["rows"][1]
    assert zero["open_interest"] is None and zero["open_interest_missing"] == 1
    assert zero["open_interest_negative"] == 0
    assert pos["open_interest"] == 40193.2
    assert pos["open_interest_missing"] == 0 and pos["open_interest_negative"] == 0


# ---------------------------------------------------------------------------
# (c) funding-scale detection + normalization + labeling
# ---------------------------------------------------------------------------

def test_funding_scale_pct_normalized_and_labeled():
    # archive era: funding persisted as percentage (1%, 2%) -> normalize /100.
    rows = [
        _row(1699000000000, "BTC", "0.01", "10", "77477.0", "1", "0",
             "78010.0", "78000.0", "78005.0", "77999.0", "78006.0"),
        _row(1699000000000, "ETH", "0.02", "10", "2000.0", "1", "0",
             "2000.5", "2000.0", "2000.2", "1999.9", "2000.3"),
    ]
    parsed = _parse(_lz4_csv(rows))
    assert parsed["meta"]["funding_scale"] == "pct"
    r = parsed["rows"][0]
    assert r["funding_raw"] == 0.01          # as-archived preserved
    assert abs(r["funding"] - 0.0001) < 1e-18  # normalized to hourly fraction
    assert parsed["rows"][1]["funding"] > 0  # second coin normalized too
    assert abs(parsed["rows"][1]["funding"] - 0.0002) < 1e-18


def test_funding_scale_canonical_unchanged():
    rows = [
        _row(1699000000000, "BTC", "0.00005", "10", "77477.0", "1", "0",
             "78010.0", "78000.0", "78005.0", "77999.0", "78006.0"),
        _row(1699000000000, "ETH", "0.00006", "10", "2000.0", "1", "0",
             "2000.5", "2000.0", "2000.2", "1999.9", "2000.3"),
    ]
    parsed = _parse(_lz4_csv(rows))
    assert parsed["meta"]["funding_scale"] == "1h_frac"
    assert abs(parsed["rows"][0]["funding"] - 0.00005) < 1e-18  # unchanged
    assert parsed["rows"][0]["funding_raw"] == 0.00005


# ---------------------------------------------------------------------------
# (d) changed header -> refusal (no guessed mapping)
# ---------------------------------------------------------------------------

def test_changed_header_refused():
    bad_col = ",".join(
        ["time", "coin", "funding", "open_interest", "prev_day_px",
         "day_ntl_vlm", "premium", "oracle_px", "mark_px", "mid_px",
         "impact_bid_px", "openInterest"]  # renamed field
    )
    _refused(_lz4_csv([_row(1699000000000, "BTC", "0", "1", "1", "1", "0",
                            "1", "1", "1", "1", "1")], header=bad_col))


def test_reordered_header_refused():
    reordered = ",".join(["coin", "time", "funding", "open_interest",
                          "prev_day_px", "day_ntl_vlm", "premium", "oracle_px",
                          "mark_px", "mid_px", "impact_bid_px", "impact_ask_px"])
    _refused(_lz4_csv([_row(1699000000000, "BTC", "0", "1", "1", "1", "0",
                            "1", "1", "1", "1", "1")], header=reordered))


def _refused(fixture, **kw):
    try:
        _parse(fixture, **kw)
    except M.ArchiveRefused:
        return
    raise AssertionError("expected ArchiveRefused, but parse succeeded")


# ---------------------------------------------------------------------------
# defense-in-depth: corruption refusal + idempotency + resumability
# ---------------------------------------------------------------------------

def test_negative_price_refused():
    row = _row(1699000000000, "BTC", "0", "1", "1", "1", "0", "1", "-1",
               "1", "1", "1")  # mark_px = -1
    _refused(_lz4_csv([row]))


def test_funding_out_of_range_refused():
    # raw |funding| = 50 > FUNDING_RAW_ABS_MAX (1.0) -> refuse (scale-independent)
    row = _row(1699000000000, "BTC", "50", "1", "1", "1", "0", "1", "1",
               "1", "1", "1")
    _refused(_lz4_csv([row]))


def test_too_many_rows_refused():
    rows = [_row(1699000000000 + i, "BTC", "0.00005", "1", "1", "1", "0",
                 "1", "1", "1", "1", "1") for i in range(3)]
    _refused(_lz4_csv(rows), max_rows=2)


def test_store_insert_or_ignore_idempotency(tmp_path=None):
    orig = M.STORE_DIR
    M.STORE_DIR = pathlib.Path(_tmpdir())
    try:
        conn = M.open_store()
        rows = [_first(_parse(_lz4_csv([
            _row(1699000000000, "BTC", "0.00005", "10", "1", "1", "0",
                 "1", "1", "1", "1", "1"),
        ])))]
        n1 = M.append_rows(conn, rows)
        n2 = M.append_rows(conn, rows)  # same (coin,time) -> 0
        conn.close()
        assert n1 == 1 and n2 == 0
    finally:
        M.STORE_DIR = orig


def test_manifest_roundtrip_and_mark_ingested():
    orig = M.STORE_DIR
    try:
        base = pathlib.Path(_tmpdir())
        M.STORE_DIR = base
        assert M.load_manifest() == {}
        m = {}
        M._mark_ingested(m, "20231101", 123)
        assert M.load_manifest()["20231101"]["status"] == "ingested"
        assert M.load_manifest()["20231101"]["new_rows"] == 123
        # re-mark same day is idempotent at the manifest level (overwrite)
        M._mark_ingested(m, "20231101", 0)
        assert M.load_manifest()["20231101"]["new_rows"] == 0
    finally:
        M.STORE_DIR = orig


def _tmpdir():
    import tempfile
    d = tempfile.mkdtemp(prefix="oi_archive_test_")
    return d


# ---------------------------------------------------------------------------
# runner
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    tests = [name for name in sorted(globals()) if name.startswith("test_")]
    failed = 0
    for name in tests:
        fn = globals()[name]
        try:
            fn()
        except Exception as e:
            failed += 1
            print(f"FAIL {name}: {type(e).__name__}: {e}")
        else:
            print(f"PASS {name}")
    print(f"{len(tests) - failed}/{len(tests)} passed")
    sys.exit(1 if failed else 0)