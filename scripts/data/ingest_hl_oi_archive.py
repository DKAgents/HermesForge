"""ingest_hl_oi_archive.py — HermesForge US-198 follow-up: Hyperliquid asset_ctxs
historical OI backfill (the data HYP-16 needs).

Pulls the daily, lz4-compressed CSV archive from the requester-pays public S3
bucket ``s3://hyperliquid-archive/asset_ctxs/{YYYYMMDD}.csv.lz4`` (one row per
coin per minute, perp markets, back to ~May 2023) and appends it to a dedicated,
append-only OI archive store. This is the ONLY honest deep OI-history source:
``metaAndAssetCtxs`` (US-199) has no history endpoint and only accumulates going
forward, so HYP-16 (~200d gate) can only be unblocked by backfilling this
archive.

The data goes to a DEDICATED store (``hl_assetctx_archive/oi_archive.db``), NOT
the forward-poll ``asset_ctx`` table, because the archive carries (a) columns the
poll snapshot does not (mid_px, impact_bid_px, impact_ask_px) and (b) per-field
``*_missing`` / ``*_negative`` / ``funding_scale`` provenance flags that must be
persisted so the fabricated-zero and negative-OI traps are label-visible — the
poll path has no such placeholders and must not be polluted by them.

CORRECTNESS TRAPS (mandatory, all enforced in parse_assetctx_csv):
  * Fabricated-zero placeholders — HL writes 0.0 for MISSING, never NULL. For
    open_interest, premium, mark_px, mid_px, impact_bid_px, impact_ask_px a 0.0
    is treated as missing -> NULL + a <field>_missing flag.
  * open_interest may be legitimately NEGATIVE around a delisting settlement, so
    the missing rule is EXACT-equal-to-0.0 -> missing, while negative values are
    PRESERVED as real data and flagged <open_interest_negative>. Using <= 0.0
    here would silently erase those real negative rows (they must survive, not
    be nulled).
  * Funding scale changes partway through the archive with no in-row marker —
    detected per-day (median |funding| classified to the nearest known anchor
    magnitude) and normalized to the canonical hourly-decimal unit, with the raw
    value and the detected scale persisted alongside.
  * Corruption refusal — a changed header, a day with too many rows, a negative
    price (or volume), or an out-of-range funding value REFUSES the file (the
    whole day is rejected, nothing is partially parsed).

AWS creds are NOT read/touched here: the ``aws s3 cp --request-payer requester``
CLI resolves credentials itself from the standard env / ~/.aws/credentials
(SDK default chain). This module never hardcodes creds and never touches .env.

GATED: no real archive data is pulled until AWS creds exist (no AWS account on
this deployment yet, US-198). ``--cost-only`` lists the touched days + egress
without pulling a byte; the ingest path itself fails closed with a clear message
if the ``aws`` CLI is missing.

Usage:
    python3 ingest_hl_oi_archive.py --start 20231101 --end 20231130            # pull + ingest
    python3 ingest_hl_oi_archive.py --start 20231101 --end 20231130 --cost-only  # dry-run cost
"""

from __future__ import annotations

import argparse
import csv
import ctypes
import io
import json
import math
import pathlib
import shutil
import sqlite3
import statistics
import subprocess
import sys
from datetime import datetime, timedelta, timezone

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

S3_BUCKET_BASE = "s3://hyperliquid-archive/asset_ctxs"

# EXACT schema (header order). Refuse the file if the header differs — do NOT
# guess a new mapping.
EXPECTED_HEADER = [
    "time", "coin", "funding", "open_interest", "prev_day_px", "day_ntl_vlm",
    "premium", "oracle_px", "mark_px", "mid_px", "impact_bid_px", "impact_ask_px",
]
N_HEADER_COLS = len(EXPECTED_HEADER)

# Fields where a 0.0 value is HL's "fabricated zero" placeholder for MISSING
# (never NULL in the raw file) -> stored NULL + <field>_missing flag.
MISSING_AT_ZERO = {
    "open_interest", "premium", "mark_px", "mid_px",
    "impact_bid_px", "impact_ask_px",
}

# Fields that are prices: a NEGATIVE value is corruption (refusal). prev_day_px
# and oracle_px are not subject to the 0.0->missing rule (a 0.0 prev_day_px is a
# legitimate "no previous day" on a new listing), but a negative one is invalid.
PRICE_FIELDS = {
    "mark_px", "oracle_px", "mid_px", "impact_bid_px", "impact_ask_px",
    "prev_day_px",
}

# funding's canonical unit is the Hyperliquid HOURLY rate expressed as a decimal
# fraction (e.g. 0.0000125 = 0.00125%/hr). The archive changes scale partway
# through with no in-row marker. Each tuple is (label, factor, anchor_magnitude)
# where factor normalizes to canonical (raw / factor) and anchor is the typical
# |funding| magnitude at that scale, used for nearest-in-log-space detection.
# NOTE: anchors are calibration points — verify against the first real pull.
FUNDING_SCALES = (
    ("1h_frac", 1.0,   1e-4),   # canonical hourly decimal fraction
    ("8h_frac", 8.0,   8e-4),   # 8-hour decimal fraction (older archive era)
    ("pct",     100.0, 1e-2),   # hourly percentage (not fraction)
)

# Out-of-range funding (corruption -> refuse). Two independent guards:
#   * RAW: |funding| > 1.0 is impossible in any archive scale (a decimal-fraction
#     funding rate can never exceed 100%/hr), so it is refused scale-independently.
#   * NORMALIZED: after scale normalization, |hourly funding| > 10% is refused.
FUNDING_RAW_ABS_MAX = 1.0
FUNDING_ABS_MAX_NORM = 0.1

# Corruption guard: a day with more rows than this is refused (we should never
# see more than the ~full perp universe x 1440 minutes/day). Generous on purpose
# so a normal day never trips it; only a genuinely inflated/corrupt file does.
MAX_ROWS_PER_DAY = 500_000

# Requester-pays cost model.
MB_PER_DAY = 7.0
USD_PER_GB = 0.09

STORE_DIR = pathlib.Path.home() / ".hermes" / "market_data" / "hl_assetctx_archive"
DB_NAME = "oi_archive.db"
MANIFEST_NAME = "manifest.json"
DOWNLOAD_DIR_NAME = "downloads"

PRAGMAS = (
    "PRAGMA journal_mode=WAL;",
    "PRAGMA synchronous=NORMAL;",
    "PRAGMA foreign_keys=ON;",
)

_SCHEMA = """
CREATE TABLE IF NOT EXISTS assetctx_archive (
    coin          TEXT    NOT NULL,
    time          INTEGER NOT NULL,   -- ms epoch (normalized from the CSV 'time')
    funding       REAL,               -- normalized hourly-decimal funding rate
    funding_raw   REAL,               -- as-archived (before scale normalization)
    funding_scale TEXT,               -- detected scale label (1h_frac|8h_frac|pct)
    open_interest REAL,               -- NULL when the 0.0 placeholder was seen
    open_interest_missing  INTEGER NOT NULL DEFAULT 0,  -- 1 => fabricated-zero -> NULL
    open_interest_negative INTEGER NOT NULL DEFAULT 0,  -- 1 => real negative OI (delist)
    prev_day_px   REAL,
    day_ntl_vlm   REAL,
    premium       REAL,
    premium_missing       INTEGER NOT NULL DEFAULT 0,
    oracle_px     REAL,
    mark_px       REAL,
    mark_px_missing       INTEGER NOT NULL DEFAULT 0,
    mid_px        REAL,
    mid_px_missing        INTEGER NOT NULL DEFAULT 0,
    impact_bid_px REAL,
    impact_bid_px_missing INTEGER NOT NULL DEFAULT 0,
    impact_ask_px REAL,
    impact_ask_px_missing INTEGER NOT NULL DEFAULT 0,
    day           TEXT    NOT NULL,   -- YYYYMMDD source-file provenance
    PRIMARY KEY (coin, time)
) WITHOUT ROWID;

CREATE INDEX IF NOT EXISTS idx_oi_archive_coin_time
    ON assetctx_archive (coin, time);
"""


class ArchiveRefused(Exception):
    """Raised (and optionally set as ``day``) when a day's file is corrupt and
    must be refused rather than silently parsed."""

    def __init__(self, message: str, day: str | None = None):
        super().__init__(message)
        self.day = day


# ---------------------------------------------------------------------------
# Dates / cost
# ---------------------------------------------------------------------------

def iter_date_range(start: str, end: str) -> list[str]:
    """Expand an inclusive [YYYYMMDD, YYYYMMDD] range into a list of day keys.
    Raises ValueError on a malformed date or a reversed range."""
    def _parse(s: str) -> datetime:
        if len(s) != 8 or not s.isdigit():
            raise ValueError(f"invalid date {s!r} (expected YYYYMMDD)")
        return datetime.strptime(s, "%Y%m%d")

    d0 = _parse(start)
    d1 = _parse(end)
    if d1 < d0:
        raise ValueError(f"range reversed: {start} > {end}")
    out, cur = [], d0
    while cur <= d1:
        out.append(cur.strftime("%Y%m%d"))
        # monotonic day step without DST surprises (naive UTC dates):
        cur = cur.replace(year=cur.year, month=cur.month, day=cur.day) + timedelta(days=1)
    return out


def cost_estimate(days: list[str]) -> dict:
    """{days, count, mb, gb, usd} — total requester-pays egress for the range."""
    n = len(days)
    mb = MB_PER_DAY * n
    gb = mb / 1000.0
    return {"days": days, "count": n, "mb": mb, "gb": gb, "usd": gb * USD_PER_GB}


def s3_key(day: str) -> str:
    return f"{S3_BUCKET_BASE}/{day}.csv.lz4"


# ---------------------------------------------------------------------------
# lz4 decompression (streaming, in-process where possible; no extra deps)
# ---------------------------------------------------------------------------

def decompress_lz4(data: bytes) -> bytes:
    """Decompress an lz4 FRAME. Ladder: python ``lz4.frame`` (if importable) ->
    ``unlz4``/``lz4`` CLI (if on PATH) -> ctypes bind to the system liblz4
    (guaranteed-present stdlib-only fallback). Raises on any failure; never
    returns partial data."""
    # 1) python-lz4 (in-process, preferred).
    try:
        import lz4.frame  # noqa: F401  (optional dependency)
        return lz4.frame.decompress(data)
    except ImportError:
        pass

    # 2) unlz4 / lz4 CLI (documented fallback).
    cli = shutil.which("unlz4") or shutil.which("lz4")
    if cli:
        try:
            proc = subprocess.run(
                [cli, "-d", "-c"], input=data, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
        except (OSError, subprocess.SubprocessError) as e:
            raise ArchiveRefused(f"lz4 CLI failed: {e}") from e
        if proc.returncode != 0:
            raise ArchiveRefused(
                f"lz4 CLI exit {proc.returncode}: "
                f"{proc.stderr.decode(errors='replace').strip()}"
            )
        return proc.stdout

    # 3) ctypes -> system liblz4 (present on this deployment; no pip dependency).
    return _ctypes_lz4_decompress(data)


def _liblz4():
    lib = ctypes.CDLL("liblz4.so.1")
    lib.LZ4F_createDecompressionContext.argtypes = [
        ctypes.POINTER(ctypes.c_void_p), ctypes.c_uint]
    lib.LZ4F_createDecompressionContext.restype = ctypes.c_size_t
    lib.LZ4F_decompress.argtypes = [
        ctypes.c_void_p, ctypes.c_void_p, ctypes.POINTER(ctypes.c_size_t),
        ctypes.c_void_p, ctypes.POINTER(ctypes.c_size_t), ctypes.c_void_p]
    lib.LZ4F_decompress.restype = ctypes.c_size_t
    lib.LZ4F_freeDecompressionContext.argtypes = [ctypes.c_void_p]
    lib.LZ4F_freeDecompressionContext.restype = ctypes.c_size_t
    lib.LZ4F_isError.argtypes = [ctypes.c_size_t]
    lib.LZ4F_isError.restype = ctypes.c_uint
    lib.LZ4F_getErrorName.argtypes = [ctypes.c_size_t]
    lib.LZ4F_getErrorName.restype = ctypes.c_char_p
    return lib


def _ctypes_lz4_decompress(data: bytes) -> bytes:
    lib = _liblz4()
    ctx = ctypes.c_void_p()
    rc = lib.LZ4F_createDecompressionContext(ctypes.byref(ctx), 100)
    if lib.LZ4F_isError(rc):
        raise ArchiveRefused(
            f"LZ4F_createDecompressionContext: "
            f"{lib.LZ4F_getErrorName(rc).decode()}"
        )
    src = ctypes.create_string_buffer(data)
    remaining = len(data)
    offset = 0
    out = bytearray()
    dst = ctypes.create_string_buffer(1 << 16)
    done = False
    try:
        while not done:
            dst_size = ctypes.c_size_t(1 << 16)
            src_left = ctypes.c_size_t(remaining)
            src_ptr = ctypes.c_void_p(ctypes.addressof(src) + offset)
            ret = lib.LZ4F_decompress(ctx, dst, ctypes.byref(dst_size), src_ptr,
                                      ctypes.byref(src_left), None)
            if lib.LZ4F_isError(ret):
                raise ArchiveRefused(
                    f"LZ4F_decompress: {lib.LZ4F_getErrorName(ret).decode()}")
            consumed = src_left.value
            offset += consumed
            remaining -= consumed
            if dst_size.value:
                out += dst.raw[:dst_size.value]
            if ret == 0:
                done = True
            elif remaining == 0 and dst_size.value == 0:
                raise ArchiveRefused("truncated lz4 frame (no progress, not done)")
    finally:
        lib.LZ4F_freeDecompressionContext(ctx)
    return bytes(out)


# ---------------------------------------------------------------------------
# Parsing + correctness traps
# ---------------------------------------------------------------------------

def _parse_float(v: str | None) -> float | None:
    """float() -> None for empty/blank/non-numeric. Never raises."""
    if v is None:
        return None
    s = v.strip()
    if s == "":
        return None
    try:
        return float(s)
    except ValueError:
        return None


def _normalize_time(v: str) -> int:
    """Coerce the 'time' field to ms epoch. Accepts either ms epoch (>= 1e11) or
    seconds epoch (< 1e11), normalizing seconds -> ms. This is defensive unit
    normalization, not a schema guess."""

    result = int(v)
    if result < 10_000_000_000:
        result *= 1000
    return result


def _validate_header(header_line: str) -> None:
    """Exact-schema check. Refuses the file if the header differs in ANY way (no
    guessed remapping). Tolerates a leading UTF-8 BOM only."""
    header = header_line.lstrip("\ufeff").strip()
    actual = [c.strip() for c in header.split(",")]
    if actual != EXPECTED_HEADER:
        raise ArchiveRefused(
            f"header mismatch: got {actual} (expected {EXPECTED_HEADER}) — "
            "refusing file, no guessed mapping"
        )


def _detect_funding_scale(samples: list[float | None]) -> tuple[str, float]:
    """classify the day's funding scale by nearest anchor magnitude (log-space).
    Returns (label, factor). Non-zero only; falls back to canonical when a day
    has no funding observations."""
    vals = [abs(x) for x in samples if x is not None and x != 0.0]
    if not vals:
        return "1h_frac", 1.0
    med = statistics.median(vals)
    log_med = math.log10(max(med, 1e-30))
    label, factor, _anchor = min(
        FUNDING_SCALES,
        key=lambda s: abs(log_med - math.log10(s[2])),
    )
    return label, factor


def _check_negative_price(field: str, value: float | None, day: str) -> None:
    if value is not None and value < 0.0:
        raise ArchiveRefused(
            f"negative {field} ({value}) in {day} — corrupt, refusing", day=day)


def parse_assetctx_csv(text: str, day: str,
                       max_rows: int | None = None) -> dict:
    """Parse raw CSV text into rows + meta. Enforces every correctness trap and
    REFUSES (ArchiveRefused) on corruption instead of silently parsing garbage.

    Returns {"rows": [dict...], "meta": {"n_raw": int, "funding_scale": str}}
    where each row is keyed for the store."""

    max_rows = MAX_ROWS_PER_DAY if max_rows is None else max_rows

    lines = text.split("\n")
    if not lines:
        raise ArchiveRefused(f"{day}: empty file", day=day)
    _validate_header(lines[0])

    reader = csv.reader(io.StringIO(text))
    header = next(reader, None)  # already validated vs EXPECTED_HEADER
    _ = header

    rows = []
    raw_funding: list[float | None] = []
    n_rows = 0

    for rec in reader:
        if not rec or all(c.strip() == "" for c in rec):
            continue
        if len(rec) != N_HEADER_COLS:
            raise ArchiveRefused(
                f"{day}: row has {len(rec)} fields (expected {N_HEADER_COLS})",
                day=day)
        n_rows += 1
        if n_rows > max_rows:
            raise ArchiveRefused(
                f"{day}: {n_rows} rows exceeds limit {max_rows} — corrupt",
                day=day)

        time_ms = _normalize_time(rec[0])
        coin = rec[1].strip()
        if not coin:
            raise ArchiveRefused(f"{day}: empty coin name", day=day)

        funding_raw = _parse_float(rec[2])
        if funding_raw is not None and abs(funding_raw) > FUNDING_RAW_ABS_MAX:
            raise ArchiveRefused(
                f"{day}: funding out of range ({funding_raw}, "
                f"> {FUNDING_RAW_ABS_MAX}) — corrupt", day=day)
        oi_raw = _parse_float(rec[3])
        prev_day_px = _parse_float(rec[4])
        day_ntl_vlm = _parse_float(rec[5])
        premium_raw = _parse_float(rec[6])
        oracle_px = _parse_float(rec[7])
        mark_px = _parse_float(rec[8])
        mid_px = _parse_float(rec[9])
        impact_bid_px = _parse_float(rec[10])
        impact_ask_px = _parse_float(rec[11])

        # --- corruption: negative price / volume ---
        _check_negative_price("mark_px", mark_px, day)
        _check_negative_price("oracle_px", oracle_px, day)
        _check_negative_price("mid_px", mid_px, day)
        _check_negative_price("impact_bid_px", impact_bid_px, day)
        _check_negative_price("impact_ask_px", impact_ask_px, day)
        _check_negative_price("prev_day_px", prev_day_px, day)
        if day_ntl_vlm is not None and day_ntl_vlm < 0.0:
            raise ArchiveRefused(
                f"{day}: negative day_ntl_vlm ({day_ntl_vlm}) — corrupt", day=day)

        # --- fabricated-zero -> missing (NULL + flag) ---
        # open_interest: EXACT == 0.0 is the placeholder -> NULL; NEGATIVE is
        # real (delisting settlement) -> preserved + flagged, never nulled.
        if oi_raw == 0.0:
            open_interest, oi_missing, oi_negative = None, 1, 0
        elif oi_raw is not None and oi_raw < 0.0:
            open_interest, oi_missing, oi_negative = oi_raw, 0, 1
        else:
            open_interest, oi_missing, oi_negative = oi_raw, 0, 0

        premium, prem_missing = premium_raw, 0
        if premium_raw == 0.0:
            premium, prem_missing = None, 1

        mark_px_v, mark_missing = mark_px, 0
        if mark_px == 0.0:
            mark_px_v, mark_missing = None, 1
        mid_px_v, mid_missing = mid_px, 0
        if mid_px == 0.0:
            mid_px_v, mid_missing = None, 1
        ib, ib_missing = impact_bid_px, 0
        if impact_bid_px == 0.0:
            ib, ib_missing = None, 1
        ia, ia_missing = impact_ask_px, 0
        if impact_ask_px == 0.0:
            ia, ia_missing = None, 1

        raw_funding.append(funding_raw)

        rows.append({
            "coin": coin,
            "time": time_ms,
            "funding_raw": funding_raw,
            "open_interest": open_interest,
            "open_interest_missing": oi_missing,
            "open_interest_negative": oi_negative,
            "prev_day_px": prev_day_px,
            "day_ntl_vlm": day_ntl_vlm,
            "premium": premium,
            "premium_missing": prem_missing,
            "oracle_px": oracle_px,
            "mark_px": mark_px_v,
            "mark_px_missing": mark_missing,
            "mid_px": mid_px_v,
            "mid_px_missing": mid_missing,
            "impact_bid_px": ib,
            "impact_bid_px_missing": ib_missing,
            "impact_ask_px": ia,
            "impact_ask_px_missing": ia_missing,
            "day": day,
        })

    # --- funding scale normalization + out-of-range refusal ---
    scale_label, factor = _detect_funding_scale(raw_funding)
    norm_funding: list[float | None] = []
    for f in raw_funding:
        if f is None:
            norm_funding.append(None)
            continue
        nf = f / factor
        if abs(nf) > FUNDING_ABS_MAX_NORM:
            raise ArchiveRefused(
                f"{day}: funding out of range ({f} -> normalized {nf}, "
                f"> {FUNDING_ABS_MAX_NORM}) — corrupt", day=day)
        norm_funding.append(nf)
    for r, nf in zip(rows, norm_funding):
        r["funding"] = nf
        r["funding_scale"] = scale_label

    return {
        "rows": rows,
        "meta": {
            "n_raw": len(rows),
            "funding_scale": scale_label,
        },
    }


# ---------------------------------------------------------------------------
# Store
# ---------------------------------------------------------------------------

def db_path() -> pathlib.Path:
    return STORE_DIR / DB_NAME


def manifest_path() -> pathlib.Path:
    return STORE_DIR / MANIFEST_NAME


def open_store() -> sqlite3.Connection:
    """Open (create if absent) the OI archive DB; apply PRAGMAs; run schema DDL
    idempotently. Returns a WAL-mode connection."""
    path = db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    for pragma in PRAGMAS:
        conn.execute(pragma)
    conn.executescript(_SCHEMA)
    conn.commit()
    return conn


def append_rows(conn: sqlite3.Connection, rows: list[dict]) -> int:
    """INSERT OR IGNORE keyed (coin, time). Idempotent: re-ingesting a day inserts
    0 for existing keys. Commit inside; rollback on error (atomic). Returns the
    count of NEW rows."""
    if not rows:
        return 0
    tuples = [
        (r["coin"], r["time"], r["funding"], r["funding_raw"], r["funding_scale"],
         r["open_interest"], r["open_interest_missing"],
         r["open_interest_negative"], r["prev_day_px"], r["day_ntl_vlm"],
         r["premium"], r["premium_missing"], r["oracle_px"], r["mark_px"],
         r["mark_px_missing"], r["mid_px"], r["mid_px_missing"],
         r["impact_bid_px"], r["impact_bid_px_missing"], r["impact_ask_px"],
         r["impact_ask_px_missing"], r["day"])
        for r in rows
    ]
    sql = (
        "INSERT OR IGNORE INTO assetctx_archive ("
        "coin, time, funding, funding_raw, funding_scale, "
        "open_interest, open_interest_missing, open_interest_negative, "
        "prev_day_px, day_ntl_vlm, premium, premium_missing, oracle_px, "
        "mark_px, mark_px_missing, mid_px, mid_px_missing, "
        "impact_bid_px, impact_bid_px_missing, impact_ask_px, "
        "impact_ask_px_missing, day) "
        "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)"
    )
    try:
        cur = conn.executemany(sql, tuples)
        conn.commit()
        return cur.rowcount if cur.rowcount is not None else 0
    except Exception:
        conn.rollback()
        raise


def load_manifest() -> dict:
    path = manifest_path()
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return {}


def save_manifest(manifest: dict) -> None:
    path = manifest_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(manifest, indent=2, sort_keys=True))
    tmp.replace(path)  # atomic


def _mark_ingested(manifest: dict, day: str, new_rows: int) -> None:
    manifest[day] = {
        "status": "ingested",
        "new_rows": new_rows,
        "ts": datetime.now(timezone.utc).isoformat(),
    }
    save_manifest(manifest)


# ---------------------------------------------------------------------------
# Download / ingest orchestration
# ---------------------------------------------------------------------------

def download_day(day: str, outdir: pathlib.Path,
                 cli: str = "aws") -> pathlib.Path:
    """``aws s3 cp --request-payer requester`` one day into outdir. Returns the
    local path. Credentials resolve via the SDK standard chain (env /
    ~/.aws/credentials) — never hardcoded here. Raises if ``aws`` is missing or
    the transfer fails."""
    if shutil.which(cli) is None:
        raise ArchiveRefused(
            f"'{cli}' CLI not found on PATH. Configure AWS credentials "
            f"(env / ~/.aws/credentials) and install the AWS CLI to pull the "
            f"archive.", day=day)
    outdir.mkdir(parents=True, exist_ok=True)
    dest = outdir / f"{day}.csv.lz4"
    key = s3_key(day)
    proc = subprocess.run(
        [cli, "s3", "cp", "--request-payer", "requester", key, str(dest)],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    if proc.returncode != 0:
        raise ArchiveRefused(
            f"aws s3 cp failed for {day} (exit {proc.returncode}): "
            f"{proc.stderr.decode(errors='replace').strip()}", day=day)
    return dest


def ingest_day_from_path(conn: sqlite3.Connection, path: pathlib.Path,
                         day: str) -> dict:
    """Decompress + parse + append one day. Returns a status dict. Refusal
    (ArchiveRefused) leaves the store untouched (atomic per-day)."""
    data = path.read_bytes()
    text = decompress_lz4(data).decode("utf-8")
    parsed = parse_assetctx_csv(text, day)
    new_rows = append_rows(conn, parsed["rows"])
    return {
        "day": day, "ok": True, "new_rows": new_rows,
        "n_raw": parsed["meta"]["n_raw"],
        "funding_scale": parsed["meta"]["funding_scale"],
        "error": None,
    }


def ingest_range(start: str, end: str, outdir: pathlib.Path | None = None,
                 cli: str = "aws") -> dict:
    """Pull + ingest [start, end] inclusive, skipping already-ingested days
    (manifest). Returns a summary dict."""
    days = iter_date_range(start, end)
    manifest = load_manifest()
    results = []
    errors = []
    skipped = [d for d in days if manifest.get(d, {}).get("status") == "ingested"]
    todo = [d for d in days if d not in set(skipped)]

    conn = open_store()
    try:
        for day in todo:
            prev = manifest.get(day, {})
            try:
                path = download_day(day, outdir or (STORE_DIR / DOWNLOAD_DIR_NAME),
                                    cli=cli)
                res = ingest_day_from_path(conn, path, day)
                _mark_ingested(manifest, day, res["new_rows"])
                results.append(res)
            except ArchiveRefused as e:
                # Record the refusal in the manifest (NOT marked ingested) so a
                # re-run retries it after the corrupt file is fixed upstream.
                manifest[day] = {
                    "status": "refused",
                    "reason": str(e),
                    "ts": datetime.now(timezone.utc).isoformat(),
                }
                save_manifest(manifest)
                errors.append({"day": day, "error": str(e)})
                results.append({"day": day, "ok": False, "error": str(e)})
    finally:
        conn.close()

    return {
        "ok": len(errors) == 0,
        "days": len(days),
        "skipped": skipped,
        "refused": errors,
        "results": results,
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser(
        description="Backfill Hyperliquid asset_ctxs OI history from the "
                    "requester-pays S3 archive (HYP-16 data).")
    ap.add_argument("--start", required=True, help="Start day YYYYMMDD (inclusive).")
    ap.add_argument("--end", required=True, help="End day YYYYMMDD (inclusive).")
    ap.add_argument("--cost-only", action="store_true",
                    help="List the touched days + egress estimate; pull nothing.")
    ap.add_argument("--outdir", default=None, help="Download directory override.")
    ap.add_argument("--max-rows", type=int, default=MAX_ROWS_PER_DAY,
                    help="Rows-per-day corruption refusal threshold.")
    args = ap.parse_args()

    try:
        days = iter_date_range(args.start, args.end)
    except ValueError as e:
        print(f"[INGEST] invalid range: {e}")
        return 2

    if args.cost_only:
        est = cost_estimate(days)
        print("[COST-ONLY] requester-pays egress estimate (no bytes pulled)")
        for d in days:
            print(f"  {s3_key(d)}")
        print(f"  days={est['count']}  ~={est['mb']:.1f} MB  "
              f"~=${est['usd']:.4f} (${USD_PER_GB}/GB)")
        return 0

    summary = ingest_range(args.start, args.end, args.outdir)
    new_rows = sum(r.get("new_rows", 0) for r in summary["results"])
    print(f"[INGEST] days={summary['days']} skipped={len(summary['skipped'])} "
          f"new_rows={new_rows} refused={len(summary['refused'])}")
    for r in summary["results"]:
        if not r.get("ok"):
            print(f"  REFUSED {r['day']}: {r['error']}")
        else:
            print(f"  ok {r['day']}: new_rows={r['new_rows']} "
                  f"scale={r['funding_scale']}")
    return 0 if summary["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())